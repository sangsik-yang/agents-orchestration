from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "SQLQueryer", "FINISH"]
    instruction: str = "Proceed with the assigned task."

def create_supervisor(llm: ChatGoogleGenerativeAI):
    """Supervisor agent to route the conversation."""
    system_prompt = (
        "You are the manager of a research, writing, and data analysis team."
        "\nYour goal is to coordinate between the Researcher, the Writer, and the SQLQueryer."
        "\n\nYOUR TASKS:"
        "\n1. Analyze the conversation history."
        "\n2. Determine which worker should act next."
        "\n3. Provide a clear, specific 'instruction' for that worker explaining what they need to do or what information is missing."
        "\n4. If a worker's previous answer was insufficient, tell them exactly what to fix or add in the 'instruction'."
        "\n5. If the task is complete, set 'next' to FINISH."
        "\n\nWORKERS:"
        "\n- Researcher: Real-time web search."
        "\n- SQLQueryer: Titanic dataset (SQLite) analysis."
        "\n- Writer: Summarizing and synthesizing findings."
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
