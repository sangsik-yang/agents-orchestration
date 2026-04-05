from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

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
    # The agent expects a list of messages
    result = researcher_agent.invoke(state)
    
    # We want to return the last message from the agent's run
    return {"messages": [result["messages"][-1]]}
