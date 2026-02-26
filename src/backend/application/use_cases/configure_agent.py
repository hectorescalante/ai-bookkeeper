"""Use case for configuring agent profile."""

from backend.application.dtos import AgentResponse, ConfigureAgentRequest
from backend.domain.entities.configuration import Agent
from backend.ports.output.repositories import AgentRepository


class ConfigureAgentUseCase:
    """Configure or update agent profile."""

    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    def execute(self, request: ConfigureAgentRequest) -> AgentResponse:
        """Execute the use case."""
        agent = self.agent_repo.get()

        if agent:
            agent.update(
                name=request.name,
                email=request.email,
                phone=request.phone,
            )
        else:
            agent = Agent.create(
                name=request.name,
                email=request.email,
                phone=request.phone,
            )

        self.agent_repo.save(agent)

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            email=agent.email,
            phone=agent.phone,
        )

    def get_agent(self) -> AgentResponse | None:
        """Get current agent profile."""
        agent = self.agent_repo.get()

        if not agent:
            return None

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            email=agent.email,
            phone=agent.phone,
        )
