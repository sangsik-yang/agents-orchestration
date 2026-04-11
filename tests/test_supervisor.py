import pytest
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from agents.supervisor import create_supervisor

def test_create_supervisor_routing(mock_llm):
    supervisor = create_supervisor(mock_llm)

    state = {"messages": [HumanMessage(content="Analyze titanic data")]}
    result = supervisor.invoke(state)

    assert result.next == "SQLQueryer"


@pytest.fixture
def mock_llm():
    return RunnableLambda(
        lambda _input: AIMessage(
            content='{"next": "SQLQueryer", "instruction": "Calculate survival rates."}'
        )
    )
