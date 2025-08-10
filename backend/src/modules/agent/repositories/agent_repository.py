from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select
from src.common.logger import logger
from src.modules.agent.models.agent_model import Agent


class AgentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_agent(self, agent_data: dict) -> Agent:
        try:
            agent = Agent(**agent_data)
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
            logger.info(f"Created agent with ID: {agent.agent_id}")
            return agent
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create agent: {e}")
            raise

    def get_agent_by_id(self, agent_id: UUID) -> Optional[Agent]:
        try:
            return self.db.exec(select(Agent).where(Agent.agent_id == agent_id)).first()
        except Exception as e:
            logger.error(f"Failed to get agent by ID {agent_id}: {e}")
            raise

    def get_agents_by_user_id(self, user_id: str) -> List[Agent]:
        try:
            return self.db.exec(select(Agent).where(Agent.user_id == user_id)).all()
        except Exception as e:
            logger.error(f"Failed to get agents for user {user_id}: {e}")
            raise

    def update_agent(self, agent_id: UUID, update_data: dict) -> Optional[Agent]:
        try:
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                return None

            for key, value in update_data.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)

            self.db.commit()
            self.db.refresh(agent)
            logger.info(f"Updated agent with ID: {agent_id}")
            return agent
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise

    def delete_agent(self, agent_id: UUID) -> bool:
        try:
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                return False

            self.db.delete(agent)
            self.db.commit()
            logger.info(f"Deleted agent with ID: {agent_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise
