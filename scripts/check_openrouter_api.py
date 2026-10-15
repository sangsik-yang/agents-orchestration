from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from config import OPENROUTER_BASE_URL, get_openrouter_api_key, get_openrouter_model

load_dotenv()


def main() -> None:
    print("Testing OpenRouter connection...")
    try:
        llm = ChatOpenAI(
            model=get_openrouter_model(),
            openai_api_key=get_openrouter_api_key(),
            base_url=OPENROUTER_BASE_URL,
            temperature=0,
            request_timeout=30,
        )
        print("Sending request...")
        response = llm.invoke([HumanMessage(content="Say 'Hello World'")])
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
