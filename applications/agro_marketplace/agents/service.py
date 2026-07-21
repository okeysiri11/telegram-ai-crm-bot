# Agro AI agent registry and invocation.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.ai.models import AgentInvocation, AgroAgent, AgroAgentType
from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store

_DEFAULT_AGENTS: list[dict[str, Any]] = [
    {
        "agent_type": AgroAgentType.FARMER_ASSISTANT,
        "name": "Farmer Assistant",
        "description": "Helps farmers with crops, harvests, pricing and listings",
        "skills": ["crop_advice", "harvest", "pricing", "listings"],
    },
    {
        "agent_type": AgroAgentType.BUYER_ASSISTANT,
        "name": "Buyer Assistant",
        "description": "Assists buyers with sourcing, RFQs and negotiations",
        "skills": ["sourcing", "rfq", "negotiation", "quality"],
    },
    {
        "agent_type": AgroAgentType.SUPPLIER_ASSISTANT,
        "name": "Supplier Assistant",
        "description": "Supports suppliers with demand matching and offers",
        "skills": ["demand", "offers", "inventory"],
    },
    {
        "agent_type": AgroAgentType.EXPORTER_ASSISTANT,
        "name": "Exporter Assistant",
        "description": "Guides exporters on compliance, logistics and markets",
        "skills": ["export", "compliance", "logistics"],
    },
    {
        "agent_type": AgroAgentType.MARKETPLACE_MODERATOR,
        "name": "Marketplace Moderator",
        "description": "Moderates listings, matches and trade integrity",
        "skills": ["moderation", "matching", "risk"],
    },
    {
        "agent_type": AgroAgentType.PRICING_ADVISOR,
        "name": "Pricing Advisor",
        "description": "Estimates fair market prices and premiums",
        "skills": ["price_estimation", "forecasting"],
    },
    {
        "agent_type": AgroAgentType.CROP_ADVISOR,
        "name": "Crop Advisor",
        "description": "Provides crop taxonomy and seasonality guidance",
        "skills": ["taxonomy", "seasonality", "yield"],
    },
    {
        "agent_type": AgroAgentType.WAREHOUSE_ADVISOR,
        "name": "Warehouse Advisor",
        "description": "Optimizes storage capacity and lot placement",
        "skills": ["inventory", "capacity", "lots"],
    },
    {
        "agent_type": AgroAgentType.LOGISTICS_ADVISOR,
        "name": "Logistics Advisor",
        "description": "Advises on delivery routing and shipment readiness",
        "skills": ["delivery", "routing", "export"],
    },
    {
        "agent_type": AgroAgentType.EXECUTIVE_AGRO_AI,
        "name": "Executive Agro AI",
        "description": "Executive reporting and opportunity prioritization",
        "skills": ["reporting", "opportunities", "planning"],
    },
]


class AgentRegistry:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store
        self._seeded = False

    def _ensure_seeded(self) -> None:
        if self._seeded and self._store.agro_agents.count() > 0:
            return
        if self._store.agro_agents.count() == 0:
            for spec in _DEFAULT_AGENTS:
                agent = AgroAgent(
                    agent_type=spec["agent_type"],
                    name=spec["name"],
                    description=spec["description"],
                    skills=list(spec["skills"]),
                )
                self._store.agro_agents.save(agent.agent_id, agent)
        self._seeded = True

    def list_agents(self) -> list[AgroAgent]:
        self._ensure_seeded()
        return self._store.agro_agents.list_all()

    def get_by_type(self, agent_type: AgroAgentType | str) -> AgroAgent:
        self._ensure_seeded()
        at = AgroAgentType(agent_type) if isinstance(agent_type, str) else agent_type
        for agent in self.list_agents():
            if agent.agent_type == at and agent.is_active:
                return agent
        raise NotFoundError("AgroAgent", str(at))


class AgroAgentService:
    def __init__(
        self,
        store: AgroStore | None = None,
        registry: AgentRegistry | None = None,
        ecosystem: EcosystemBridge | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self.registry = registry or AgentRegistry(self._store)
        self._ecosystem = ecosystem or ecosystem_bridge
        self._platform = platform or platform_bridge

    def list_agents(self) -> list[AgroAgent]:
        return self.registry.list_agents()

    async def invoke(
        self,
        agent_type: AgroAgentType | str,
        message: str,
        *,
        user_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> AgentInvocation:
        agent = self.registry.get_by_type(agent_type)
        ctx = {"agent": agent.to_dict(), "application": "agro_marketplace", **(context or {})}
        await self._platform.remember_context(f"{agent.agent_type.value}:{user_id or 'anon'}", ctx)
        await self._ecosystem.invoke_workforce(
            f"agro_agent:{agent.agent_type.value}",
            context={"message": message, **ctx},
        )
        assistant = await self._ecosystem.ask_assistant(
            message,
            user_id=user_id or f"agro-{agent.agent_type.value}",
            context=ctx,
        )
        reply = assistant.get("reply") or assistant.get("message") or str(assistant)
        if assistant.get("fallback"):
            reply = (
                f"{agent.name}: I can help with {', '.join(agent.skills)}. "
                f"Regarding '{message[:120]}', review marketplace data and knowledge base for next steps."
            )
        invocation = AgentInvocation(
            agent_type=agent.agent_type,
            user_id=user_id,
            message=message,
            context=ctx,
            reply=reply,
            actions=[{"type": "assistant_invoke", "agent": agent.agent_type.value}],
        )
        return self._store.agent_invocations.save(invocation.invocation_id, invocation)

    def metrics(self) -> dict[str, Any]:
        self.registry._ensure_seeded()
        return {
            "agents": self._store.agro_agents.count(),
            "invocations": self._store.agent_invocations.count(),
        }


agent_service = AgroAgentService()
