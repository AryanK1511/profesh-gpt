from typing import Annotated, Generator

from fastapi import Depends
from sqlmodel import Session
from src.database.postgres.postgres_client import postgres_client
from src.database.qdrant.qdrant_client import qdrant_client
from src.database.redis.redis_client import redis_client
from src.database.storage_bucket.storage_bucket_client import storage_bucket_client


def get_db() -> Generator[Session, None, None]:
    with Session(postgres_client.engine) as session:
        try:
            yield session
        finally:
            session.close()


def get_qdrant_client():
    return qdrant_client


def get_redis_client():
    return redis_client


def get_storage_client():
    return storage_bucket_client


DB = Annotated[Session, Depends(get_db)]
QdrantClient = Annotated[type(qdrant_client), Depends(get_qdrant_client)]
RedisClient = Annotated[type(redis_client), Depends(get_redis_client)]
StorageClient = Annotated[type(storage_bucket_client), Depends(get_storage_client)]
