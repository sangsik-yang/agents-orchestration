import pytest
from unittest.mock import MagicMock, patch
from main import build_graph
from langchain_core.messages import HumanMessage, AIMessage
from agents.supervisor import RouteResponse

def test_full_graph_orchestration():
    """Test the full graph flow using a mocked LLM and mocked supervisor nodes."""
    mock_llm = MagicMock()
    
    # Patch call_supervisor because it is the actual node function in the graph
    with patch("main.call_supervisor") as mock_call_sup, \
         patch("main.run_sql_queryer") as mock_run_sql:
        
        # Mock the supervisor node's behavior to return the dict expected by the graph
        mock_call_sup.side_effect = [
            {"next": "SQLQueryer"},
            {"next": "FINISH"}
        ]
        
        # Mock the SQL worker node
        mock_run_sql.return_value = {"messages": [AIMessage(content="Data analysis result")]}
        
        # Build the graph
        app = build_graph(mock_llm)
        
        # Initial task
        initial_state = {
            "messages": [HumanMessage(content="Analyze the Titanic dataset.")],
            "next": "Supervisor",
            "data": {}
        }
        
        # Run the graph
        events = list(app.stream(initial_state))
        
        # Node execution sequence check
        node_names = [list(event.keys())[0] for event in events]
        
        # Expected nodes: Supervisor, SQLQueryer, Supervisor
        assert "Supervisor" in node_names
        assert "SQLQueryer" in node_names
        
        assert mock_call_sup.call_count == 2
        assert mock_run_sql.call_count == 1
