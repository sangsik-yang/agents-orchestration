import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage
from agents.supervisor import create_supervisor, RouteResponse

@pytest.fixture
def mock_llm():
    return MagicMock()

def test_create_supervisor_routing(mock_llm):
    # supervisor = prompt | llm.with_structured_output(RouteResponse)
    
    # Mock the return value of with_structured_output
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    
    # When we do prompt | mock_structured_llm, it returns a Runnable
    # We need to mock the invoke of that final chain
    with patch("langchain_core.prompts.ChatPromptTemplate.from_messages") as mock_prompt_class:
        mock_prompt = MagicMock()
        mock_prompt_class.return_value = mock_prompt
        # Mock (prompt | llm) behavior
        mock_chain = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = RouteResponse(next="SQLQueryer")
        
        supervisor = create_supervisor(mock_llm)
        
        state = {"messages": [HumanMessage(content="Analyze titanic data")]}
        result = supervisor.invoke(state)
        
        assert result.next == "SQLQueryer"
