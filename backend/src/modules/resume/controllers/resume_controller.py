from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlmodel import Session
from src.common.logger import logger
from src.common.utils.exceptions import DatabaseError, ValidationError
from src.common.utils.response import Response, Status
from src.database.postgres.postgres_client import postgres_client
from src.modules.auth.dependencies.auth_dependencies import get_current_user
from src.modules.auth.schemas.auth_schemas import CurrentUser
from src.modules.resume.repositories.resume_repository import ResumeRepository
from src.modules.resume.schemas.resume_schema import (
    ResumeCreateResponse,
    ResumeUpdateResponse,
)
from src.modules.resume.services.resume_service import ResumeService

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/", response_model=ResumeCreateResponse)
async def upload_resume(
    file: UploadFile = File(...),
    fileName: str = Form(...),
    agent_id: str = Query(None, description="Optional agent ID for embedding metadata"),
    db: Session = Depends(postgres_client.get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        if file.content_type != "application/pdf":
            raise ValidationError("Only PDF files are allowed")

        repository = ResumeRepository(db)
        service = ResumeService(repository)
        file_bytes = await file.read()
        result = await service.upload_resume(
            user_id=current_user.user_id,
            file_name=f"{fileName}.pdf",
            file_bytes=file_bytes,
            agent_id=agent_id,
        )

        return Response.success(
            data=ResumeCreateResponse(resume=result).model_dump(mode="json"),
            status_code=Status.CREATED,
        )
    except ValidationError as e:
        return Response.error(message=str(e), status_code=Status.BAD_REQUEST)
    except DatabaseError as e:
        logger.error(f"Database error uploading resume: {e}")
        return Response.error(message=str(e), status_code=Status.INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Unexpected error uploading resume: {e}")
        return Response.error(
            message="An unexpected error occurred while uploading the resume",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.put("/{resume_id}", response_model=ResumeUpdateResponse)
async def update_resume(
    resume_id: UUID,
    file: UploadFile = File(...),
    fileName: str = Form(...),
    agent_id: str = Query(None, description="Optional agent ID for embedding metadata"),
    db: Session = Depends(postgres_client.get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        if file.content_type != "application/pdf":
            raise ValidationError("Only PDF files are allowed")

        repository = ResumeRepository(db)
        service = ResumeService(repository)
        file_bytes = await file.read()
        result = await service.update_resume(
            user_id=current_user.user_id,
            resume_id=resume_id,
            new_file_name=f"{fileName}.pdf",
            new_file_bytes=file_bytes,
            agent_id=agent_id,
        )

        if not result:
            return Response.error(
                message="Resume not found", status_code=Status.NOT_FOUND
            )

        return Response.success(
            data=ResumeUpdateResponse(resume=result).model_dump(mode="json"),
            status_code=Status.OK,
        )
    except ValidationError as e:
        return Response.error(message=str(e), status_code=Status.BAD_REQUEST)
    except DatabaseError as e:
        logger.error(f"Database error updating resume: {e}")
        return Response.error(message=str(e), status_code=Status.INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Unexpected error updating resume: {e}")
        return Response.error(
            message="An unexpected error occurred while updating the resume",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    db: Session = Depends(postgres_client.get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        repository = ResumeRepository(db)
        service = ResumeService(repository)
        deleted = await service.delete_resume(
            resume_id=resume_id, user_id=current_user.user_id
        )

        if not deleted:
            return Response.error(
                message="Resume not found", status_code=Status.NOT_FOUND
            )

        return Response.success(message="Resume deleted", status_code=Status.NO_CONTENT)
    except DatabaseError as e:
        logger.error(f"Database error deleting resume: {e}")
        return Response.error(message=str(e), status_code=Status.INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Unexpected error deleting resume: {e}")
        return Response.error(
            message="An unexpected error occurred while deleting the resume",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )
