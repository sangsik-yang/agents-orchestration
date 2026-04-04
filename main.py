import os
import sys
from functools import partial
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

# Local imports
from state import AgentState
from agents.supervisor import create_supervisor
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.sql_queryer import sql_query_node

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("Error: GOOGLE_API_KEY is not set.")
    sys.exit(1)

# Global references
supervisor_instance = None

def call_supervisor(state):
    global supervisor_instance
    result = supervisor_instance.invoke(state)
    
    # Print the supervisor's decision and instruction for easier monitoring
    print(f"\n[Supervisor Decision]")
    print(f"Target Agent: {result.next}")
    print(f"Instruction : {result.instruction}")
    
    return {
        "next": result.next,
        "messages": [AIMessage(content=f"To {result.next}: {result.instruction}", name="Supervisor")]
    }

def run_researcher(state, llm):
    return researcher_node(state, llm)

def run_writer(state, llm):
    return writer_node(state, llm)

def run_sql_queryer(state, llm):
    return sql_query_node(state, llm)

def build_graph(llm: ChatGoogleGenerativeAI):
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

def run_interaction(app, initial_query=None):
    """Run an interactive loop for the agent system."""
    state = {
        "messages": [],
        "next": "Supervisor",
        "data": {}
    }
    
    print("--- Hierarchical Agent System Ready ---")
    
    is_first_run = True
    while True:
        if is_first_run and initial_query:
            user_input = initial_query
            is_first_run = False
            print(f"\n[Initial Task]: {user_input}")
        else:
            try:
                user_input = input("\nUser (type 'exit' to quit): ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
            except EOFError:
                break
        
        if not user_input.strip():
            continue

        state["messages"].append(HumanMessage(content=user_input))
        
        # Stream the graph execution
        for event in app.stream(state, {"recursion_limit": 20}):
            for key, value in event.items():
                if key == "Supervisor":
                    # Supervisor info is already printed in call_supervisor function
                    continue
                
                print(f"\n[Node: {key}]")
                if "messages" in value:
                    content = value['messages'][-1].content
                    print(f"Result: {content[:1000]}...")
                
                # Update state messages for persistence
                if "messages" in value:
                    state["messages"].extend(value["messages"])

if __name__ == "__main__":
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    app = build_graph(llm)
    
    initial_task = "Analyze the Titanic dataset: What was the survival rate of female passengers? Then summarize the finding."
    run_interaction(app, initial_query=initial_task)
