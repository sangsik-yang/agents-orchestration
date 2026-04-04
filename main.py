import os
from functools import partial
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Local imports
from state import AgentState
from agents.supervisor import create_supervisor
from agents.researcher import researcher_node, search_tool
from agents.writer import writer_node

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY is not set. The program will likely fail.")

def build_graph(llm: ChatOpenAI):
    """Assemble the hierarchical graph."""
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Define the nodes
    # Supervisor
    supervisor = create_supervisor(llm)
    
    # Function to call supervisor and update 'next'
    def call_supervisor(state):
        result = supervisor.invoke(state)
        return {"next": result.next}
    
    # Function to run researcher and return messages
    def run_researcher(state):
        return researcher_node(state, llm)
    
    # Function to run writer and return messages
    def run_writer(state):
        return writer_node(state, llm)
    
    # Tool node for researcher (if needed, but researcher_node handles it)
    # tool_node = ToolNode([search_tool])
    
    # Add nodes to graph
    workflow.add_node("Supervisor", call_supervisor)
    workflow.add_node("Researcher", run_researcher)
    workflow.add_node("Writer", run_writer)
    
    # Define edges
    workflow.add_edge(START, "Supervisor")
    
    # Add conditional edges from Supervisor to Researcher, Writer or END
    workflow.add_conditional_edges(
        "Supervisor",
        lambda x: x["next"],
        {
            "Researcher": "Researcher",
            "Writer": "Writer",
            "FINISH": END
        }
    )
    
    # Workers always return to the supervisor
    workflow.add_edge("Researcher", "Supervisor")
    workflow.add_edge("Writer", "Supervisor")
    
    return workflow.compile()

if __name__ == "__main__":
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Build the graph
    app = build_graph(llm)
    
    # Initial task
    initial_state = {
        "messages": [
            ("user", "Research the latest AI breakthroughs of 2024 and write a short summary.")
        ],
        "next": "Supervisor",
        "data": {}
    }
    
    print("--- Starting Hierarchical Orchestration ---")
    for event in app.stream(initial_state):
        for key, value in event.items():
            print(f"\n[Node: {key}]")
            if "messages" in value:
                print(f"Message: {value['messages'][-1].content[:200]}...")
            elif "next" in value:
                print(f"Next: {value['next']}")
    print("\n--- Orchestration Finished ---")
