from typing import Annotated

from fastapi import Depends
from src.common.utils.dependencies import DB, StorageClient
from src.modules.resume.repositories.resume_repository import ResumeRepository
from src.modules.resume.services.resume_service import ResumeService


def get_resume_repository(db: DB, storage_client: StorageClient) -> ResumeRepository:
    return ResumeRepository(db, storage_client)


def get_resume_service(
    resume_repo: Annotated[ResumeRepository, Depends(get_resume_repository)],
) -> ResumeService:
    return ResumeService(resume_repo)


ResumeServiceDep = Annotated[ResumeService, Depends(get_resume_service)]
