from typing import List, Optional

from pydantic import BaseModel, Field


class AuthenticateResponse(BaseModel):
    token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")


class UserProfile(BaseModel):
    user_id: str = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="User email")
    permissions: List[str] = Field(default_factory=list, description="User permissions")


class TokenRequest(BaseModel):
    email: Optional[str] = Field(
        None, description="User email (optional for test user)"
    )
    password: Optional[str] = Field(
        None, description="User password (optional for test user)"
    )


class TokenValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the token is valid")
    user_id: Optional[str] = Field(None, description="User ID if token is valid")
    error: Optional[str] = Field(None, description="Error message if token is invalid")
