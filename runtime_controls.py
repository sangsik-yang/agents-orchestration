from __future__ import annotations

import json
import os
import threading
import time
from typing import Any
from urllib.request import urlopen

from langchain_core.callbacks import BaseCallbackHandler

from logger import logger


def configure_tracing(disabled: bool = False) -> bool:
    """Enable requested tracing only when its endpoint is reachable."""
    setting = next(
        (os.environ[key] for key in (
            "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING_V2",
            "LANGSMITH_TRACING", "LANGCHAIN_TRACING",
        ) if os.environ.get(key, "").strip()),
        "false",
    )
    if disabled or setting.strip().lower() != "true":
        logger.info("🔍 LangSmith tracing disabled.")
        return False

    endpoint = (
        os.getenv("LANGSMITH_ENDPOINT") or os.getenv("LANGCHAIN_ENDPOINT")
        or "https://api.smith.langchain.com"
    ).strip().strip("\"'").rstrip("/")
    try:
        # Public health information; no API key or run payload is sent.
        with urlopen(f"{endpoint}/info", timeout=2) as response:
            if response.status != 200:
                raise RuntimeError("Unhealthy tracing endpoint")
    except Exception as exc:
        logger.warning(
            f"🔍 LangSmith unavailable ({type(exc).__name__}); continuing without tracing."
        )
        return False

    logger.info("🔍 LangSmith tracing enabled.")
    return True


def _shorten(text: str, limit: int = 1200) -> str:
    """Keep log payloads compact and readable."""
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated {len(text) - limit} chars]"


def _stringify_payload(payload: Any) -> str:
    """Convert callback payloads to readable text for logging."""
    if payload is None:
        return "None"

    if isinstance(payload, str):
        return _shorten(payload)

    try:
        return _shorten(json.dumps(payload, ensure_ascii=False, default=str, indent=2))
    except Exception:
        return _shorten(str(payload))


class APICallLogger(BaseCallbackHandler):
    """Log model and tool calls while enforcing a minimum delay between model calls."""

    def __init__(
        self,
        min_delay_seconds: float = 0.0,
        *,
        logger_obj=logger,
    ):
        self.min_delay_seconds = max(0.0, float(min_delay_seconds))
        self.logger = logger_obj
        self._lock = threading.Lock()
        self._next_allowed_at = 0.0
        self._call_count = 0
        self._seen_start_runs: set[str] = set()

    def _call_name(self, serialized: dict[str, Any] | None, fallback: str) -> str:
        if not isinstance(serialized, dict):
            return fallback
        return (
            serialized.get("name")
            or serialized.get("id")
            or serialized.get("lc")
            or fallback
        )

    def _throttle(self, call_name: str) -> tuple[int, float]:
        """Sleep until the next model call is allowed."""
        with self._lock:
            now = time.monotonic()
            wait_seconds = max(0.0, self._next_allowed_at - now)

            if wait_seconds > 0:
                self.logger.info(
                    f"⏳ API throttle: waiting {wait_seconds:.2f}s before '{call_name}'"
                )
                time.sleep(wait_seconds)
                now = time.monotonic()

            self._call_count += 1
            call_id = self._call_count
            self._next_allowed_at = now + self.min_delay_seconds
            return call_id, wait_seconds

    def _should_log_start(self, kwargs: dict[str, Any]) -> bool:
        run_id = kwargs.get("run_id")
        if run_id is None:
            return True

        run_key = str(run_id)
        with self._lock:
            if run_key in self._seen_start_runs:
                return False
            self._seen_start_runs.add(run_key)
            return True

    def on_chat_model_start(self, serialized, messages, **kwargs):
        if not self._should_log_start(kwargs):
            return
        call_name = self._call_name(serialized, "chat-model")
        call_id, wait_seconds = self._throttle(call_name)
        self.logger.info(
            f"🤖 LLM START #{call_id}: {call_name} | wait={wait_seconds:.2f}s | "
            f"input={_stringify_payload(messages)}"
        )

    def on_llm_start(self, serialized, prompts, **kwargs):
        if not self._should_log_start(kwargs):
            return
        call_name = self._call_name(serialized, "llm")
        call_id, wait_seconds = self._throttle(call_name)
        self.logger.info(
            f"🤖 LLM START #{call_id}: {call_name} | wait={wait_seconds:.2f}s | "
            f"input={_stringify_payload(prompts)}"
        )

    def on_llm_end(self, response, **kwargs):
        run_id = kwargs.get("run_id")
        if run_id is not None:
            with self._lock:
                self._seen_start_runs.discard(str(run_id))
        self.logger.info(f"✅ LLM END | output={_stringify_payload(response)}")

    def on_llm_error(self, error, **kwargs):
        run_id = kwargs.get("run_id")
        if run_id is not None:
            with self._lock:
                self._seen_start_runs.discard(str(run_id))
        self.logger.error(f"❌ LLM ERROR: {error}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = self._call_name(serialized, kwargs.get("name", "tool"))
        self.logger.info(
            f"🛠️ TOOL START: {tool_name} | input={_stringify_payload(input_str)}"
        )

    def on_tool_end(self, output, **kwargs):
        tool_name = kwargs.get("name", "tool")
        self.logger.info(
            f"✅ TOOL END: {tool_name} | output={_stringify_payload(output)}"
        )

    def on_tool_error(self, error, **kwargs):
        tool_name = kwargs.get("name", "tool")
        self.logger.error(f"❌ TOOL ERROR: {tool_name} | error={error}")


def create_runtime_callback_handler(min_delay_seconds: float = 0.0) -> APICallLogger:
    return APICallLogger(min_delay_seconds=min_delay_seconds)


def create_runtime_config(min_delay_seconds: float = 0.0) -> dict[str, Any]:
    """Return a runnable config that logs API activity and enforces throttle."""
    return {"callbacks": [create_runtime_callback_handler(min_delay_seconds)]}
