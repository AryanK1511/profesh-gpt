from typing import Optional
from uuid import UUID, uuid4

from src.common.logger import logger
from src.common.utils.exceptions import DatabaseError, ValidationError
from src.modules.resume.repositories.resume_repository import ResumeRepository
from src.modules.resume.schemas.resume_schema import ResumeResponse


class ResumeService:
    def __init__(self, repository: ResumeRepository):
        self.repository = repository

    async def upload_resume(
        self, *, user_id: str, file_name: str, file_bytes: bytes
    ) -> ResumeResponse:
        try:
            if not file_name.lower().endswith(".pdf"):
                raise ValidationError("File must be a PDF")

            resume_id = uuid4()

            storage_path = await self.repository.upload_resume_bytes(
                user_id=user_id,
                resume_id=resume_id,
                file_name=file_name,
                file_bytes=file_bytes,
            )

            try:
                resume_record = self.repository.create_resume_record(
                    {
                        "resume_id": resume_id,
                        "user_id": user_id,
                        "filename": file_name,
                        "filepath": storage_path,
                    }
                )
            except Exception as db_error:
                try:
                    await self.repository.delete_resume_file(storage_path=storage_path)
                finally:
                    raise db_error

            logger.info(
                f"Uploaded resume and created record (user_id={user_id}, resume_id={resume_record.resume_id})"
            )
            return ResumeResponse.model_validate(resume_record)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to upload resume for user {user_id}: {e}")
            raise DatabaseError("Failed to upload resume")

    async def update_resume(
        self,
        *,
        user_id: str,
        resume_id: UUID,
        new_file_name: str,
        new_file_bytes: bytes,
    ) -> Optional[ResumeResponse]:
        try:
            if not new_file_name.lower().endswith(".pdf"):
                raise ValidationError("File must be a PDF")

            existing = self.repository.get_resume_by_id(resume_id)
            if not existing or existing.user_id != user_id:
                return None

            new_storage_path = await self.repository.upload_resume_bytes(
                user_id=user_id,
                resume_id=resume_id,
                file_name=new_file_name,
                file_bytes=new_file_bytes,
            )

            # Try DB update; if it fails, remove the newly uploaded file to avoid orphaned storage
            try:
                updated = self.repository.update_resume_record(
                    resume_id,
                    {"filename": new_file_name, "filepath": new_storage_path},
                )
            except Exception as db_error:
                try:
                    await self.repository.delete_resume_file(
                        storage_path=new_storage_path
                    )
                finally:
                    raise db_error

            try:
                await self.repository.delete_resume_file(storage_path=existing.filepath)
            except Exception as e:
                logger.warning(
                    f"Updated DB for resume {resume_id} but failed to delete old file {existing.filepath}: {e}"
                )

            return ResumeResponse.model_validate(updated)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to update resume {resume_id} for user {user_id}: {e}")
            raise DatabaseError("Failed to update resume")

    async def delete_resume(self, *, user_id: str, resume_id: UUID) -> bool:
        try:
            existing = self.repository.get_resume_by_id(resume_id)
            if not existing or existing.user_id != user_id:
                return False

            file_path = existing.filepath
            deleted = self.repository.delete_resume_record(resume_id)
            if not deleted:
                return False

            try:
                await self.repository.delete_resume_file(storage_path=file_path)
            except Exception as e:
                logger.warning(
                    f"Deleted DB record for resume {resume_id} but failed to delete file {file_path}: {e}"
                )

            return True
        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id} for user {user_id}: {e}")
            raise DatabaseError("Failed to delete resume")
