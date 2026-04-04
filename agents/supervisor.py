from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "SQLQueryer", "FINISH"]

def create_supervisor(llm: ChatOpenAI):
    """Supervisor agent to route the conversation."""
    system_prompt = (
        "You are the manager of a research, writing, and data analysis team."
        "\nYour goal is to coordinate between the Researcher, the Writer, and the SQLQueryer."
        "\n1. If a task needs real-time information from the web, call the Researcher."
        "\n2. If a task involves structured data analysis on the Titanic dataset, call the SQLQueryer."
        "\n3. If research or data analysis is complete, call the Writer to summarize."
        "\n4. If the final output is ready, output FINISH."
    )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Who should go next? (Researcher, Writer, or FINISH)"
            ),
        ]
    )
    
    # Use structured output to force the choice
    return prompt | llm.with_structured_output(RouteResponse)
