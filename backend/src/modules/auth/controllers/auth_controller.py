from fastapi import APIRouter, Depends
from src.common.logger import logger
from src.common.utils.response import Response, Status

from ..dependencies.auth_dependencies import get_current_user
from ..services.auth_service import AuthenticationError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/token")
async def get_token():
    try:
        auth_service = AuthService()
        token_data = auth_service.get_jwt_token()

        return Response.success(
            message="Token generated successfully",
            data=token_data.model_dump(),
            status_code=Status.OK,
        )

    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return Response.error(message=str(e), status_code=Status.UNAUTHORIZED)
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        return Response.error(
            message="Token generation failed", status_code=Status.INTERNAL_SERVER_ERROR
        )


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    try:
        return Response.success(
            message="Profile fetched successfully",
            data=current_user,
            status_code=Status.OK,
        )
    except Exception as e:
        logger.error(f"Profile fetching error: {str(e)}")
        return Response.error(
            message="Profile fetching failed", status_code=Status.INTERNAL_SERVER_ERROR
        )
