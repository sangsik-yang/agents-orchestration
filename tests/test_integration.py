import pytest
from unittest.mock import MagicMock, patch
from main import build_graph
from langchain_core.messages import HumanMessage, AIMessage
from agents.supervisor import RouteResponse
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.callbacks import BaseCallbackHandler
import sqlite3
import main

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


def test_real_sql_and_writer_graph_with_scripted_model(tmp_path, monkeypatch):
    """Exercise real nodes and SQLite tools without an external model service."""
    monkeypatch.chdir(tmp_path)
    with sqlite3.connect("titanic.db") as conn:
        conn.execute("CREATE TABLE titanic (sex TEXT, survived INTEGER)")
        conn.executemany("INSERT INTO titanic VALUES (?, ?)", [
            ("female", 1), ("female", 1), ("female", 0), ("male", 0),
        ])

    model = FakeMessagesListChatModel(responses=[
        AIMessage(content='{"next":"SQLQueryer","instruction":"Calculate female survival rate."}'),
        AIMessage(content="", tool_calls=[{
            "name": "sql_db_query", "id": "query-1",
            "args": {"query": "SELECT 100.0 * SUM(survived) / COUNT(*) FROM titanic WHERE sex = 'female'"},
        }]),
        AIMessage(content="Female survival rate: 66.67%."),
        AIMessage(content='{"next":"Writer","instruction":"Summarize the SQL result."}'),
        AIMessage(content="2 out of 3 female passengers survived (66.67%)."),
        AIMessage(content='{"next":"FINISH","instruction":"Done."}'),
    ])
    tool_outputs = []

    class CaptureTools(BaseCallbackHandler):
        def on_tool_end(self, output, **kwargs):
            tool_outputs.append(str(output))

    config = {"callbacks": [CaptureTools()]}
    app = main.build_graph(model, runtime_config=config)
    state = main.create_initial_state()
    output = main.process_turn(app, state, "Analyze female survival.", runtime_config=config)

    assert output == "2 out of 3 female passengers survived (66.67%)."
    assert state["data"]["last_sql_result"] == "Female survival rate: 66.67%."
    assert any("66.66666666666667" in output for output in tool_outputs)
