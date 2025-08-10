from typing import Annotated

from fastapi import Depends
from src.common.utils.dependencies import DB, RedisClient
from src.modules.agent.repositories.agent_repository import AgentRepository
from src.modules.agent.repositories.agent_status_repository import AgentStatusRepository
from src.modules.agent.repositories.embedding_repository import EmbeddingRepository
from src.modules.agent.services.agent_crud_service import AgentCRUDService
from src.modules.agent.services.embedding_service import EmbeddingService
from src.modules.resume.dependencies.resume_dependencies import get_resume_repository
from src.modules.resume.repositories.resume_repository import ResumeRepository


def get_agent_repository(db: DB) -> AgentRepository:
    return AgentRepository(db)


def get_agent_status_repository(redis_client: RedisClient) -> AgentStatusRepository:
    return AgentStatusRepository(redis_client)


def get_embedding_repository() -> EmbeddingRepository:
    return EmbeddingRepository()


def get_agent_service(
    agent_repo: Annotated[AgentRepository, Depends(get_agent_repository)],
    resume_repo: Annotated[ResumeRepository, Depends(get_resume_repository)],
) -> AgentCRUDService:
    return AgentCRUDService(agent_repo, resume_repo)


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


AgentService = Annotated[AgentCRUDService, Depends(get_agent_service)]
EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]

AgentStatusRepo = Annotated[AgentStatusRepository, Depends(get_agent_status_repository)]
EmbeddingRepo = Annotated[EmbeddingRepository, Depends(get_embedding_repository)]
