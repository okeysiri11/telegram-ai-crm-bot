# BaseAgent — every future AI module must inherit from this interface.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from platform_orchestrator.models import (
    AgentContext,
    AgentHealthResult,
    AgentMetadata,
    AgentStatus,
    TaskRequest,
    TaskResult,
)


class BaseAgent(ABC):
    """Provider-independent agent contract — no business logic in the base class."""

    agent_id: ClassVar[str] = ""
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    capabilities: ClassVar[list[str]] = []
    priority: ClassVar[int] = 0
    version: ClassVar[str] = "1.0.0"
    status: ClassVar[AgentStatus] = AgentStatus.ACTIVE

    @classmethod
    def metadata(cls) -> AgentMetadata:
        return AgentMetadata(
            id=cls.agent_id,
            name=cls.name,
            description=cls.description,
            capabilities=tuple(cls.capabilities),
            priority=cls.priority,
            version=cls.version,
            status=cls.status,
        )

    async def initialize(self, context: AgentContext) -> None:
        """Prepare agent with injected context — override when needed."""

    @abstractmethod
    async def execute(self, task: TaskRequest) -> TaskResult:
        """Execute a routed task and return structured output."""

    def validate(self, task: TaskRequest) -> None:
        """Validate task before execution — override for custom rules."""

    async def shutdown(self) -> None:
        """Release resources — override when needed."""

    async def health_check(self) -> AgentHealthResult:
        meta = self.metadata()
        return AgentHealthResult(
            agent_id=meta.id,
            status=meta.status.value,
            healthy=meta.status == AgentStatus.ACTIVE,
            details={"version": meta.version, "capabilities": list(meta.capabilities)},
        )
