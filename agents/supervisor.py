import json
from typing import Literal, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from logger import logger

class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "SQLQueryer", "FINISH"]
    instruction: str = "Proceed with the assigned task."

def create_supervisor(llm: ChatOpenAI):
    """Supervisor agent to route the conversation and handle errors."""
    system_prompt = (
        "You are the manager of a research, writing, and data analysis team."
        "\nYour goal is to coordinate between the Researcher, the Writer, and the SQLQueryer."
        "\n\n### ERROR RECOVERY & SELF-CORRECTION ###"
        "\n- If the previous worker failed with an error (see the last message), you must analyze the error message."
        "\n- Provide a specific CORRECTION INSTRUCTION to the same worker to fix the error."
        "\n- For SQL errors, suggest fixing table names or query syntax."
        "\n- For Search errors, suggest different keywords."
        "\n- If a worker has failed 3 times (check messages), you MUST either try a different approach (e.g., Researcher instead of SQLQueryer) or ask the Writer to explain the limitation to the user."
        "\n\n### WORKERS ###"
        "\n- Researcher: Real-time web search via DuckDuckGo."
        "\n- SQLQueryer: Titanic dataset (SQLite) analysis (Table: 'titanic')."
        "\n- Writer: Summarizing and synthesizing findings into a final report."
        "\n\n### RESPONSE FORMAT ###"
        "\nYou MUST respond with a valid JSON object only. No other text."
        "\nExample: {{ \"next\": \"SQLQueryer\", \"instruction\": \"Calculate survival rates of children under 10.\" }}"
        "\n\n### DECISION RULES ###"
        "\n1. Analyze the history and 'data' provided (if any)."
        "\n2. Determine the next worker and provide clear, specific 'instruction'."
        "\n3. Set 'next' to FINISH only when the final summary is provided by the Writer."
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
    
    def parse_output(ai_message):
        content = ai_message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        try:
            data = json.loads(content)
            return RouteResponse(**data)
        except Exception as e:
            logger.error(f"Supervisor Parse Error: {e} | Content: {content}")
            if "FINISH" in content.upper():
                return RouteResponse(next="FINISH", instruction="Completed.")
            return RouteResponse(next="Writer", instruction="Synthesize findings or explain the error.")

    return prompt | llm | parse_output
