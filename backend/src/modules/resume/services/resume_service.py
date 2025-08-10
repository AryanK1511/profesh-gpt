from typing import Optional
from uuid import UUID, uuid4

from src.common.logger import logger
from src.common.utils.exceptions import DatabaseError, ValidationError
from src.modules.agent.services.embedding_service import embedding_service
from src.modules.resume.repositories.resume_repository import ResumeRepository
from src.modules.resume.schemas.resume_schema import ResumeResponse


class ResumeService:
    def __init__(self, repository: ResumeRepository):
        self.repository = repository
        self.embedding_service = embedding_service

    async def upload_resume(
        self, *, user_id: str, file_name: str, file_bytes: bytes, agent_id: str = None
    ) -> ResumeResponse:
        try:
            if not file_name.lower().endswith(".pdf"):
                raise ValidationError("File must be a PDF")

            resume_id = uuid4()

            # Upload file to storage
            storage_path = await self.repository.upload_resume_bytes(
                user_id=user_id,
                resume_id=resume_id,
                file_name=file_name,
                file_bytes=file_bytes,
            )

            try:
                # Create database record
                resume_record = self.repository.create_resume_record(
                    {
                        "resume_id": resume_id,
                        "user_id": user_id,
                        "filename": file_name,
                        "filepath": storage_path,
                    }
                )

                # Delegate embedding to embedding service
                embed_success = await self.embedding_service.embed_resume(
                    user_id=user_id, resume_id=str(resume_id)
                )

                if not embed_success:
                    logger.warning(
                        f"Failed to embed resume {resume_id}, but resume record was created"
                    )

            except Exception as db_error:
                # Cleanup storage if database operation fails
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
        agent_id: str = None,
    ) -> Optional[ResumeResponse]:
        """Update resume file and database record"""
        try:
            if not new_file_name.lower().endswith(".pdf"):
                raise ValidationError("File must be a PDF")

            existing = self.repository.get_resume_by_id(resume_id)
            if not existing or existing.user_id != user_id:
                return None

            # Upload new file to storage
            new_storage_path = await self.repository.upload_resume_bytes(
                user_id=user_id,
                resume_id=resume_id,
                file_name=new_file_name,
                file_bytes=new_file_bytes,
            )

            try:
                # Update database record
                updated = self.repository.update_resume_record(
                    resume_id,
                    {"filename": new_file_name, "filepath": new_storage_path},
                )

                # Delegate re-embedding to embedding service
                embed_success = await self.embedding_service.embed_resume(
                    user_id=user_id, resume_id=str(resume_id)
                )

                if not embed_success:
                    logger.warning(
                        f"Failed to re-embed resume {resume_id} after update"
                    )

            except Exception as db_error:
                # Cleanup new file if database operation fails
                try:
                    await self.repository.delete_resume_file(
                        storage_path=new_storage_path
                    )
                finally:
                    raise db_error

            # Cleanup old file
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

    async def delete_resume(self, resume_id: UUID, user_id: str) -> bool:
        """Delete resume record, file, and embeddings"""
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

            # Delegate embedding deletion to embedding service
            await self.embedding_service.delete_resume_embeddings(resume_id=str(resume_id))

            # Delete file from storage
            await self.repository.delete_resume_file(storage_path=resume.filepath)

            # Delete database record
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
