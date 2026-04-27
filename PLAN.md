# Project Plan

## Completed
- Added `AGENTS.md` as the repository contributor guide.
- Expanded `.gitignore` for Python caches, virtual environments, local DB files, build outputs, and editor metadata.
- Removed the global Supervisor instance from `main.py`; each graph now receives its own Supervisor runnable.
- Added `config.py` for OpenRouter settings, LLM call delay parsing, and Titanic DB path/URI handling.
- Updated Researcher and SQLQueryer nodes to return new `data` payloads instead of mutating input state directly.
- Moved manual OpenRouter checks into `scripts/`:
  - `uv run python -m scripts.check_openrouter_api`
  - `uv run python -m scripts.check_openrouter_structured_output`
- Added tests for configurable DB paths and worker state immutability.

## Current Baseline
- Test command: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q`
- Current result: `11 passed`
- Known noise: when `LANGCHAIN_TRACING_V2=true`, LangSmith network calls can emit DNS/connection warnings in offline environments.

## Next Work
1. Add an offline/CI guard for LangSmith tracing so tests stay quiet without requiring network access.
2. Tighten `process_turn` state handling so manual state updates and LangGraph reducers are clearly separated.
3. Add CLI options to `setup_db.py` for custom CSV source and DB output path.
4. Improve SQLQueryer tests with representative intermediate tool-call structures.
5. Consider a lightweight web UI only after the CLI workflow and state model are stable.
