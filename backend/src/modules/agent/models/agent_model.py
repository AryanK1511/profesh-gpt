import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlmodel import Field, SQLModel

from ..schemas.agent_schemas import AgentStatus


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    agent_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    name: str
    description: Optional[str] = None
    custom_instructions: Optional[str] = None
    status: AgentStatus = Field(default=AgentStatus.QUEUED, index=True)
    curr_resume_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="resumes.resume_id"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP"),
        },
    )

    def __repr__(self):
        return f"<Agent(agent_id={self.agent_id}, name='{self.name}', user_id='{self.user_id}')>"
