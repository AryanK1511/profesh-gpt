from src.common.config import settings
from src.common.logger import logger
from supabase import Client, create_client


class StorageBucketClient:
    def __init__(self):
        self.supabase: Client = None
        self.bucket_name: str = settings.SUPABASE_STORAGE_BUCKET_NAME
        self._initialize_client()

    def _initialize_client(self):
        try:
            self.supabase = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase storage client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    async def upload_bytes_to_path(
        self,
        file_bytes: bytes,
        storage_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        try:
            self.supabase.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type},
            )

            logger.info(f"Uploaded bytes to path: {storage_path}")
            return storage_path
        except Exception as e:
            logger.error(f"Failed to upload bytes to path {storage_path}: {e}")
            raise

    async def download_bytes_from_path(self, storage_path: str) -> bytes:
        try:
            response = self.supabase.storage.from_(self.bucket_name).download(
                storage_path
            )
            logger.info(f"Downloaded bytes from path: {storage_path}")
            return response
        except Exception as e:
            logger.error(f"Failed to download bytes from path {storage_path}: {e}")
            raise

    async def delete_pdf(self, file_path: str) -> bool:
        try:
            self.supabase.storage.from_(self.bucket_name).remove([file_path])
            logger.info(f"PDF deleted successfully: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete PDF {file_path}: {e}")
            raise


storage_bucket_client = StorageBucketClient()
