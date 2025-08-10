import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlmodel import Field, SQLModel


class Resume(SQLModel, table=True):
    __tablename__ = "resumes"

    resume_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)
    agent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="agents.agent_id")
    filename: str
    filepath: str
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
        return f"<Resume(resume_id={self.resume_id}, filename='{self.filename}', user_id='{self.user_id}')>"
