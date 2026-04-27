from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from config import OPENROUTER_BASE_URL, get_openrouter_api_key, get_openrouter_model

load_dotenv()


class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "SQLQueryer", "FINISH"]
    instruction: str = "Proceed with the assigned task."


def main() -> None:
    print("Testing Structured Output with OpenRouter...")
    try:
        llm = ChatOpenAI(
            model=get_openrouter_model(),
            openai_api_key=get_openrouter_api_key(),
            base_url=OPENROUTER_BASE_URL,
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
    main()
