from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
import os

def sql_query_node(state, llm: ChatOpenAI):
    """SQL Query worker using LangChain's SQL agent."""
    db = SQLDatabase.from_uri("sqlite:///titanic.db")
    
    # Create the SQL agent
    sql_agent = create_sql_agent(
        llm,
        db=db,
        agent_type="openai-tools",
        verbose=False
    )
    
    # Run the agent on the latest user message
    # We pass the message history to provide context
    result = sql_agent.invoke({"input": state["messages"][-1].content})
    
    # Return the final output message from the agent
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content=result["output"])]}
