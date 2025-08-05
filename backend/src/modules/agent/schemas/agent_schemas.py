from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    TOOL_CALL = "tool_call"
    TOOL_OUTPUT = "tool_output"
    LLM_OUTPUT = "llm_output"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"


class AgentEvent(BaseModel):
    event_type: EventType
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = {}
    message: Optional[str] = None


class ToolCallEvent(AgentEvent):
    event_type: EventType = EventType.TOOL_CALL
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = {}


class ToolOutputEvent(AgentEvent):
    event_type: EventType = EventType.TOOL_OUTPUT
    tool_name: str
    output: Any


class LLMOutputEvent(AgentEvent):
    event_type: EventType = EventType.LLM_OUTPUT
    content: str
    is_complete: bool = False


class AgentCompleteEvent(AgentEvent):
    event_type: EventType = EventType.AGENT_COMPLETE
    final_output: str


class AgentErrorEvent(AgentEvent):
    event_type: EventType = EventType.AGENT_ERROR
    error_message: str
    error_type: str


class AgentRunRequest(BaseModel):
    input_text: str = "Hello"


class AgentRunResponse(BaseModel):
    run_id: str
    status: str
    message: Optional[str] = None
