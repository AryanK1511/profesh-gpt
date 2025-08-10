from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeResponse(BaseModel):
    resume_id: UUID
    user_id: str
    filename: str
    filepath: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeCreateResponse(BaseModel):
    resume: ResumeResponse
    message: str = Field(default="Resume uploaded successfully")


class ResumeUpdateResponse(BaseModel):
    resume: ResumeResponse
    message: str = Field(default="Resume updated successfully")
