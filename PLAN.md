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
- Added `setup_db.py` CLI options for custom CSV source, DB output path, and table name.
- Added LangSmith startup connectivity fallback and disabled external tracing in tests.
- Added DB preflight and non-zero exit codes for incomplete or failed workflows.
- Switched the default to `openrouter/free` and verified the live Titanic SQL/Writer workflow.
- Added runtime call logging, shared throttling, and a static project dashboard.

## Current Baseline
- Test command: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q`
- Current result: `32 passed` (2026-10-15).
- Known warnings: LangGraph serialization default change and `create_react_agent` deprecation.

## Next Work
1. Handle tracing outages that begin after startup; startup fallback and offline tests are complete.
2. Tighten `process_turn` state handling so manual state updates and LangGraph reducers are clearly separated.
3. Improve SQLQueryer tests with representative intermediate tool-call structures.
4. Consider a lightweight web UI only after the CLI workflow and state model are stable.
