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

    class Config:
        env_file = ".env"


load_dotenv(override=True)
settings = Settings()
