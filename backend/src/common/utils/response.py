from typing import Any, Optional

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    status: bool = Field(..., description="Indicates success (true) or failure (false)")
    message: Optional[str] = Field(
        None, description="A descriptive message about the response"
    )
    data: Optional[Any] = Field(
        None, description="The payload data for success responses"
    )


class Response:
    @staticmethod
    def success(
        message: str = "Success",
        data: Optional[Any] = None,
        status_code: int = status.HTTP_200_OK,
    ) -> JSONResponse:
        response = StandardResponse(status=True, message=message, data=data)
        return JSONResponse(status_code=status_code, content=response.model_dump())

    @staticmethod
    def error(
        message: str = "An error occurred",
        data: Optional[Any] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> JSONResponse:
        response = StandardResponse(status=False, message=message, data=data)
        return JSONResponse(status_code=status_code, content=response.model_dump())


class Status:
    OK = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    ACCEPTED = status.HTTP_202_ACCEPTED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    CONFLICT = status.HTTP_409_CONFLICT
    UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
