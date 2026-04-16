import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from typing import Literal

load_dotenv()


class RouteResponse(BaseModel):
    next: Literal["Researcher", "Writer", "SQLQueryer", "FINISH"]
    instruction: str = "Proceed with the assigned task."


def test_structured():
    print("Testing Structured Output with Google Gemini...")
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0,
            request_timeout=45,
            convert_system_message_to_human=True,
        )

        structured_llm = llm.with_structured_output(RouteResponse)
        print("Sending request to structured LLM...")
        response = structured_llm.invoke([HumanMessage(content="Analyze the Titanic dataset.")])
        print(f"Result: {response}")
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_structured()
