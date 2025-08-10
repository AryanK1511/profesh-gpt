from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from src.common.logger import logger
from src.common.utils.exceptions import DatabaseError, ValidationError
from src.common.utils.response import Response as ApiResponse
from src.common.utils.response import Status
from src.modules.auth.dependencies.auth_dependencies import get_current_user
from src.modules.auth.schemas.auth_schemas import CurrentUser
from src.modules.resume.dependencies.resume_dependencies import ResumeServiceDep
from src.modules.resume.schemas.resume_schema import (
    ResumeCreateResponse,
)

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/", response_model=ResumeCreateResponse)
async def upload_resume(
    resume_service: ResumeServiceDep,
    current_user: CurrentUser = Depends(get_current_user),
    file: UploadFile = File(...),
    fileName: str = Form(...),
    agent_id: str = Query(None, description="Optional agent ID for embedding metadata"),
):
    try:
        if file.content_type != "application/pdf":
            raise ValidationError("Only PDF files are allowed")

        file_bytes = await file.read()
        result = await resume_service.upload_resume(
            user_id=current_user.user_id,
            file_name=f"{fileName}.pdf",
            file_bytes=file_bytes,
            agent_id=agent_id,
        )

        return ApiResponse.success(
            data=ResumeCreateResponse(resume=result).model_dump(mode="json"),
            status_code=Status.CREATED,
        )
    except ValidationError as e:
        return ApiResponse.error(message=str(e), status_code=Status.BAD_REQUEST)
    except DatabaseError as e:
        logger.error(f"Database error uploading resume: {e}")
        return ApiResponse.error(
            message=str(e), status_code=Status.INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error uploading resume: {e}")
        return ApiResponse.error(
            message="An unexpected error occurred while uploading the resume",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/{resume_id}")
async def get_resume(
    resume_id: UUID,
    resume_service: ResumeServiceDep,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        file_bytes, filename = await resume_service.get_resume_bytes_for_download(
            resume_id=resume_id, user_id=current_user.user_id
        )

        return Response(
            content=file_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache",
            },
        )

    except ValidationError as e:
        return ApiResponse.error(message=str(e), status_code=Status.NOT_FOUND)
    except DatabaseError as e:
        logger.error(f"Database error downloading resume {resume_id}: {e}")
        return ApiResponse.error(
            message=str(e), status_code=Status.INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error downloading resume {resume_id}: {e}")
        return ApiResponse.error(
            message="An unexpected error occurred while downloading the resume",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    resume_service: ResumeServiceDep,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        deleted = await resume_service.delete_resume(
            resume_id=resume_id, user_id=current_user.user_id
        )

        if not deleted:
            return ApiResponse.error(
                message="Resume not found", status_code=Status.NOT_FOUND
            )

        return Response(status_code=Status.NO_CONTENT)
    except DatabaseError as e:
        logger.error(f"Database error deleting resume: {e}")
        return ApiResponse.error(
            message=str(e), status_code=Status.INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting resume: {e}")
        return ApiResponse.error(
            message="An unexpected error occurred while deleting the resume",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )
