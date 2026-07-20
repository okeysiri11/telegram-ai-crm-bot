# Built-in demonstration agents.

from __future__ import annotations

from typing import Any

from platform_agents.base_agent import BaseAgent
from platform_agents.models import AgentExecutionResult
from platform_agents.registry import AgentRegistry


class _DemoAgent(BaseAgent):
    """Minimal demonstration agent — acknowledges capabilities without domain logic."""

    async def execute(self, capability: str, payload: dict[str, Any] | None = None) -> AgentExecutionResult:
        self.validate_capability(capability)
        return AgentExecutionResult(
            agent_id=self.agent_id,
            capability=capability,
            success=True,
            output={
                "agent_id": self.agent_id,
                "capability": capability,
                "acknowledged": True,
                "payload_keys": list((payload or {}).keys()),
            },
        )


class AutoAgent(_DemoAgent):
    agent_id = "auto_agent"
    name = "Auto Agent"
    description = "Automotive vertical — vehicle sales, VIN lookup, financing"
    author = "Platform Team"
    version = "1.0.0"
    capabilities = ["buy_car", "sell_car", "vin_lookup", "vehicle_inspection", "auto_financing"]
    priority = 100


class AgroAgent(_DemoAgent):
    agent_id = "agro_agent"
    name = "Agro Agent"
    description = "Agricultural trading — grain, freight, crop analytics"
    author = "Platform Team"
    version = "1.0.0"
    capabilities = ["grain_trade", "crop_analysis", "freight_quote", "agro_contract", "harvest_forecast"]
    priority = 90


class LegalAgent(_DemoAgent):
    agent_id = "legal_agent"
    name = "Legal Agent"
    description = "Legal vertical — contracts, compliance, document review"
    author = "Platform Team"
    version = "1.0.0"
    capabilities = ["legal_contract", "compliance_check", "document_review", "legal_advice"]
    priority = 95


class BeautyAgent(_DemoAgent):
    agent_id = "beauty_agent"
    name = "Beauty Agent"
    description = "Beauty and wellness — appointments, services, catalog"
    author = "Platform Team"
    version = "1.0.0"
    capabilities = ["book_appointment", "service_catalog", "beauty_consultation", "salon_schedule"]
    priority = 65


class MarketplaceAgent(_DemoAgent):
    agent_id = "marketplace_agent"
    name = "Marketplace Agent"
    description = "Marketplace operations — listings, orders, pricing"
    author = "Platform Team"
    version = "1.0.0"
    capabilities = ["create_listing", "order_management", "price_analysis", "marketplace_search"]
    priority = 75


class EngineeringAgent(_DemoAgent):
    agent_id = "engineering_agent"
    name = "Engineering Agent"
    description = "Engineering vertical — design, blueprints, construction planning"
    author = "Platform Team"
    version = "1.0.0"
    capabilities = [
        "engineering_design",
        "blueprint_review",
        "construction_plan",
        "technical_audit",
        "project_estimate",
    ]
    priority = 80


BUILTIN_AGENTS: list[type[BaseAgent]] = [
    AutoAgent,
    AgroAgent,
    LegalAgent,
    BeautyAgent,
    MarketplaceAgent,
    EngineeringAgent,
]


def register_builtin_agents(registry: AgentRegistry) -> None:
    for agent_cls in BUILTIN_AGENTS:
        registry.register(agent_cls, source="builtin")


__all__ = [
    "AgroAgent",
    "AutoAgent",
    "BeautyAgent",
    "BUILTIN_AGENTS",
    "EngineeringAgent",
    "LegalAgent",
    "MarketplaceAgent",
    "register_builtin_agents",
]
