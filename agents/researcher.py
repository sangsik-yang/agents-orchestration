from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from logger import logger

# Use DuckDuckGo Search
search_tool = DuckDuckGoSearchRun()
tools = [search_tool]

def researcher_node(state, llm: ChatOpenAI):
    """Researcher agent logic using a ReAct agent."""
    researcher_agent = create_react_agent(
        llm, 
        tools=tools,
        prompt="You are a meticulous researcher. Your goal is to gather accurate information using your search tool."
    )
    
    # Run the agent
    result = researcher_agent.invoke(state)
    last_msg = result["messages"][-1]
    
    # Update shared data
    if "data" not in state:
        state["data"] = {}
    
    if "search_history" not in state["data"]:
        state["data"]["search_history"] = []
    
    state["data"]["search_history"].append(last_msg.content)
    
    return {
        "messages": [last_msg],
        "data": state["data"]
    }
