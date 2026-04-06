from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from logger import logger
import json

def writer_node(state, llm: ChatOpenAI):
    """Writer agent logic."""
    writer_agent = create_react_agent(
        llm,
        tools=[],
        prompt="""You are a professional writer. Your goal is to synthesize findings into a clear and concise summary.
        You should prioritize the data provided in the 'shared_data' context when creating your summary.
        If the 'shared_data' is empty, look at the conversation history."""
    )
    
    # Enrich the input with shared data for better context
    shared_data_str = json.dumps(state.get("data", {}), indent=2)
    enriched_input = f"Shared Data Context: {shared_data_str}\n\nTask: {state['messages'][-1].content}"
    
    # We invoke with a fresh state that includes the enriched context
    # but still pass the previous messages to maintain continuity if needed.
    result = writer_agent.invoke({
        "messages": state["messages"] + [HumanMessage(content=enriched_input)]
    })
    
    last_msg = result["messages"][-1]
    
    return {
        "messages": [AIMessage(content=last_msg.content, name="Writer")]
    }
