# Built-in platform agents — capability stubs, no business logic.

from __future__ import annotations

from platform_orchestrator.base_agent import BaseAgent
from platform_orchestrator.models import AgentContext, TaskRequest, TaskResult, TaskStatus


class _StubAgent(BaseAgent):
    """Minimal agent that acknowledges tasks without domain logic."""

    async def execute(self, task: TaskRequest) -> TaskResult:
        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            capability=task.capability,
            status=TaskStatus.COMPLETED,
            output={
                "agent_id": self.agent_id,
                "capability": task.capability,
                "acknowledged": True,
                "payload_keys": list(task.payload.keys()),
            },
        )


class AutoAgent(_StubAgent):
    agent_id = "auto_agent"
    name = "Auto Agent"
    description = "Automotive vertical — vehicle sales, VIN, procurement"
    capabilities = ["buy_car", "sell_car", "vin_lookup", "vehicle_inspection", "auto_financing"]
    priority = 100
    version = "1.0.0"


class AgroAgent(_StubAgent):
    agent_id = "agro_agent"
    name = "Agro Agent"
    description = "Agricultural trading — grain, freight, crop analytics"
    capabilities = ["grain_trade", "crop_analysis", "freight_quote", "agro_contract", "harvest_forecast"]
    priority = 90
    version = "1.0.0"


class LegalAgent(_StubAgent):
    agent_id = "legal_agent"
    name = "Legal Agent"
    description = "Legal vertical — contracts, compliance, document review"
    capabilities = ["legal_contract", "compliance_check", "document_review", "legal_advice", "dispute_resolution"]
    priority = 95
    version = "1.0.0"


class ERPAgent(_StubAgent):
    agent_id = "erp_agent"
    name = "ERP Agent"
    description = "Enterprise resource planning — analytics, inventory, finance"
    capabilities = ["market_analysis", "inventory_report", "financial_summary", "erp_sync", "supply_chain"]
    priority = 85
    version = "1.0.0"


class PortAgent(_StubAgent):
    agent_id = "port_agent"
    name = "Port Agent"
    description = "Logistics and port operations — shipping, tracking, customs"
    capabilities = ["shipment_tracking", "customs_clearance", "port_schedule", "cargo_manifest", "logistics_route"]
    priority = 80
    version = "1.0.0"


class MarketplaceAgent(_StubAgent):
    agent_id = "marketplace_agent"
    name = "Marketplace Agent"
    description = "Marketplace operations — listings, orders, pricing"
    capabilities = ["create_listing", "order_management", "price_analysis", "marketplace_search", "seller_onboarding"]
    priority = 75
    version = "1.0.0"


class CafeAgent(_StubAgent):
    agent_id = "cafe_agent"
    name = "Cafe Agent"
    description = "Cafe vertical — menu, orders, reservations"
    capabilities = ["menu_management", "cafe_order", "reservation", "inventory_cafe", "loyalty_program"]
    priority = 70
    version = "1.0.0"


class BeautyAgent(_StubAgent):
    agent_id = "beauty_agent"
    name = "Beauty Agent"
    description = "Beauty and wellness — appointments, services, catalog"
    capabilities = ["book_appointment", "service_catalog", "beauty_consultation", "salon_schedule", "product_recommendation"]
    priority = 65
    version = "1.0.0"


BUILTIN_AGENTS: list[type[BaseAgent]] = [
    AutoAgent,
    AgroAgent,
    LegalAgent,
    ERPAgent,
    PortAgent,
    MarketplaceAgent,
    CafeAgent,
    BeautyAgent,
]


def register_builtin_agents(registry) -> None:
    """Register all built-in vertical agents."""
    for agent_cls in BUILTIN_AGENTS:
        registry.register(agent_cls)


__all__ = [
    "AgroAgent",
    "AutoAgent",
    "BeautyAgent",
    "BUILTIN_AGENTS",
    "CafeAgent",
    "ERPAgent",
    "LegalAgent",
    "MarketplaceAgent",
    "PortAgent",
    "register_builtin_agents",
]
