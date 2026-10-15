import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from typing import Literal

load_dotenv()


class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "SQLQueryer", "FINISH"]
    instruction: str = "Proceed with the assigned task."


def test_structured():
    print("Testing Structured Output with OpenRouter...")
    try:
        llm = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openrouter/free"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            temperature=0,
            timeout=45,
        )

        structured_llm = llm.with_structured_output(RouteResponse)
        print("Sending request to structured LLM...")
        response = structured_llm.invoke([HumanMessage(content="Analyze the Titanic dataset.")])
        print(f"Result: {response}")
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_structured()
