# Hierarchical Agent Orchestration

A multi-agent system built with **LangGraph** that follows a supervisor-worker pattern. This project demonstrates how to coordinate multiple specialized agents to perform research and writing tasks autonomously.

## Architecture

The system uses a **Hierarchical Orchestration** pattern:
1.  **Supervisor**: Acts as a manager, receiving tasks and routing them to specialized workers.
2.  **Researcher**: Uses DuckDuckGo Search to find relevant information.
3.  **Writer**: Processes findings and synthesizes them into a clear, professional summary.

The workflow is cyclic: Supervisor → Worker → Supervisor. This ensures the manager can review worker output before proceeding or finishing.

## Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/sangsik-yang/agents-orchestration.git
    cd agents-orchestration
    ```
2.  Install dependencies:
    ```bash
    uv sync
    # or
    pip install -r requirements.txt
    ```
3.  Set up environment variables:
    Create a `.env` file and add your OpenAI API key:
    ```env
    OPENAI_API_KEY=your_api_key_here
    ```

### Usage
Run the main script to see the orchestration in action:
```bash
python main.py
```
The default task is to research AI breakthroughs of 2024 and write a summary.

## Project Structure
- `main.py`: Graph construction and execution logic.
- `state.py`: Shared state definition.
- `agents/`: Implementation of Supervisor, Researcher, and Writer.
- `STATUS.md`: Current development status and roadmap.

## Technologies Used
- **LangGraph**: For managing complex agent workflows.
- **LangChain**: For LLM integration and tool calling.
- **OpenAI GPT-4o**: The primary model powering the agents.
- **DuckDuckGo Search**: For real-time information gathering.
- **uv**: For modern Python package management.
