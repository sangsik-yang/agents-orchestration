from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

import main
from config import get_titanic_db_uri


def test_main_smoke_mode_uses_builtin_query():
    with patch("main.create_llm") as mock_create_llm, \
         patch("main.validate_database") as mock_validate_database, \
         patch("main.build_graph") as mock_build_graph, \
         patch("main.run_interaction") as mock_run_interaction:
        mock_create_llm.return_value = MagicMock()
        mock_build_graph.return_value = MagicMock()
        mock_run_interaction.return_value = True

        exit_code = main.main(["--smoke-test"])

        assert exit_code == 0
        mock_validate_database.assert_called_once()
        mock_run_interaction.assert_called_once()
        _, kwargs = mock_run_interaction.call_args
        assert kwargs["interactive"] is False
        assert kwargs["initial_query"] == main.DEFAULT_SMOKE_QUERY


def test_run_interaction_non_interactive_skips_input():
    app = MagicMock()
    app.stream.return_value = iter(
        [{"Writer": {"messages": [AIMessage(content="final result")]}}]
    )

    with patch("builtins.input", side_effect=AssertionError("input should not be called")) as mock_input:
        result = main.run_interaction(app, initial_query="smoke query", interactive=False)

    assert result is True
    mock_input.assert_not_called()
    app.stream.assert_called_once()


def test_main_non_interactive_failure_returns_nonzero():
    with patch("main.create_llm") as mock_create_llm, \
         patch("main.validate_database"), \
         patch("main.build_graph") as mock_build_graph, \
         patch("main.run_interaction") as mock_run_interaction:
        mock_create_llm.return_value = MagicMock()
        mock_build_graph.return_value = MagicMock()
        mock_run_interaction.return_value = False

        exit_code = main.main(["--smoke-test"])

    assert exit_code == 1


def test_validate_database_rejects_missing_db(tmp_path):
    missing_db = tmp_path / "missing.db"

    with pytest.raises(RuntimeError) as exc_info:
        main.validate_database(str(missing_db))

    assert "Missing database" in str(exc_info.value)


@pytest.mark.parametrize("events", [
    [],
    [{"Researcher": {"messages": [AIMessage(content="research only")]}}],
    [{"Writer": {"messages": [AIMessage(content="")]}}],
    [{"Writer": {
        "messages": [AIMessage(content="failed")], "last_error": "API failure",
    }}],
])
def test_incomplete_workflow_fails(events):
    app = MagicMock()
    app.stream.return_value = iter(events)
    assert main.run_interaction(app, initial_query="task", interactive=False) is False


def test_disable_tracing_overrides_modern_env_and_restores_context(monkeypatch):
    from langsmith.utils import tracing_is_enabled
    monkeypatch.setenv("LANGSMITH_TRACING_V2", "true")
    with patch("main.run", side_effect=lambda args: int(tracing_is_enabled())):
        assert main.main(["--smoke-test", "--disable-tracing"]) == 0


def test_create_llm_defaults_to_free_router(monkeypatch):
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("main.ThrottledChatOpenAI") as model:
        main.create_llm()
    assert model.call_args.kwargs["model"] == "openrouter/free"
def test_create_llm_uses_openrouter_defaults(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "z-ai/glm-4.5-air:free")
    monkeypatch.setenv("OPENROUTER_LLM_CALL_DELAY_SECONDS", "4.5")
    monkeypatch.setenv("OPENROUTER_HTTP_REFERER", "https://example.com")
    monkeypatch.setenv("OPENROUTER_APP_TITLE", "agents-orchestration")

    llm = main.create_llm()

    assert isinstance(llm, main.ThrottledChatOpenAI)
    assert llm.model_name == "z-ai/glm-4.5-air:free"
    assert str(llm.openai_api_base) == main.OPENROUTER_BASE_URL
    assert llm.openai_api_key.get_secret_value() == "test-openrouter-key"
    assert llm.call_delay_seconds == 4.5
    assert llm.default_headers == {
        "HTTP-Referer": "https://example.com",
        "X-OpenRouter-Title": "agents-orchestration",
    }


def test_throttled_chat_openai_waits_before_next_slot():
    llm = main.ThrottledChatOpenAI(
        model="z-ai/glm-4.5-air:free",
        openai_api_key="test-openrouter-key",
        base_url=main.OPENROUTER_BASE_URL,
        call_delay_seconds=2.0,
    )
    llm._next_available_at = 10.0

    with patch("main.time.monotonic", side_effect=[8.0, 8.0]), patch(
        "main.time.sleep"
    ) as mock_sleep:
        llm._wait_for_slot()

    mock_sleep.assert_called_once_with(2.0)
    assert llm._next_available_at == 10.0


def test_titanic_db_uri_uses_env_path(monkeypatch):
    monkeypatch.setenv("TITANIC_DB_PATH", "data/custom.db")

    assert get_titanic_db_uri() == "sqlite:///data/custom.db"


def test_validate_database_uses_configured_path(tmp_path, monkeypatch):
    import sqlite3
    db_path = tmp_path / "custom.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE titanic (survived INTEGER)")
        conn.execute("INSERT INTO titanic VALUES (1)")
    monkeypatch.setenv("TITANIC_DB_PATH", str(db_path))
    main.validate_database()


def test_legacy_delay_option_and_environment_remain_supported(monkeypatch):
    monkeypatch.delenv("MIN_API_DELAY_SECONDS", raising=False)
    monkeypatch.setenv("OPENROUTER_LLM_CALL_DELAY_SECONDS", "4.5")
    assert main.parse_min_api_delay(None) == 4.5
    args = main.parse_args(["--llm-call-delay-seconds", "2"])
    assert main.parse_min_api_delay(args.min_api_delay) == 2.0
