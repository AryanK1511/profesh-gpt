from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session
from src.common.logger import logger
from src.common.utils.exceptions import DatabaseError, ValidationError
from src.common.utils.response import Response, Status
from src.database.postgres.postgres_client import postgres_client
from src.modules.agent.repositories.agent_repository import AgentRepository
from src.modules.agent.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentCreateResponse,
    AgentResponse,
)
from src.modules.agent.services.agent_crud_service import AgentCRUDService
from src.modules.auth.dependencies.auth_dependencies import get_current_user
from src.modules.auth.schemas.auth_schemas import CurrentUser

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/", response_model=AgentCreateResponse)
async def create_agent(
    request: AgentCreateRequest,
    db: Session = Depends(postgres_client.get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        repository = AgentRepository(db)
        service = AgentCRUDService(repository)
        logger.info(f"Current user: {current_user}")
        agent = service.create_agent(request, current_user.user_id)

        response_data = AgentCreateResponse(agent=agent)

        return Response.success(
            data=response_data.model_dump(mode="json"),
            status_code=Status.CREATED,
        )

    except ValidationError as e:
        logger.warning(f"Validation error creating agent: {e}")
        return Response.error(
            message=str(e),
            status_code=Status.BAD_REQUEST,
        )

    except DatabaseError as e:
        logger.error(f"Database error creating agent: {e}")
        return Response.error(
            message=str(e),
            status_code=Status.INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        logger.error(f"Unexpected error creating agent: {e}")
        return Response.error(
            message="An unexpected error occurred while creating the agent",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/", response_model=list[AgentResponse])
async def get_user_agents(
    db: Session = Depends(postgres_client.get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        repository = AgentRepository(db)
        service = AgentCRUDService(repository)
        agents = service.get_user_agents(current_user.user_id)

        return Response.success(
            data=[agent.model_dump(mode="json") for agent in agents],
            status_code=Status.OK,
        )

    except DatabaseError as e:
        logger.error(f"Database error getting agents: {e}")
        return Response.error(
            message=str(e),
            status_code=Status.INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        logger.error(f"Unexpected error getting agents: {e}")
        return Response.error(
            message="An unexpected error occurred while retrieving agents",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: Session = Depends(postgres_client.get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        repository = AgentRepository(db)
        service = AgentCRUDService(repository)
        agent = service.get_agent_by_id(agent_id, current_user.user_id)

        if not agent:
            return Response.error(
                message="Agent not found",
                status_code=Status.NOT_FOUND,
            )

        return Response.success(
            data=agent.model_dump(mode="json"),
            status_code=Status.OK,
        )

    except DatabaseError as e:
        logger.error(f"Database error getting agent {agent_id}: {e}")
        return Response.error(
            message=str(e),
            status_code=Status.INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        logger.error(f"Unexpected error getting agent {agent_id}: {e}")
        return Response.error(
            message="An unexpected error occurred while retrieving the agent",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )
