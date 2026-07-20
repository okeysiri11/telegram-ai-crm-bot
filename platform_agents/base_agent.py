# BaseAgent — contract every platform AI agent must implement.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from platform_agents.models import AgentExecutionResult, AgentMetadata


class BaseAgent(ABC):
    """Provider-independent agent interface — no business logic in the base class."""

    agent_id: ClassVar[str] = ""
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Platform"
    capabilities: ClassVar[list[str]] = []
    priority: ClassVar[int] = 0
    enabled: ClassVar[bool] = True

    @classmethod
    def metadata(cls) -> AgentMetadata:
        return AgentMetadata(
            id=cls.agent_id,
            name=cls.name,
            description=cls.description,
            version=cls.version,
            author=cls.author,
            capabilities=list(cls.capabilities),
            priority=cls.priority,
            enabled=cls.enabled,
            source="builtin",
        )

    async def initialize(self, context: dict[str, Any] | None = None) -> None:
        """Prepare agent with injected context."""

    @abstractmethod
    async def execute(self, capability: str, payload: dict[str, Any] | None = None) -> AgentExecutionResult:
        """Execute a capability and return structured output."""

    def validate_capability(self, capability: str) -> None:
        if capability not in self.capabilities:
            from platform_agents.exceptions import AgentValidationError

            raise AgentValidationError(
                f"Agent {self.agent_id} does not support capability '{capability}'"
            )

    async def shutdown(self) -> None:
        """Release resources."""

    async def health_check(self) -> dict[str, Any]:
        meta = self.metadata()
        return {
            "agent_id": meta.id,
            "healthy": meta.enabled,
            "version": meta.version,
            "capabilities": list(meta.capabilities),
        }
