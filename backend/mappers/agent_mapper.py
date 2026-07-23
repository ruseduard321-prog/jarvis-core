from backend.mappers.base_mapper import BaseMapper
from backend.models.agent import Agent
from backend.schemas.agent import AgentResponse


class AgentMapper(BaseMapper[Agent, AgentResponse]):
    """Map between database rows, domain models, and response models."""

    @staticmethod
    def from_row(row: dict) -> Agent:
        """Convert a database row into an Agent domain model."""
        return Agent(**row)

    @staticmethod
    def to_response(agent: Agent) -> AgentResponse:
        """Convert an Agent domain model into a response schema."""
        return AgentResponse(**agent.model_dump())
