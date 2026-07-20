# Agent registry domain models.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentCapability:
    """Named capability exposed by an agent."""

    name: str
    description: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "description": self.description}


@dataclass
class AgentMetadata:
    """Universal agent metadata — required for every registered agent."""

    id: str
    name: str
    description: str
    version: str
    author: str
    capabilities: list[str]
    priority: int = 0
    enabled: bool = True
    source: str = "builtin"  # builtin | plugin

    def capability_objects(self) -> list[AgentCapability]:
        return [AgentCapability(name=c) for c in self.capabilities]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "capabilities": list(self.capabilities),
            "priority": self.priority,
            "enabled": self.enabled,
            "source": self.source,
        }


@dataclass
class AgentExecutionResult:
    agent_id: str
    capability: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
