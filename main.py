import argparse
import os
import sqlite3
import time
from functools import partial
from threading import Lock
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import tracing_context
from langchain_core.messages import BaseMessage
from pydantic import PrivateAttr

# Local imports
from config import (
    OPENROUTER_BASE_URL,
    get_openrouter_api_key,
    get_openrouter_headers,
    get_openrouter_model,
    get_titanic_db_path,
    resolve_llm_delay_seconds,
)
from state import AgentState
from agents.supervisor import create_supervisor
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.sql_queryer import sql_query_node
from logger import (
    logger, 
    log_node_start, 
    log_node_end, 
    log_supervisor_decision, 
    log_error
)
from runtime_controls import configure_tracing, create_runtime_config

# Load environment variables
load_dotenv()

DEFAULT_SMOKE_QUERY = (
    "Analyze the Titanic dataset: What was the survival rate of female passengers? "
    "Then summarize the finding."
)

class ThrottledChatOpenAI(ChatOpenAI):
    """ChatOpenAI wrapper that spaces out API calls to avoid RPM bursts."""

    call_delay_seconds: float = 0.0
    _throttle_lock: Lock = PrivateAttr(default_factory=Lock)
    _next_available_at: float = PrivateAttr(default=0.0)

    def _wait_for_slot(self) -> None:
        delay = max(0.0, self.call_delay_seconds)
        if delay <= 0:
            return

        with self._throttle_lock:
            now = time.monotonic()
            if self._next_available_at > now:
                time.sleep(self._next_available_at - now)
            self._next_available_at = time.monotonic() + delay

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ):
        self._wait_for_slot()
        return super()._generate(
            messages=messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ):
        self._wait_for_slot()
        return await super()._agenerate(
            messages=messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )

def create_llm(call_delay_seconds: Optional[float] = None) -> ThrottledChatOpenAI:
    """Create the OpenRouter-backed chat model."""
    return ThrottledChatOpenAI(
        model=get_openrouter_model(),
        openai_api_key=get_openrouter_api_key(),
        base_url=os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
        temperature=0,
        request_timeout=120,
        default_headers=get_openrouter_headers(),
        call_delay_seconds=resolve_llm_delay_seconds(call_delay_seconds),
    )

def create_initial_state() -> AgentState:
    """Return a fresh graph state for a new interaction."""
    return {
        "messages": [],
        "next": "Supervisor",
        "data": {},
        "retry_count": 0,
        "last_error": None,
    }

def validate_database(db_path: str | None = None) -> None:
    """Verify that the local Titanic SQLite database is ready for SQLQueryer."""
    db_path = str(get_titanic_db_path()) if db_path is None else db_path
    if not os.path.exists(db_path):
        raise RuntimeError(
            f"Missing database: {db_path}. Run `uv run setup_db.py` before executing SQL tasks."
        )

    try:
        with sqlite3.connect(db_path) as conn:
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'titanic'"
            ).fetchone()
            if not table_exists:
                raise RuntimeError(
                    f"Missing table: titanic in {db_path}. Run `uv run setup_db.py` to rebuild it."
                )

            row_count = conn.execute("SELECT COUNT(*) FROM titanic").fetchone()[0]
            if row_count == 0:
                raise RuntimeError(
                    f"Empty table: titanic in {db_path}. Run `uv run setup_db.py` to reload data."
                )
    except sqlite3.Error as exc:
        raise RuntimeError(f"Invalid database: {db_path}. SQLite error: {exc}") from exc

def call_supervisor(state: AgentState, supervisor: Any, runtime_config: dict[str, Any] | None = None) -> Dict[str, Any]:
    try:
        log_node_start("Supervisor")
        
        # Determine if we are in a retry loop
        current_agent = state.get("next")
        last_error = state.get("last_error")
        
        invoke_kwargs = {"config": runtime_config} if runtime_config else {}
        result = supervisor.invoke(state, **invoke_kwargs)
        
        # Logic to update retry count
        new_retry_count = state.get("retry_count", 0)
        if result.next == current_agent and last_error:
            new_retry_count += 1
            logger.warning(f"⚠️ Self-Correction: Retrying {result.next} (Attempt {new_retry_count}/3)")
        else:
            # Reset retry count if moving to a different agent or starting fresh
            new_retry_count = 0
            
        # Hard limit for retries
        if new_retry_count > 3:
            logger.error(f"❌ Maximum retries (3) reached for {result.next}. Redirecting to Writer.")
            result.next = "Writer"
            result.instruction = "Explain that the previous task failed after multiple attempts and summarize what we know."
            new_retry_count = 0

        log_supervisor_decision(result.next, result.instruction)
        
        return {
            "next": result.next,
            "retry_count": new_retry_count,
            "last_error": None, # Clear error after supervisor handled it
            "messages": [AIMessage(content=f"To {result.next}: {result.instruction}", name="Supervisor")]
        }
    except Exception as e:
        log_error("Supervisor", str(e))
        raise

