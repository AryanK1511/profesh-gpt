from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.common.logger import logger
from src.common.utils.exceptions import BaseAPIException
from src.common.utils.response import Response, Status


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error in {request.url.path}: {str(exc)}")

    error_details = {
        "type": "ValidationError",
        "errors": exc.errors(),
    }

    return Response.error(
        message="Validation error",
        data={
            "error_code": "VALIDATION_ERROR",
            "details": error_details,
        },
        status_code=Status.UNPROCESSABLE_ENTITY,
    )


async def not_found_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"Route not found: {request.method} {request.url.path}")

    return Response.error(
        message="The requested resource was not found",
        data={
            "error_code": "NOT_FOUND",
            "details": {"path": str(request.url.path), "method": request.method},
        },
        status_code=Status.NOT_FOUND,
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    # Handle 404s specifically
    if exc.status_code == 404:
        return await not_found_exception_handler(request, exc)

    logger.error(f"HTTP Error in {request.url.path}: {str(exc)}")

    error_details = {
        "type": "HTTPException",
        "status_code": exc.status_code,
        "detail": exc.detail,
    }

    return Response.error(
        message=str(exc.detail),
        data={
            "error_code": f"HTTP_{exc.status_code}",
            "details": error_details,
        },
        status_code=exc.status_code,
    )


async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, BaseAPIException):
        logger.error(f"API Error in {request.url.path}: {str(exc)}")
        error_details = exc.details
        status_code = exc.status_code
        error_code = exc.error_code
        message = exc.message
    else:
        logger.error(f"Unexpected Error in {request.url.path}: {str(exc)}")
        error_details = {
            "type": exc.__class__.__name__,
        }
        status_code = Status.INTERNAL_SERVER_ERROR
        error_code = "INTERNAL_SERVER_ERROR"
        message = "An unexpected error occurred"

    return Response.error(
        message=message,
        data={
            "error_code": error_code,
            "details": error_details,
        },
        status_code=status_code,
    )


def register_exception_handlers(app):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
