# Project Status: agents-orchestration

## Current State
The project is a functional prototype of a hierarchical agent orchestration system using LangGraph.

### Implemented Features
- **Hierarchical Graph Structure**: A supervisor-worker pattern where a central manager routes tasks.
- **Supervisor Agent**: Uses structured output (`RouteResponse`) to decide whether to call the `Researcher`, the `Writer`, or `FINISH`.
- **Researcher Agent**: A ReAct-based agent integrated with DuckDuckGo Search for real-time information gathering.
- **Writer Agent**: A ReAct-based agent focused on synthesizing research into final summaries.
- **Environment Management**: Configured for `uv` and `python-dotenv`.

### Project Structure
- `main.py`: Entry point that builds and executes the LangGraph workflow.
- `state.py`: Defines the global `AgentState`.
- `agents/`: Contains specialized agent logic:
  - `supervisor.py`: Task routing and team coordination.
  - `researcher.py`: Search and data gathering tools.
  - `writer.py`: Content creation and summarization.

## Pending / Next Steps
- [ ] Implement robust error handling for API failures.
- [ ] Add more specialized workers (e.g., Code Reviewer, Fact Checker).
- [ ] Enhance shared state management (currently uses `messages` and a `data` dict).
- [ ] Improve prompt engineering for better coordination between agents.
- [ ] Add unit tests for individual agent nodes.

## Environment Requirements
- Python >= 3.11
- OpenAI API Key (set in `.env`)
- Dependencies managed via `uv` or `pip install -r requirements.txt`.
