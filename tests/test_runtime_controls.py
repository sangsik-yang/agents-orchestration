from unittest.mock import MagicMock

import pytest
import runtime_controls
from runtime_controls import APICallLogger


def test_api_call_logger_throttles_model_calls(monkeypatch):
    fake_logger = MagicMock()
    sleep_calls = []
    monotonic_values = iter([100.0, 100.2, 101.0])

    monkeypatch.setattr(runtime_controls.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(runtime_controls.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    handler = APICallLogger(min_delay_seconds=1.0, logger_obj=fake_logger)

    handler.on_chat_model_start({"name": "gemini"}, [[{"text": "first"}]])
    handler.on_chat_model_start({"name": "gemini"}, [[{"text": "second"}]])

    assert sleep_calls == [pytest.approx(0.8)]
    assert any("LLM START #1" in call.args[0] for call in fake_logger.info.call_args_list)
    assert any("waiting 0.80s" in call.args[0] for call in fake_logger.info.call_args_list)


@pytest.fixture
def tracing_env(monkeypatch):
    for key in (
        "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING_V2",
        "LANGSMITH_TRACING", "LANGCHAIN_TRACING",
        "LANGSMITH_ENDPOINT", "LANGCHAIN_ENDPOINT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_tracing_default_and_explicit_disable_do_not_connect(monkeypatch, tracing_env):
    connect = MagicMock()
    monkeypatch.setattr(runtime_controls, "urlopen", connect)
    assert runtime_controls.configure_tracing() is False
    monkeypatch.setenv("LANGSMITH_TRACING_V2", "true")
    assert runtime_controls.configure_tracing(disabled=True) is False
    connect.assert_not_called()


def test_tracing_connection_failure_falls_back(monkeypatch, tracing_env):
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    connect = MagicMock(side_effect=OSError("offline"))
    monkeypatch.setattr(runtime_controls, "urlopen", connect)
    assert runtime_controls.configure_tracing() is False
    connect.assert_called_once_with("https://api.smith.langchain.com/info", timeout=2)


def test_tracing_modern_endpoint_and_flags_take_precedence(monkeypatch, tracing_env):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://tracing.example/")
    monkeypatch.setenv("LANGCHAIN_ENDPOINT", "https://ignored.example")
    connect = MagicMock()
    connect.return_value.__enter__.return_value.status = 200
    monkeypatch.setattr(runtime_controls, "urlopen", connect)
    assert runtime_controls.configure_tracing() is True
    connect.assert_called_once_with("https://tracing.example/info", timeout=2)
    monkeypatch.setenv("LANGSMITH_TRACING_V2", "false")
    assert runtime_controls.configure_tracing() is False
