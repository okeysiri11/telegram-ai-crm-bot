# CapabilityRouter — route tasks by capability, not agent name.

from __future__ import annotations

import logging

from platform_orchestrator.agent_registry import AgentRegistry
from platform_orchestrator.config import RoutingPolicy
from platform_orchestrator.exceptions import CapabilityNotRoutableError
from platform_orchestrator.models import RoutingDecision

logger = logging.getLogger(__name__)


class CapabilityRouter:
    """Selects the responsible agent based on registered capabilities."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or AgentRegistry()

    def route(
        self,
        capability: str,
        *,
        policy: RoutingPolicy | None = None,
    ) -> RoutingDecision:
        cap = (policy.capability if policy else capability) or capability
        mapping = self._registry.capabilities()
        candidates = list(mapping.get(cap, []))

        if policy and policy.preferred_agent_id:
            if policy.preferred_agent_id in candidates:
                candidates = [policy.preferred_agent_id] + [
                    c for c in candidates if c != policy.preferred_agent_id
                ]

        if policy and policy.min_priority:
            candidates = [
                agent_id
                for agent_id in candidates
                if self._registry.metadata(agent_id).priority >= policy.min_priority
            ]

        if not candidates:
            raise CapabilityNotRoutableError(cap)

        agent_id = candidates[0]
        meta = self._registry.metadata(agent_id)
        reason = f"capability_match:{cap}:priority={meta.priority}"
        if policy and policy.preferred_agent_id == agent_id:
            reason = f"preferred_agent:{agent_id}"

        decision = RoutingDecision(
            capability=cap,
            agent_id=agent_id,
            agent_name=meta.name,
            priority=meta.priority,
            reason=reason,
            candidates=tuple(candidates),
        )
        logger.debug("routing_decision capability=%s agent=%s", cap, agent_id)
        return decision

    def route_with_fallback(
        self,
        capability: str,
        fallback_capability: str | None = None,
        *,
        policy: RoutingPolicy | None = None,
    ) -> RoutingDecision:
        try:
            return self.route(capability, policy=policy)
        except CapabilityNotRoutableError:
            fb = fallback_capability or (policy.fallback_capability if policy else None)
            if fb and fb != capability:
                return self.route(fb, policy=policy)
            raise


capability_router = CapabilityRouter()
