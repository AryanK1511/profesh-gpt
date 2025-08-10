from uuid import UUID, uuid4

from src.common.logger import logger
from src.common.utils.exceptions import DatabaseError, ValidationError
from src.modules.resume.repositories.resume_repository import ResumeRepository
from src.modules.resume.schemas.resume_schema import ResumeResponse


class ResumeService:
    def __init__(self, repository: ResumeRepository):
        self.repository = repository

    async def upload_resume(
        self, *, user_id: str, file_name: str, file_bytes: bytes, agent_id: str = None
    ) -> ResumeResponse:
        try:
            if not file_name.lower().endswith(".pdf"):
                raise ValidationError("File must be a PDF")

            existing_resume = self.repository.get_resume_by_name_and_user(
                filename=file_name, user_id=user_id
            )
            if existing_resume:
                raise ValidationError(
                    f"A resume with the name '{file_name}' already exists"
                )

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

    async def delete_resume(self, resume_id: UUID, user_id: str) -> bool:
        try:
            resume = self.repository.get_resume_by_id(resume_id)
            if not resume:
                logger.warning(f"Resume {resume_id} not found for deletion")
                return False

            if resume.user_id != user_id:
                logger.warning(
                    f"User {user_id} attempted to delete resume {resume_id} owned by {resume.user_id}"
                )
                return False

            await self.repository.delete_resume_file(storage_path=resume.filepath)

            success = self.repository.delete_resume_record(resume_id)

            if success:
                logger.info(
                    f"Successfully deleted resume {resume_id} for user {user_id}"
                )
            else:
                logger.error(f"Failed to delete resume record {resume_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id}: {e}")
            return False

    async def get_resume_bytes_for_download(
        self, resume_id: UUID, user_id: str
    ) -> tuple[bytes, str]:
        try:
            resume = self.repository.get_resume_by_id(resume_id)
            if not resume:
                raise ValidationError("Resume not found")

            if resume.user_id != user_id:
                raise ValidationError("Access denied")

            file_bytes = await self.repository.storage_client.download_bytes_from_path(
                resume.filepath
            )

            logger.info(f"Retrieved resume {resume_id} for download by user {user_id}")
            return file_bytes, resume.filename

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get resume {resume_id} for download: {e}")
            raise DatabaseError("Failed to retrieve resume")
