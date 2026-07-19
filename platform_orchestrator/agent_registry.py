# AgentRegistry — register, discover, and inspect platform agents.

from __future__ import annotations

import logging
from typing import Type

from platform_orchestrator.base_agent import BaseAgent
from platform_orchestrator.exceptions import AgentAlreadyRegisteredError, AgentNotFoundError
from platform_orchestrator.models import AgentHealthResult, AgentMetadata, AgentStatus

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry for all platform agents."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._classes: dict[str, Type[BaseAgent]] = {}
        self._metadata: dict[str, AgentMetadata] = {}

    def reset(self) -> None:
        self._agents.clear()
        self._classes.clear()
        self._metadata.clear()

    def register(self, agent: BaseAgent | Type[BaseAgent]) -> AgentMetadata:
        if isinstance(agent, type):
            instance: BaseAgent = agent()
            agent_cls = agent
        else:
            instance = agent
            agent_cls = type(agent)

        meta = instance.metadata()
        if not meta.id:
            raise ValueError(f"Agent class {agent_cls.__name__} missing agent_id")

        if meta.id in self._agents:
            raise AgentAlreadyRegisteredError(meta.id)

        self._agents[meta.id] = instance
        self._classes[meta.id] = agent_cls
        self._metadata[meta.id] = meta
        logger.info("agent_registered id=%s capabilities=%s", meta.id, meta.capabilities)
        return meta

    def unregister(self, agent_id: str) -> None:
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        self._agents.pop(agent_id, None)
        self._classes.pop(agent_id, None)
        self._metadata.pop(agent_id, None)
        logger.info("agent_unregistered id=%s", agent_id)

    def get(self, agent_id: str) -> BaseAgent:
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        return self._agents[agent_id]

    def list(self) -> list[AgentMetadata]:
        return list(self._metadata.values())

    def capabilities(self) -> dict[str, list[str]]:
        """Map capability → agent ids (sorted by priority descending)."""
        mapping: dict[str, list[tuple[int, str]]] = {}
        for meta in self._metadata.values():
            if meta.status != AgentStatus.ACTIVE:
                continue
            for cap in meta.capabilities:
                mapping.setdefault(cap, []).append((meta.priority, meta.id))

        return {
            cap: [agent_id for _, agent_id in sorted(entries, reverse=True)]
            for cap, entries in mapping.items()
        }

    async def health(self) -> dict[str, AgentHealthResult]:
        results: dict[str, AgentHealthResult] = {}
        for agent_id, agent in self._agents.items():
            results[agent_id] = await agent.health_check()
        return results

    def metadata(self, agent_id: str) -> AgentMetadata:
        if agent_id not in self._metadata:
            raise AgentNotFoundError(agent_id)
        return self._metadata[agent_id]

    def set_status(self, agent_id: str, status: AgentStatus) -> AgentMetadata:
        meta = self.metadata(agent_id)
        updated = AgentMetadata(
            id=meta.id,
            name=meta.name,
            description=meta.description,
            capabilities=meta.capabilities,
            priority=meta.priority,
            version=meta.version,
            status=status,
        )
        self._metadata[agent_id] = updated
        agent_cls = self._classes[agent_id]
        agent_cls.status = status
        return updated

    def summary(self) -> dict:
        caps = self.capabilities()
        return {
            "total": len(self._metadata),
            "active": sum(1 for m in self._metadata.values() if m.status == AgentStatus.ACTIVE),
            "capabilities": {k: len(v) for k, v in caps.items()},
        }


agent_registry = AgentRegistry()
