from typing import Optional
from uuid import UUID

from sqlmodel import Session, select
from src.common.logger import logger
from src.database.storage_bucket.storage_bucket_client import (
    StorageBucketClient,
    storage_bucket_client,
)
from src.modules.resume.models.resume_model import Resume


class ResumeRepository:
    def __init__(
        self, db: Session, storage_client: StorageBucketClient = storage_bucket_client
    ):
        self.db = db
        self.storage_client: StorageBucketClient = storage_client

    def get_resume_by_id(self, resume_id: UUID) -> Optional[Resume]:
        return self.db.exec(select(Resume).where(Resume.resume_id == resume_id)).first()

    def get_resume_by_name_and_user(
        self, filename: str, user_id: str
    ) -> Optional[Resume]:
        return self.db.exec(
            select(Resume).where(Resume.filename == filename, Resume.user_id == user_id)
        ).first()

    def create_resume_record(self, resume_data: dict) -> Resume:
        resume = Resume(**resume_data)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        logger.info(f"Created resume record {resume.resume_id}")
        return resume

    def update_resume_record(
        self, resume_id: UUID, update_data: dict
    ) -> Optional[Resume]:
        resume = self.get_resume_by_id(resume_id)
        if not resume:
            return None
        for key, value in update_data.items():
            if hasattr(resume, key):
                setattr(resume, key, value)
        self.db.commit()
        self.db.refresh(resume)
        logger.info(f"Updated resume record {resume_id}")
        return resume

    def delete_resume_record(self, resume_id: UUID) -> bool:
        resume = self.get_resume_by_id(resume_id)
        if not resume:
            return False
        self.db.delete(resume)
        self.db.commit()
        logger.info(f"Deleted resume record {resume_id}")
        return True

    async def upload_resume_bytes(
        self, *, user_id: str, resume_id: UUID, file_name: str, file_bytes: bytes
    ) -> str:
        storage_path = f"{user_id}/{resume_id}"
        await self.storage_client.upload_bytes_to_path(
            file_bytes=file_bytes,
            storage_path=storage_path,
            content_type="application/pdf",
        )
        return storage_path

    async def delete_resume_file(self, *, storage_path: str) -> None:
        await self.storage_client.delete_pdf(storage_path)
