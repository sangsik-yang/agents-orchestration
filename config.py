import os
from pathlib import Path
from typing import Dict, Optional

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "z-ai/glm-4.5-air:free"
DEFAULT_TITANIC_DB_PATH = "titanic.db"


def get_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing API Key: OPENROUTER_API_KEY must be set in .env")
    return api_key


def get_openrouter_model() -> str:
    return os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)


def get_openrouter_headers() -> Optional[Dict[str, str]]:
    headers: Dict[str, str] = {}

    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    if referer:
        headers["HTTP-Referer"] = referer

    title = os.getenv("OPENROUTER_APP_TITLE")
    if title:
        headers["X-OpenRouter-Title"] = title

    return headers or None


def resolve_llm_delay_seconds(value: Optional[float] = None) -> float:
    if value is not None:
        return max(0.0, value)

    raw_value = os.getenv("OPENROUTER_LLM_CALL_DELAY_SECONDS", "0").strip()
    try:
        return max(0.0, float(raw_value))
    except ValueError as exc:
        raise RuntimeError(
            "OPENROUTER_LLM_CALL_DELAY_SECONDS must be a non-negative number"
        ) from exc


def get_titanic_db_path() -> Path:
    return Path(os.getenv("TITANIC_DB_PATH", DEFAULT_TITANIC_DB_PATH))


def get_titanic_db_uri() -> str:
    return f"sqlite:///{get_titanic_db_path().as_posix()}"
