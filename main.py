import os
from functools import partial
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Local imports
from state import AgentState
from agents.supervisor import create_supervisor
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.sql_queryer import sql_query_node

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY is not set. The program will likely fail.")

def build_graph(llm: ChatOpenAI):
    """Assemble the hierarchical graph with SQLQueryer."""
    workflow = StateGraph(AgentState)
    
    # Define the nodes
    supervisor = create_supervisor(llm)
    
    def call_supervisor(state):
        result = supervisor.invoke(state)
        return {"next": result.next}
    
    # Worker nodes
    def run_researcher(state):
        return researcher_node(state, llm)
    
    def run_writer(state):
        return writer_node(state, llm)
    
    def run_sql_queryer(state):
        return sql_query_node(state, llm)
    
    # Add nodes to graph
    workflow.add_node("Supervisor", call_supervisor)
    workflow.add_node("Researcher", run_researcher)
    workflow.add_node("Writer", run_writer)
    workflow.add_node("SQLQueryer", run_sql_queryer)
    
    # Define edges
    workflow.add_edge(START, "Supervisor")
    
    # Add conditional edges
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
    
    # Workers always return to the supervisor
    workflow.add_edge("Researcher", "Supervisor")
    workflow.add_edge("Writer", "Supervisor")
    workflow.add_edge("SQLQueryer", "Supervisor")
    
    return workflow.compile()

if __name__ == "__main__":
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Build the graph
    app = build_graph(llm)
    
    # Scenario: Query Titanic data and summarize
    initial_state = {
        "messages": [
            ("user", "Analyze the Titanic dataset: What was the survival rate of female passengers? "
                     "Then summarize the finding in a professional tone.")
        ],
        "next": "Supervisor",
        "data": {}
    }
    
    print("--- Starting Hierarchical Orchestration (with SQL Queryer) ---")
    for event in app.stream(initial_state):
        for key, value in event.items():
            print(f"\n[Node: {key}]")
            if "messages" in value:
                content = value['messages'][-1].content
                # Print a bit more of the message
                print(f"Message: {content[:300]}...")
            elif "next" in value:
                print(f"Next: {value['next']}")
    print("\n--- Orchestration Finished ---")
