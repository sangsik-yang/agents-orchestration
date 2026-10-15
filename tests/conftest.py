import pytest
from langsmith import tracing_context


@pytest.fixture(autouse=True)
def disable_test_tracing(monkeypatch):
    """Keep unit tests independent of .env tracing and external services."""
    for key in (
        "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING_V2",
        "LANGSMITH_TRACING", "LANGCHAIN_TRACING",
    ):
        monkeypatch.setenv(key, "false")
    with tracing_context(enabled=False):
        yield