def run_researcher(state: AgentState, llm: Any, runtime_config: dict[str, Any] | None = None):
    log_node_start("Researcher")
    try:
        res = researcher_node(state, llm, runtime_config=runtime_config)
        log_node_end("Researcher")
        return res
    except Exception as e:
        log_error("Researcher", str(e))
        return {
            "messages": [HumanMessage(content=f"Error in Researcher: {str(e)}", name="System")],
            "last_error": str(e)
        }

def run_writer(state: AgentState, llm: Any, runtime_config: dict[str, Any] | None = None):
    log_node_start("Writer")
    try:
        res = writer_node(state, llm, runtime_config=runtime_config)
        log_node_end("Writer")
        return res
    except Exception as e:
        log_error("Writer", str(e))
        return {
            "messages": [HumanMessage(content=f"Error in Writer: {str(e)}", name="System")],
            "last_error": str(e)
        }

def run_sql_queryer(state: AgentState, llm: Any, runtime_config: dict[str, Any] | None = None):
    log_node_start("SQLQueryer")
    try:
        res = sql_query_node(state, llm, runtime_config=runtime_config)
        log_node_end("SQLQueryer")
        return res
    except Exception as e:
        log_error("SQLQueryer", str(e))
        # We pass the error back to the supervisor to let it decide what to do
        return {
            "messages": [HumanMessage(content=f"Error in SQLQueryer: {str(e)}. Please fix the query or table name.", name="System")],
            "last_error": str(e)
        }

def build_graph(llm: Any, runtime_config: dict[str, Any] | None = None):
    """Assemble the hierarchical graph."""
    workflow = StateGraph(AgentState)
    
    supervisor = create_supervisor(llm)
    
    workflow.add_node("Supervisor", partial(call_supervisor, supervisor=supervisor, runtime_config=runtime_config))
    workflow.add_node("Researcher", partial(run_researcher, llm=llm, runtime_config=runtime_config))
    workflow.add_node("Writer", partial(run_writer, llm=llm, runtime_config=runtime_config))
    workflow.add_node("SQLQueryer", partial(run_sql_queryer, llm=llm, runtime_config=runtime_config))
    
    workflow.add_edge(START, "Supervisor")
    
    workflow.add_conditional_edges(
        "Supervisor",
        lambda x: x["next"],
        {
            "Researcher": "Researcher",
            "Writer": "Writer",
            "SQLQueryer": "SQLQueryer",
            "FINISH": END
        }
    )
    
    workflow.add_edge("Researcher", "Supervisor")
    workflow.add_edge("Writer", "Supervisor")
    workflow.add_edge("SQLQueryer", "Supervisor")
    
    return workflow.compile()

def process_turn(app, state: AgentState, user_input: str, runtime_config: dict[str, Any] | None = None) -> Optional[str]:
    """Process a single user query and return the last agent output."""
    state["messages"].append(HumanMessage(content=user_input))
    state["retry_count"] = 0  # Reset for new user input

    print("\n" + "-" * 30)
    print("⚙️ Processing...")

    last_agent_output = ""
    writer_output = None
    try:
        stream_config = {"recursion_limit": 50}
        if runtime_config:
            stream_config.update(runtime_config)

        for event in app.stream(state, stream_config):
            for node_name, value in event.items():
                if node_name == "Supervisor":
                    continue

                # Update state from node output
                if "messages" in value:
                    state["messages"].extend(value["messages"])
                    last_agent_output = value["messages"][-1].content
                    if node_name == "Writer" and not value.get("last_error"):
                        writer_output = last_agent_output

                if "data" in value:
                    state["data"].update(value.get("data", {}))

                if "retry_count" in value:
                    state["retry_count"] = value["retry_count"]

                if "last_error" in value:
                    state["last_error"] = value["last_error"]
                    print(f"  └── ⚠️ {node_name} failed. Attempting self-correction...")
                else:
                    print(f"  └── 🤖 {node_name} finished successfully.")
                    state["last_error"] = None

        if not writer_output or state.get("last_error"):
            logger.error("Workflow ended without a successful Writer response.")
            return None

        print("-" * 30)
        print("\n✨ FINAL RESPONSE:")
        print(writer_output)
        print("\n" + "=" * 50)
        return writer_output
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
        print(f"\n❌ A fatal error occurred: {e}")
        return None

