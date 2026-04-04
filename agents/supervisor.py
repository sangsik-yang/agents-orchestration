from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "FINISH"]

def create_supervisor(llm: ChatOpenAI):
    """Supervisor agent to route the conversation."""
    system_prompt = (
        "You are the manager of a research and writing team."
        "\nYour goal is to coordinate between the Researcher and the Writer."
        "\n1. If a task needs information, call the Researcher."
        "\n2. If research is complete, call the Writer to summarize."
        "\n3. If the final output is ready, output FINISH."
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
