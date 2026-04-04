from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

def writer_node(state, llm: ChatOpenAI):
    """Writer agent logic."""
    writer_agent = create_react_agent(
        llm,
        tools=[],
        state_modifier="You are a professional writer. Your goal is to synthesize findings into a clear and concise summary."
    )
    result = writer_agent.invoke(state)
    return {"messages": [result["messages"][-1]]}
