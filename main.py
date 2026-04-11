import argparse
import os
from functools import partial
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

# Local imports
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

# Load environment variables
load_dotenv()

DEFAULT_SMOKE_QUERY = (
    "Analyze the Titanic dataset: What was the survival rate of female passengers? "
    "Then summarize the finding."
)

# Global references
supervisor_instance = None

def create_llm() -> ChatOpenAI:
    """Create the OpenRouter-backed chat model."""
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise RuntimeError("Missing API Key: OPENROUTER_API_KEY must be set in .env")

    return ChatOpenAI(
        model="z-ai/glm-4.5-air:free",
        openai_api_key=openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/sangsik-yang/agents-orchestration",
            "X-Title": "Agents Orchestration",
        },
        temperature=0,
        timeout=120,
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

def call_supervisor(state: AgentState) -> Dict[str, Any]:
    global supervisor_instance
    try:
        log_node_start("Supervisor")
        
        # Determine if we are in a retry loop
        current_agent = state.get("next")
        last_error = state.get("last_error")
        
        result = supervisor_instance.invoke(state)
        
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

def run_researcher(state: AgentState, llm: ChatOpenAI):
    log_node_start("Researcher")
    try:
        res = researcher_node(state, llm)
        log_node_end("Researcher")
        return res
    except Exception as e:
        log_error("Researcher", str(e))
        return {
            "messages": [HumanMessage(content=f"Error in Researcher: {str(e)}", name="System")],
            "last_error": str(e)
        }

def run_writer(state: AgentState, llm: ChatOpenAI):
    log_node_start("Writer")
    try:
        res = writer_node(state, llm)
        log_node_end("Writer")
        return res
    except Exception as e:
        log_error("Writer", str(e))
        return {
            "messages": [HumanMessage(content=f"Error in Writer: {str(e)}", name="System")],
            "last_error": str(e)
        }

def run_sql_queryer(state: AgentState, llm: ChatOpenAI):
    log_node_start("SQLQueryer")
    try:
        res = sql_query_node(state, llm)
        log_node_end("SQLQueryer")
        return res
    except Exception as e:
        log_error("SQLQueryer", str(e))
        # We pass the error back to the supervisor to let it decide what to do
        return {
            "messages": [HumanMessage(content=f"Error in SQLQueryer: {str(e)}. Please fix the query or table name.", name="System")],
            "last_error": str(e)
        }

def build_graph(llm: ChatOpenAI):
    """Assemble the hierarchical graph."""
    global supervisor_instance
    workflow = StateGraph(AgentState)
    
    supervisor_instance = create_supervisor(llm)
    
    workflow.add_node("Supervisor", call_supervisor)
    workflow.add_node("Researcher", partial(run_researcher, llm=llm))
    workflow.add_node("Writer", partial(run_writer, llm=llm))
    workflow.add_node("SQLQueryer", partial(run_sql_queryer, llm=llm))
    
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

def process_turn(app, state: AgentState, user_input: str) -> str:
    """Process a single user query and return the last agent output."""
    state["messages"].append(HumanMessage(content=user_input))
    state["retry_count"] = 0  # Reset for new user input

    print("\n" + "-" * 30)
    print("⚙️ Processing...")

    last_agent_output = ""
    try:
        for event in app.stream(state, {"recursion_limit": 50}):
            for node_name, value in event.items():
                if node_name == "Supervisor":
                    continue

                # Update state from node output
                if "messages" in value:
                    state["messages"].extend(value["messages"])
                    last_agent_output = value["messages"][-1].content

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

        print("-" * 30)
        print("\n✨ FINAL RESPONSE:")
        print(last_agent_output)
        print("\n" + "=" * 50)
        return last_agent_output
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
        print(f"\n❌ A fatal error occurred: {e}")
        return ""

def run_interaction(
    app,
    initial_query: Optional[str] = None,
    interactive: bool = True,
):
    """Run an interactive loop or a single smoke-test turn."""
    state = create_initial_state()

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

        process_turn(app, state, user_input)

        if not interactive:
            break

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
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)

    # Check LangSmith Tracing
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    if tracing_enabled:
        project_name = os.getenv("LANGCHAIN_PROJECT", "default")
        logger.info(f"🔍 LangSmith Tracing is ENABLED (Project: {project_name})")
    else:
        logger.warning("🔍 LangSmith Tracing is DISABLED (Set LANGCHAIN_TRACING_V2=true in .env)")

    try:
        llm = create_llm()
    except RuntimeError as exc:
        logger.error(str(exc))
        return 1

    app = build_graph(llm)

    non_interactive = args.smoke_test or args.query is not None
    initial_task = args.query if args.query is not None else (
        DEFAULT_SMOKE_QUERY if args.smoke_test else None
    )

    if non_interactive:
        logger.info("Running in non-interactive mode.")

    run_interaction(
        app,
        initial_query=initial_task,
        interactive=not non_interactive,
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
