# Hierarchical Agent Orchestration with LangGraph

This project implements a hierarchical agent orchestration system using [LangGraph](https://github.com/langchain-ai/langgraph).
It features a **Supervisor** agent that coordinates between a **Researcher** and a **Writer** to complete complex tasks.

## Setup

1.  **Environment Variables**:
    - Copy `.env.example` to `.env`.
    - Set your `OPENAI_API_KEY`.

2.  **Installation**:
    This project uses [uv](https://github.com/astral-sh/uv) for dependency management.
    ```bash
    uv sync
    ```

## Running the Project

To run the hierarchical orchestration:
```bash
uv run main.py
```

## Architecture

- **Supervisor**: An LLM-powered router that decides which specialist should work next or if the task is finished.
- **Researcher**: Uses DuckDuckGo search to gather information.
- **Writer**: Synthesizes the gathered information into a final summary.
- **State**: A shared `AgentState` that stores the conversation history and the next agent to be called.
