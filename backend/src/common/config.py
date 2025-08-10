from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from src.common.constants import PROJECT_NAME


class Settings(BaseSettings):
    PROJECT_NAME: str = PROJECT_NAME

    # ========== APP-RELATED ==========
    LOG_LEVEL: str = "INFO"
    PYTHON_ENV: str = "dev"

    # ========== REDIS ==========
    REDIS_URL: str

    # ========== DATABASE ==========
    DATABASE_URL: str

    # ========== OPENAI ==========
    OPENAI_API_KEY: str

    # ========== STORAGE BUCKET ==========
    SUPABASE_STORAGE_BUCKET_NAME: str = "documents"

    # ========== SUPABASE CONFIG ==========
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    # ========== QDRANT ==========
    QDRANT_URL: str
    QDRANT_API_KEY: str = None

    # ========== WORKOS ==========
    WORKOS_API_KEY: str
    WORKOS_CLIENT_ID: str
    WORKOS_JWKS_URL: str
    WORKOS_TESTUSER_EMAIL: str
    WORKOS_TESTUSER_PASSWORD: str

    class Config:
        env_file = ".env"


load_dotenv(override=True)
settings = Settings()
