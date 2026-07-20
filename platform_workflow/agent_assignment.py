# Agent assignment — select best agent by capability via Agent Registry.

from __future__ import annotations

import logging

from platform_agents.registry import AgentRegistry, agent_registry
from platform_workflow.exceptions import AgentAssignmentError

logger = logging.getLogger(__name__)


class AgentAssignmentService:
    """Assign tasks to agents by capability with fallback support."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or agent_registry

    def assign(self, capability: str, *, exclude: set[str] | None = None) -> str:
        candidates = self._registry.find_by_capability(capability)
        excluded = exclude or set()

        for meta in candidates:
            if meta.id not in excluded:
                logger.info("agent_assigned capability=%s agent=%s", capability, meta.id)
                return meta.id

        raise AgentAssignmentError(capability, f"No available agent for capability '{capability}'")

    def assign_with_fallback(
        self,
        capability: str,
        fallback_capabilities: list[str] | None = None,
        *,
        exclude: set[str] | None = None,
    ) -> tuple[str, str]:
        """Return (agent_id, resolved_capability)."""
        try:
            return self.assign(capability, exclude=exclude), capability
        except AgentAssignmentError:
            for fb in fallback_capabilities or []:
                try:
                    return self.assign(fb, exclude=exclude), fb
                except AgentAssignmentError:
                    continue
            raise

    def utilization(self) -> dict[str, int]:
        index = self._registry.capabilities_index()
        return {agent_id: sum(1 for ids in index.values() if agent_id in ids) for agent_id in {a.id for a in self._registry.list_agents()}}


agent_assignment_service = AgentAssignmentService()
