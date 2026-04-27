import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.sql_queryer import sql_query_node

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    # Mock invoke return for standard nodes
    llm.invoke.return_value = AIMessage(content="Mocked response")
    return llm

@pytest.fixture
def initial_state():
    return {
        "messages": [HumanMessage(content="Test task")],
        "next": "",
        "data": {}
    }

def test_researcher_node(mock_llm, initial_state):
    # Mock create_react_agent
    with patch("agents.researcher.create_react_agent") as mock_create:
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [AIMessage(content="Research info")]}
        mock_create.return_value = mock_agent
        original_data = initial_state["data"]
        
        result = researcher_node(initial_state, mock_llm)
        
        assert "messages" in result
        assert result["messages"][0].content == "Research info"
        assert result["data"]["search_history"] == ["Research info"]
        assert initial_state["data"] is original_data
        assert initial_state["data"] == {}
        mock_create.assert_called_once()

def test_writer_node(mock_llm, initial_state):
    with patch("agents.writer.create_react_agent") as mock_create:
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [AIMessage(content="Written summary")]}
        mock_create.return_value = mock_agent
        
        result = writer_node(initial_state, mock_llm)
        
        assert "messages" in result
        assert result["messages"][0].content == "Written summary"
        mock_create.assert_called_once()

def test_sql_query_node(mock_llm, initial_state, monkeypatch):
    monkeypatch.delenv("TITANIC_DB_PATH", raising=False)
    # Mock SQLDatabase and create_sql_agent
    with patch("agents.sql_queryer.SQLDatabase") as mock_db, \
         patch("agents.sql_queryer.create_sql_agent") as mock_create:
        
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"output": "SQL analysis result"}
        mock_create.return_value = mock_agent
        original_data = initial_state["data"]
        
        result = sql_query_node(initial_state, mock_llm)
        
        assert "messages" in result
        assert result["messages"][0].content == "SQL analysis result"
        assert result["data"]["last_sql_result"] == "SQL analysis result"
        assert initial_state["data"] is original_data
        assert initial_state["data"] == {}
        mock_db.from_uri.assert_called_once_with("sqlite:///titanic.db")
        mock_create.assert_called_once()