def run_interaction(
    app,
    initial_query: Optional[str] = None,
    interactive: bool = True,
    runtime_config: dict[str, Any] | None = None,
):
    """Run an interactive loop or a single smoke-test turn."""
    state = create_initial_state()
    completed_turn = False
    failed_turn = False

    print("\n" + "=" * 50)
    print("🚀 Hierarchical Agent System Ready (Self-Correction Enabled)")
    print("=" * 50 + "\n")

    pending_query = initial_query
    while True:
        if pending_query is not None:
            user_input = pending_query
            pending_query = None
            print(f"User Query: {user_input}")
        elif interactive:
            try:
                user_input = input("\nUser > ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
            except EOFError:
                break
        else:
            break

        if not user_input.strip():
            if not interactive:
                break
            continue

        result = process_turn(app, state, user_input, runtime_config=runtime_config)
        completed_turn = completed_turn or result is not None
        failed_turn = failed_turn or result is None

        if not interactive:
            break

    if interactive:
        return not failed_turn

    return completed_turn and not failed_turn

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Hierarchical agent orchestration runner.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run one non-interactive turn with a built-in query and exit.",
    )
    parser.add_argument(
        "--query",
        help="Run a single non-interactive turn with a custom query and exit.",
    )
    parser.add_argument(
        "--min-api-delay", "--llm-call-delay-seconds",
        type=float,
        default=None,
        help="Minimum delay in seconds between LLM API calls. Defaults to MIN_API_DELAY_SECONDS or 0.",
    )
    parser.add_argument(
        "--disable-tracing",
        action="store_true",
        help="Disable LangSmith tracing for this run, even if LANGCHAIN_TRACING_V2=true is set.",
    )
    return parser.parse_args(argv)

def parse_min_api_delay(cli_delay: float | None) -> float:
    """Resolve the minimum delay from CLI or environment configuration."""
    if cli_delay is not None:
        return max(0.0, cli_delay)

    env_delay = os.getenv("MIN_API_DELAY_SECONDS")
    if not env_delay:
        return resolve_llm_delay_seconds()

    try:
        return max(0.0, float(env_delay))
    except ValueError:
        logger.warning(
            f"Invalid MIN_API_DELAY_SECONDS value '{env_delay}'. Falling back to 0.0."
        )
        return 0.0

def main(argv=None):
    args = parse_args(argv)
    tracing_enabled = configure_tracing(disabled=args.disable_tracing)
    with tracing_context(enabled=tracing_enabled):
        return run(args)


def run(args):
    """Run the workflow within the selected tracing context."""
    try:
        validate_database()
        min_api_delay = parse_min_api_delay(args.min_api_delay)
        # CLI throttling belongs to the shared callback, including tool model calls.
        llm = create_llm(call_delay_seconds=0)
    except RuntimeError as exc:
        logger.error(str(exc))
        return 1

    runtime_config = create_runtime_config(min_api_delay)

    logger.info(f"🔧 API call delay configured to {min_api_delay:.2f}s")
    app = build_graph(llm, runtime_config=runtime_config)

    non_interactive = args.smoke_test or args.query is not None
    initial_task = args.query if args.query is not None else (
        DEFAULT_SMOKE_QUERY if args.smoke_test else None
    )

    if non_interactive:
        logger.info("Running in non-interactive mode.")

    success = run_interaction(
        app,
        initial_query=initial_task,
        interactive=not non_interactive,
        runtime_config=runtime_config,
    )
    return 0 if success else 1

if __name__ == "__main__":
    raise SystemExit(main())
