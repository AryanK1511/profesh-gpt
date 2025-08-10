from src.database.postgres.postgres_client import postgres_client
from src.database.redis.redis_client import redis_client
from src.database.storage_bucket.storage_bucket_client import storage_bucket_client
from src.modules.agent.core.ai_agent import AIAgent
from src.modules.agent.dependencies.agent_dependencies import (
    get_agent_repository,
    get_agent_status_repository,
    get_embedding_repository,
    get_embedding_service,
)
from src.modules.agent.services.agent_crud_service import AgentCRUDService
from src.modules.agent.services.agent_service import AgentService
from src.modules.resume.dependencies.resume_dependencies import get_resume_repository


def create_agent_repository():
    db = next(postgres_client.get_db())
    return get_agent_repository(db)


def create_resume_repository():
    db = next(postgres_client.get_db())
    return get_resume_repository(db, storage_bucket_client)


def create_agent_status_repository():
    return get_agent_status_repository(redis_client)


def create_embedding_repository():
    return get_embedding_repository()


def create_agent_service():
    agent_repo = create_agent_repository()
    resume_repo = create_resume_repository()
    return AgentCRUDService(agent_repo, resume_repo)


def create_agent_processing_service():
    ai_agent = AIAgent()
    status_repo = create_agent_status_repository()
    return AgentService(ai_agent=ai_agent, repository=status_repo)


def create_embedding_service():
    return get_embedding_service()
