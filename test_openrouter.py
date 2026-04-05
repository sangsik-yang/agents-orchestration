import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

def test_llm():
    print("Testing OpenRouter connection...")
    try:
        llm = ChatOpenAI(
            model="stepfun/step-3.5-flash:free",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
            max_retries=1,
            timeout=30
        )
        print("Sending request...")
        response = llm.invoke([HumanMessage(content="Say 'Hello World'")])
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_llm()
