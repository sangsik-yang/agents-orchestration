# Repository Guidelines

## Project Structure & Module Organization

- `main.py` builds and runs the graph, parses CLI options, and wires the Supervisor/worker nodes.
- `agents/` contains worker implementations: `supervisor.py`, `researcher.py`, `sql_queryer.py`, and `writer.py`.
- `state.py` defines the shared `AgentState`; `logger.py` centralizes console logging.
- `config.py` centralizes OpenRouter and Titanic DB settings.
- `setup_db.py` downloads and loads the Titanic dataset into `titanic.db`.
- `scripts/` contains manual OpenRouter checks.
- `tests/` contains pytest tests. Pytest is configured to collect only `tests/test_*.py`.

## Build, Test, and Development Commands

- `uv sync`: install dependencies from `pyproject.toml` and `uv.lock`.
- `uv run setup_db.py`: create or refresh the local SQLite Titanic database.
- `uv run setup_db.py --csv-url ./data/titanic.csv --db-path ./data/titanic.db --table-name titanic`: load a custom CSV into a chosen SQLite table.
- `uv run main.py`: run the interactive agent CLI.
- `uv run main.py --smoke-test`: run one built-in non-interactive query.
- `uv run main.py --query "Analyze the Titanic dataset."`: run one custom query.
- `uv run pytest -q`: run the automated test suite.
- `uv run python -m scripts.check_openrouter_api`: manually test OpenRouter connectivity.

If sandboxed tooling blocks uv cache access, use `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q`.

## Coding Style & Naming Conventions

Use 4-space indentation and Python type hints for public helpers and graph-facing functions. Keep node functions named by role, for example `researcher_node`, `writer_node`, and `sql_query_node`. Return dictionaries should use `AgentState` keys such as `messages`, `data`, `next`, `retry_count`, and `last_error`.

Avoid broad refactors when changing one agent. Do not commit generated caches such as `__pycache__/` or `*.pyc`.

## Testing Guidelines

The project uses pytest. Add tests under `tests/` using the `test_*.py` pattern. Mock LLM calls and external services; automated tests should not require OpenRouter, DuckDuckGo, LangSmith, or network access. For CLI behavior, follow `tests/test_main.py` and patch `create_llm`, `build_graph`, or node functions.

Run `uv run pytest -q` before opening a PR. Current expected baseline is 14 passing tests.

## Commit & Pull Request Guidelines

Recent commits use short imperative summaries such as `Switch default model to GLM 4.5 Air free` and `update docs and smoke mode`. Keep commit subjects concise and focused on one change.

Pull requests should include a short description, test results, and any required environment changes. Link related issues when available. For behavior changes, mention affected commands such as `--smoke-test`, `--query`, or `setup_db.py`.

## Security & Configuration Tips

Do not commit `.env`, API keys, LangSmith keys, or generated `titanic.db` files unless explicitly intended. Required runtime configuration includes `OPENROUTER_API_KEY`; optional settings include `OPENROUTER_MODEL`, `OPENROUTER_LLM_CALL_DELAY_SECONDS`, `TITANIC_DB_PATH`, `LANGCHAIN_TRACING_V2`, and `LANGCHAIN_API_KEY`.
