import json
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "SQLQueryer", "FINISH"]
    instruction: str = "Proceed with the assigned task."

def create_supervisor(llm: ChatOpenAI):
    """Supervisor agent to route the conversation."""
    system_prompt = (
        "You are the manager of a research, writing, and data analysis team."
        "\nYour goal is to coordinate between the Researcher, the Writer, and the SQLQueryer."
        "\n\nIMPORTANT:"
        "\n- NEVER output FINISH for the first user message. You must always use at least one worker first."
        "\n- If the user asks for data analysis on Titanic, you MUST call the SQLQueryer."
        "\n- If the user asks for web research, you MUST call the Researcher."
        "\n- Only output FINISH after a worker (like Writer) has provided the final summarized result to the user's satisfaction."
        "\n\nRESPONSE FORMAT:"
        "\nYou MUST respond with a valid JSON object only. No other text."
        "\nExample: {{ \"next\": \"SQLQueryer\", \"instruction\": \"Calculate survival rates.\" }}"
        "\n\nYOUR TASKS:"
        "\n1. Analyze the conversation history."
        "\n2. Determine which worker should act next."
        "\n3. Provide a clear, specific 'instruction' for that worker."
        "\n4. If the task is complete and a final summary is ready, set 'next' to FINISH."
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
                "Who should go next? Respond in JSON format with 'next' and 'instruction' fields."
            ),
        ]
    )
    
    # Manual parsing because with_structured_output is unstable on free models
    def parse_output(ai_message):
        content = ai_message.content.strip()
        # Handle cases where the model might wrap JSON in code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        try:
            data = json.loads(content)
            return RouteResponse(**data)
        except Exception as e:
            # Fallback if parsing fails
            print(f"Warning: Failed to parse Supervisor output: {content}. Error: {e}")
            if "FINISH" in content.upper():
                return RouteResponse(next="FINISH", instruction="Completed.")
            return RouteResponse(next="Writer", instruction="Synthesize the findings so far.")

    return prompt | llm | parse_output
