from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent
from typing import Any

# Use DuckDuckGo Search
search_tool = DuckDuckGoSearchRun()
tools = [search_tool]

def researcher_node(state, llm: Any):
    """Researcher agent logic using a ReAct agent."""
    researcher_agent = create_react_agent(
        llm, 
        tools=tools,
        prompt="You are a meticulous researcher. Your goal is to gather accurate information using your search tool."
    )
    
    # Run the agent
    result = researcher_agent.invoke(state)
    last_msg = result["messages"][-1]
    
    data = dict(state.get("data", {}))
    search_history = list(data.get("search_history", []))
    search_history.append(last_msg.content)
    data["search_history"] = search_history
    
    return {
        "messages": [last_msg],
        "data": data
    }
