from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

import main


def test_main_smoke_mode_uses_builtin_query():
    with patch("main.create_llm") as mock_create_llm, \
         patch("main.build_graph") as mock_build_graph, \
         patch("main.run_interaction") as mock_run_interaction:
        mock_create_llm.return_value = MagicMock()
        mock_build_graph.return_value = MagicMock()

        exit_code = main.main(["--smoke-test"])

        assert exit_code == 0
        mock_run_interaction.assert_called_once()
        _, kwargs = mock_run_interaction.call_args
        assert kwargs["interactive"] is False
        assert kwargs["initial_query"] == main.DEFAULT_SMOKE_QUERY


def test_run_interaction_non_interactive_skips_input():
    app = MagicMock()
    app.stream.return_value = iter(
        [{"Researcher": {"messages": [AIMessage(content="research result")]}}]
    )

    with patch("builtins.input", side_effect=AssertionError("input should not be called")) as mock_input:
        result = main.run_interaction(app, initial_query="smoke query", interactive=False)

    assert result is None
    mock_input.assert_not_called()
    app.stream.assert_called_once()


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
