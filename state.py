from typing import Annotated, Optional, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # The messages in the conversation
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # The next worker to transition to
    next: str
    # Shared data across nodes
    data: dict
    # Error tracking and self-correction
    retry_count: int
    last_error: Optional[str]
