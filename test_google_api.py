import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()


def test_llm():
    print("Testing Google Gemini connection...")
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0,
            request_timeout=30,
            convert_system_message_to_human=True,
        )
        print("Sending request...")
        response = llm.invoke([HumanMessage(content="Say 'Hello World'")])
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_llm()
