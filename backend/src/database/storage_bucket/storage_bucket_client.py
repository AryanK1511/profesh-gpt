import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.common.config import settings
from src.common.logger import logger
from supabase import Client, create_client


class StorageBucketClient:
    def __init__(self):
        self.supabase: Client = None
        self.bucket_name: str = settings.SUPABASE_STORAGE_BUCKET_NAME
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Supabase client."""
        try:
            self.supabase = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase storage client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    def set_bucket(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        logger.info(f"Storage bucket set to: {bucket_name}")

    async def upload_pdf(
        self,
        file_path: str,
        file_name: Optional[str] = None,
        folder_path: str = "pdfs",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            if not file_path.lower().endswith(".pdf"):
                raise ValueError("File must be a PDF")

            if not file_name:
                file_name = os.path.basename(file_path)

            file_id = str(uuid.uuid4())
            file_extension = Path(file_name).suffix
            unique_file_name = f"{file_id}{file_extension}"

            storage_path = f"{folder_path}/{unique_file_name}"

            with open(file_path, "rb") as file:
                result = self.supabase.storage.from_(self.bucket_name).upload(
                    path=storage_path,
                    file=file,
                    file_options={"content-type": "application/pdf"},
                )

            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(
                storage_path
            )

            upload_result = {
                "file_path": storage_path,
                "file_name": file_name,
                "public_url": public_url,
                "file_id": file_id,
                "metadata": metadata or {},
                "size": os.path.getsize(file_path),
            }

            logger.info(f"PDF uploaded successfully: {storage_path}")
            return upload_result

        except Exception as e:
            logger.error(f"Failed to upload PDF {file_path}: {e}")
            raise

    async def upload_pdf_from_bytes(
        self,
        file_bytes: bytes,
        file_name: str,
        folder_path: str = "pdfs",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            # Validate file name has PDF extension
            if not file_name.lower().endswith(".pdf"):
                raise ValueError("File name must have .pdf extension")

            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(file_name).suffix
            unique_file_name = f"{file_id}{file_extension}"

            # Create full storage path
            storage_path = f"{folder_path}/{unique_file_name}"

            # Upload file from bytes
            result = self.supabase.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": "application/pdf"},
            )

            # Get public URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(
                storage_path
            )

            upload_result = {
                "file_path": storage_path,
                "file_name": file_name,
                "public_url": public_url,
                "file_id": file_id,
                "metadata": metadata or {},
                "size": len(file_bytes),
            }

            logger.info(f"PDF uploaded successfully from bytes: {storage_path}")
            return upload_result

        except Exception as e:
            logger.error(f"Failed to upload PDF from bytes: {e}")
            raise

    async def download_pdf(
        self, file_path: str, local_path: Optional[str] = None
    ) -> str:
        try:
            # Generate local path if not provided
            if not local_path:
                file_name = os.path.basename(file_path)
                local_path = f"/tmp/{file_name}"

            # Download file
            response = self.supabase.storage.from_(self.bucket_name).download(file_path)

            # Save to local file
            with open(local_path, "wb") as file:
                file.write(response)

            logger.info(f"PDF downloaded successfully: {file_path} -> {local_path}")
            return local_path

        except Exception as e:
            logger.error(f"Failed to download PDF {file_path}: {e}")
            raise

    async def get_pdf_bytes(self, file_path: str) -> bytes:
        try:
            response = self.supabase.storage.from_(self.bucket_name).download(file_path)
            logger.info(f"PDF bytes retrieved successfully: {file_path}")
            return response

        except Exception as e:
            logger.error(f"Failed to get PDF bytes {file_path}: {e}")
            raise

    async def delete_pdf(self, file_path: str) -> bool:
        try:
            result = self.supabase.storage.from_(self.bucket_name).remove([file_path])
            logger.info(f"PDF deleted successfully: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete PDF {file_path}: {e}")
            raise

    async def list_pdfs(
        self, folder_path: str = "pdfs", limit: int = 100
    ) -> List[Dict[str, Any]]:
        try:
            files = self.supabase.storage.from_(self.bucket_name).list(folder_path)

            # Filter for PDF files
            pdf_files = [
                {
                    "name": file["name"],
                    "path": f"{folder_path}/{file['name']}",
                    "size": file.get("metadata", {}).get("size", 0),
                    "created_at": file.get("created_at"),
                    "updated_at": file.get("updated_at"),
                    "public_url": self.supabase.storage.from_(
                        self.bucket_name
                    ).get_public_url(f"{folder_path}/{file['name']}"),
                }
                for file in files
                if file["name"].lower().endswith(".pdf")
            ]

            # Apply limit
            pdf_files = pdf_files[:limit]

            logger.info(f"Listed {len(pdf_files)} PDF files from {folder_path}")
            return pdf_files

        except Exception as e:
            logger.error(f"Failed to list PDFs in {folder_path}: {e}")
            raise

    async def get_pdf_info(self, file_path: str) -> Dict[str, Any]:
        try:
            # Get file metadata
            files = self.supabase.storage.from_(self.bucket_name).list(
                os.path.dirname(file_path)
            )

            file_name = os.path.basename(file_path)
            file_info = next(
                (file for file in files if file["name"] == file_name), None
            )

            if not file_info:
                raise FileNotFoundError(f"File not found: {file_path}")

            return {
                "name": file_info["name"],
                "path": file_path,
                "size": file_info.get("metadata", {}).get("size", 0),
                "created_at": file_info.get("created_at"),
                "updated_at": file_info.get("updated_at"),
                "public_url": self.supabase.storage.from_(
                    self.bucket_name
                ).get_public_url(file_path),
            }

        except Exception as e:
            logger.error(f"Failed to get PDF info for {file_path}: {e}")
            raise

    async def update_pdf_metadata(
        self, file_path: str, metadata: Dict[str, Any]
    ) -> bool:
        try:
            # Note: Supabase storage doesn't directly support metadata updates
            # This would require re-uploading the file with new metadata
            # For now, we'll log this limitation
            logger.warning(f"Metadata update not directly supported for {file_path}")
            logger.info(f"Metadata to update: {metadata}")
            return True

        except Exception as e:
            logger.error(f"Failed to update metadata for {file_path}: {e}")
            raise

    async def copy_pdf(self, source_path: str, destination_path: str) -> Dict[str, Any]:
        try:
            # Download the source file
            file_bytes = await self.get_pdf_bytes(source_path)

            # Upload to new location
            result = await self.upload_pdf_from_bytes(
                file_bytes=file_bytes,
                file_name=os.path.basename(destination_path),
                folder_path=os.path.dirname(destination_path),
            )

            logger.info(f"PDF copied successfully: {source_path} -> {destination_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to copy PDF {source_path} to {destination_path}: {e}")
            raise

    async def move_pdf(self, source_path: str, destination_path: str) -> bool:
        try:
            # Copy the file
            await self.copy_pdf(source_path, destination_path)

            # Delete the original
            await self.delete_pdf(source_path)

            logger.info(f"PDF moved successfully: {source_path} -> {destination_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to move PDF {source_path} to {destination_path}: {e}")
            raise


# Create a singleton instance
storage_bucket_client = StorageBucketClient()
