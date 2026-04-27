from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import AIMessage
from config import get_titanic_db_uri
from logger import logger
from typing import Any

def sql_query_node(state, llm: Any):
    """SQL Query worker using LangChain's SQL agent."""
    db = SQLDatabase.from_uri(get_titanic_db_uri())
    
    # Create the SQL agent
    sql_agent = create_sql_agent(
        llm,
        db=db,
        agent_type="openai-tools",
        verbose=False,
        return_intermediate_steps=True
    )
    
    # Run the agent
    # We pass the last message (instruction) as the main goal
    last_instruction = state["messages"][-1].content
    result = sql_agent.invoke({"input": last_instruction})
    
    data = dict(state.get("data", {}))

    # Save the last output to the shared data for the Writer to use
    data["last_sql_result"] = result["output"]
    
    # Extract SQL queries for logging
    intermediate_steps = result.get("intermediate_steps", [])
    sql_queries = []
    for step in intermediate_steps:
        action = step[0]
        if hasattr(action, "tool_calls"):
            for call in action.tool_calls:
                if "query" in call.get("args", {}):
                    sql_queries.append(call["args"]["query"])
    
    if sql_queries:
        logger.debug(f"SQLQueryer executed {len(sql_queries)} queries.")
        # For transparency, we could store queries too
        data["last_sql_queries"] = sql_queries

    # Return the final output message and updated data
    return {
        "messages": [AIMessage(content=result["output"], name="SQLQueryer")],
        "data": data
    }
