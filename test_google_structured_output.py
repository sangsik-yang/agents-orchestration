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
            model=os.getenv("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free"),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            request_timeout=45,
        )

        structured_llm = llm.with_structured_output(RouteResponse)
        print("Sending request to structured LLM...")
        response = structured_llm.invoke([HumanMessage(content="Analyze the Titanic dataset.")])
        print(f"Result: {response}")
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_structured()
