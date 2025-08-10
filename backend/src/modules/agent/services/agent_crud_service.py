from typing import Optional
from uuid import UUID

from src.common.logger import logger
from src.common.utils.exceptions import DatabaseError, ValidationError
from src.common.utils.response import Status
from src.modules.agent.repositories.agent_repository import AgentRepository
from src.modules.agent.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentResponse,
    AgentStatus,
)
from src.modules.resume.repositories.resume_repository import ResumeRepository


class AgentCRUDService:
    def __init__(
        self, repository: AgentRepository, resume_repository: ResumeRepository
    ):
        self.repository = repository
        self.resume_repository = resume_repository

    def validate_agent_creation(
        self, request: AgentCreateRequest, user_id: str
    ) -> dict:
        try:
            try:
                resume_uuid = UUID(request.resume_id)
            except ValueError:
                return {
                    "is_valid": False,
                    "error": "Invalid resume ID format",
                    "status_code": Status.BAD_REQUEST,
                }

            resume = self.resume_repository.get_resume_by_id(resume_uuid)
            if not resume:
                return {
                    "is_valid": False,
                    "error": "Resume not found",
                    "status_code": Status.NOT_FOUND,
                }

            if resume.user_id != user_id:
                return {
                    "is_valid": False,
                    "error": "Resume does not belong to the user",
                    "status_code": Status.FORBIDDEN,
                }

            existing_agents = self.repository.get_agents_by_user_id(user_id)
            for agent in existing_agents:
                if agent.name.lower() == request.name.lower():
                    return {
                        "is_valid": False,
                        "error": f"Agent with name '{request.name}' already exists",
                        "status_code": Status.CONFLICT,
                    }

            return {"is_valid": True}

        except Exception as e:
            logger.error(f"Validation error for user {user_id}: {e}")
            return {
                "is_valid": False,
                "error": "Validation failed",
                "status_code": Status.INTERNAL_SERVER_ERROR,
            }

    def create_agent(self, request: AgentCreateRequest, user_id: str) -> AgentResponse:
        try:
            resume_uuid = UUID(request.resume_id)

            agent_data = {
                "user_id": user_id,
                "name": request.name.strip(),
                "description": request.description.strip()
                if request.description
                else None,
                "custom_instructions": request.custom_instructions.strip()
                if request.custom_instructions
                else None,
                "curr_resume_id": resume_uuid,
                "status": AgentStatus.QUEUED,
            }

            agent = self.repository.create_agent(agent_data)
            agent_response = AgentResponse.model_validate(agent)

            logger.info(
                f"Successfully created agent '{agent.name}' for user {user_id} with resume {resume_uuid}"
            )
            return agent_response

        except Exception as e:
            logger.error(f"Failed to create agent for user {user_id}: {e}")
            raise DatabaseError(f"Failed to create agent: {str(e)}")

    def update_agent_task_id(self, agent_id: UUID, user_id: str, task_id: str) -> bool:
        try:
            agent = self.repository.get_agent_by_id(agent_id)
            if not agent:
                return False

            if agent.user_id != user_id:
                logger.warning(
                    f"User {user_id} attempted to update task_id for agent {agent_id} owned by {agent.user_id}"
                )
                return False

            self.repository.update_agent(agent_id, {"task_id": task_id})
            logger.info(f"Updated task_id {task_id} for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update task_id for agent {agent_id}: {e}")
            raise DatabaseError(f"Failed to update task_id: {str(e)}")

    def update_agent_status(self, agent_id: UUID, status: AgentStatus) -> bool:
        try:
            self.repository.update_agent(agent_id, {"status": status})
            logger.info(f"Updated status to {status} for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update status for agent {agent_id}: {e}")
            raise DatabaseError(f"Failed to update agent status: {str(e)}")

    def get_resume_by_id(self, resume_id: UUID):
        try:
            return self.resume_repository.get_resume_by_id(resume_id)
        except Exception as e:
            logger.error(f"Failed to get resume {resume_id}: {e}")
            raise DatabaseError(f"Failed to get resume: {str(e)}")

    def get_agent_by_id(self, agent_id: UUID, user_id: str) -> Optional[AgentResponse]:
        try:
            agent = self.repository.get_agent_by_id(agent_id)

            if not agent:
                return None

            if agent.user_id != user_id:
                logger.warning(
                    f"User {user_id} attempted to access agent {agent_id} owned by {agent.user_id}"
                )
                return None

            return AgentResponse.model_validate(agent)

        except Exception as e:
            logger.error(f"Failed to get agent {agent_id} for user {user_id}: {e}")
            raise DatabaseError(f"Failed to retrieve agent: {str(e)}")

    def get_user_agents(self, user_id: str) -> list[AgentResponse]:
        try:
            agents = self.repository.get_agents_by_user_id(user_id)
            return [AgentResponse.model_validate(agent) for agent in agents]

        except Exception as e:
            logger.error(f"Failed to get agents for user {user_id}: {e}")
            raise DatabaseError(f"Failed to retrieve agents: {str(e)}")

    def update_agent(
        self, agent_id: UUID, user_id: str, update_data: dict
    ) -> Optional[AgentResponse]:
        try:
            agent = self.repository.get_agent_by_id(agent_id)
            if not agent:
                return None

            if agent.user_id != user_id:
                logger.warning(
                    f"User {user_id} attempted to update agent {agent_id} owned by {agent.user_id}"
                )
                return None

            if "name" in update_data and not update_data["name"].strip():
                raise ValidationError("Agent name cannot be empty")

            if "name" in update_data:
                existing_agents = self.repository.get_agents_by_user_id(user_id)
                for existing_agent in existing_agents:
                    if (
                        existing_agent.agent_id != agent_id
                        and existing_agent.name.lower() == update_data["name"].lower()
                    ):
                        raise ValidationError(
                            f"Agent with name '{update_data['name']}' already exists"
                        )

            updated_agent = self.repository.update_agent(agent_id, update_data)
            if updated_agent:
                return AgentResponse.model_validate(updated_agent)

            return None

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} for user {user_id}: {e}")
            raise DatabaseError(f"Failed to update agent: {str(e)}")

    def delete_agent(self, agent_id: UUID, user_id: str) -> bool:
        try:
            agent = self.repository.get_agent_by_id(agent_id)
            if not agent:
                return False

            if agent.user_id != user_id:
                logger.warning(
                    f"User {user_id} attempted to delete agent {agent_id} owned by {agent.user_id}"
                )
                return False

            return self.repository.delete_agent(agent_id)

        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id} for user {user_id}: {e}")
            raise DatabaseError(f"Failed to delete agent: {str(e)}")
