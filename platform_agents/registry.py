# AgentRegistry — central registry for all platform AI agents.

from __future__ import annotations

import logging
from typing import Type

from platform_agents.base_agent import BaseAgent
from platform_agents.exceptions import AgentAlreadyRegisteredError, AgentNotFoundError
from platform_agents.models import AgentMetadata
from platform_agents.validation import validate_metadata

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Register, discover, enable, and disable platform agents."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._classes: dict[str, Type[BaseAgent]] = {}
        self._metadata: dict[str, AgentMetadata] = {}
        self._enabled: dict[str, bool] = {}

    def reset(self) -> None:
        self._agents.clear()
        self._classes.clear()
        self._metadata.clear()
        self._enabled.clear()

    def register(self, agent: BaseAgent | Type[BaseAgent], *, source: str = "builtin") -> AgentMetadata:
        if isinstance(agent, type):
            instance: BaseAgent = agent()
            agent_cls = agent
        else:
            instance = agent
            agent_cls = type(agent)

        meta = instance.metadata()
        if source != "builtin":
            meta = AgentMetadata(
                id=meta.id,
                name=meta.name,
                description=meta.description,
                version=meta.version,
                author=meta.author,
                capabilities=list(meta.capabilities),
                priority=meta.priority,
                enabled=meta.enabled,
                source=source,
            )

        validate_metadata(meta)

        if meta.id in self._agents:
            raise AgentAlreadyRegisteredError(meta.id)

        self._agents[meta.id] = instance
        self._classes[meta.id] = agent_cls
        self._metadata[meta.id] = meta
        self._enabled[meta.id] = meta.enabled
        logger.info("agent_registered id=%s source=%s capabilities=%s", meta.id, source, meta.capabilities)
        return meta

    def unregister(self, agent_id: str) -> None:
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        self._agents.pop(agent_id, None)
        self._classes.pop(agent_id, None)
        self._metadata.pop(agent_id, None)
        self._enabled.pop(agent_id, None)
        logger.info("agent_unregistered id=%s", agent_id)

    def get(self, agent_id: str) -> BaseAgent:
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        return self._agents[agent_id]

    def find_by_capability(self, capability: str) -> list[AgentMetadata]:
        matches: list[tuple[int, AgentMetadata]] = []
        for meta in self._metadata.values():
            if not self._enabled.get(meta.id, False):
                continue
            if capability in meta.capabilities:
                matches.append((meta.priority, meta))
        matches.sort(key=lambda x: x[0], reverse=True)
        return [meta for _, meta in matches]

    def list_agents(self, *, include_disabled: bool = True) -> list[AgentMetadata]:
        if include_disabled:
            return list(self._metadata.values())
        return [m for m in self._metadata.values() if self._enabled.get(m.id, False)]

    def enable(self, agent_id: str) -> AgentMetadata:
        meta = self._get_metadata(agent_id)
        self._enabled[agent_id] = True
        updated = AgentMetadata(**{**meta.to_dict(), "enabled": True})
        self._metadata[agent_id] = updated
        logger.info("agent_enabled id=%s", agent_id)
        return updated

    def disable(self, agent_id: str) -> AgentMetadata:
        meta = self._get_metadata(agent_id)
        self._enabled[agent_id] = False
        updated = AgentMetadata(**{**meta.to_dict(), "enabled": False})
        self._metadata[agent_id] = updated
        logger.info("agent_disabled id=%s", agent_id)
        return updated

    def is_enabled(self, agent_id: str) -> bool:
        return self._enabled.get(agent_id, False)

    def capabilities_index(self) -> dict[str, list[str]]:
        index: dict[str, list[tuple[int, str]]] = {}
        for meta in self._metadata.values():
            if not self._enabled.get(meta.id, False):
                continue
            for cap in meta.capabilities:
                index.setdefault(cap, []).append((meta.priority, meta.id))
        return {
            cap: [agent_id for _, agent_id in sorted(entries, reverse=True)]
            for cap, entries in index.items()
        }

    def summary(self) -> dict:
        caps = self.capabilities_index()
        return {
            "total": len(self._metadata),
            "enabled": sum(1 for e in self._enabled.values() if e),
            "capabilities": {k: len(v) for k, v in caps.items()},
            "sources": {
                "builtin": sum(1 for m in self._metadata.values() if m.source == "builtin"),
                "plugin": sum(1 for m in self._metadata.values() if m.source == "plugin"),
            },
        }

    def _get_metadata(self, agent_id: str) -> AgentMetadata:
        if agent_id not in self._metadata:
            raise AgentNotFoundError(agent_id)
        return self._metadata[agent_id]


agent_registry = AgentRegistry()
