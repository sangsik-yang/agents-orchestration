from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
import os

def sql_query_node(state, llm: ChatOpenAI):
    """SQL Query worker using LangChain's SQL agent."""
    db = SQLDatabase.from_uri("sqlite:///titanic.db")
    
    # Create the SQL agent with return_intermediate_steps=True
    # We specify it in both constructor and potentially by attribute for safety
    sql_agent = create_sql_agent(
        llm,
        db=db,
        agent_type="openai-tools",
        verbose=False,
        return_intermediate_steps=True
    )
    sql_agent.return_intermediate_steps = True
    
    # Run the agent
    result = sql_agent.invoke({"input": state["messages"][-1].content})
    
    # Extract SQL queries from intermediate steps
    intermediate_steps = result.get("intermediate_steps", [])
    sql_queries = []
    
    for step in intermediate_steps:
        # step is a tuple (AgentAction, Observation)
        action = step[0]
        
        # Check tool input in various formats
        query = None
        if hasattr(action, "tool") and action.tool == "sql_db_query":
            query = action.tool_input
        elif hasattr(action, "tool_calls"):
            for call in action.tool_calls:
                if call.get("name") == "sql_db_query":
                    query = call.get("args", {}).get("query")
                elif call.get("name") == "sql_db_query_checker":
                     query = f"-- Checker Query:\n{call.get('args', {}).get('query')}"
        
        if query:
            # If query is a dictionary, try to get the 'query' field
            if isinstance(query, dict):
                query = query.get("query", str(query))
            sql_queries.append(query)

    if sql_queries:
        print("\n[SQL Queryer - Generated SQL]")
        for i, query in enumerate(sql_queries, 1):
            if query:
                print(f"--- Query {i} ---\n{query}")
    
    # Return the final output message
    return {"messages": [AIMessage(content=result["output"])]}
