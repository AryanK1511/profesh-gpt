from typing import Generator

from sqlmodel import Session, SQLModel, create_engine
from src.common.config import settings
from src.common.logger import logger


class PostgresClient:
    def __init__(self):
        database_url = settings.DATABASE_URL
        logger.info("Using DATABASE_URL for connection")

        self.engine = create_engine(database_url)

    def get_db(self) -> Generator[Session, None, None]:
        with Session(self.engine) as session:
            try:
                yield session
            finally:
                session.close()

    async def init_db(self):
        try:
            SQLModel.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def close(self):
        if hasattr(self, "engine"):
            self.engine.dispose()


postgres_client = PostgresClient()
