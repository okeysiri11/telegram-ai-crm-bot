"""AI Agent registry — canonical definitions for all clients."""

from __future__ import annotations

from dataclasses import dataclass

from platform_registry.visibility import DEFAULT_UI_CLIENTS, ClientId


@dataclass(frozen=True)
class AgentDef:
    id: str
    title: str
    vertical: str | None
    role: str
    permissions: tuple[str, ...]
    entry_points: tuple[str, ...]
    available_clients: tuple[str, ...]
    model: str
    tools: tuple[str, ...]
    memory: str
    knowledge_base: str


AGENT_REGISTRY: dict[str, AgentDef] = {
    "agent_owner": AgentDef(
        "agent_owner",
        "Owner AI",
        None,
        "owner",
        ("owner.full_access", "admin.manage"),
        ("/ai-agents", "ai"),
        DEFAULT_UI_CLIENTS + (ClientId.API.value, ClientId.AI.value),
        "platform-default",
        ("govern", "audit", "escalate"),
        "enterprise",
        "platform",
    ),
    "agent_manager": AgentDef(
        "agent_manager",
        "Manager AI",
        None,
        "manager",
        ("crm.read", "crm.write", "agent.execute"),
        ("/ai-agents", "ai"),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("crm", "assign", "summarize"),
        "tenant",
        "crm",
    ),
    "agent_auto": AgentDef(
        "agent_auto",
        "Automotive Agent",
        "auto",
        "manager",
        ("crm.read", "agent.execute"),
        ("/workspace/auto", "🚗 Авто"),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("leads", "vin", "inventory"),
        "vertical",
        "auto",
    ),
    "agent_agro": AgentDef(
        "agent_agro",
        "Agro Agent",
        "agro",
        "manager",
        ("crm.read", "agent.execute"),
        ("/workspace/agro", "🌾 Agro Trading"),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("trading", "logistics"),
        "vertical",
        "agro",
    ),
    "agent_crypto": AgentDef(
        "agent_crypto",
        "Crypto OTC Agent",
        "crypto_otc",
        "dealer",
        ("crm.read", "agent.execute"),
        ("/workspace/crypto", "💱 Crypto OTC"),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("rates", "otc"),
        "vertical",
        "crypto",
    ),
    "agent_drone": AgentDef(
        "agent_drone",
        "Drone Agent",
        "drone",
        "operator",
        ("crm.read", "agent.execute"),
        ("/workspace/drone",),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("engineering",),
        "vertical",
        "drone",
    ),
    "agent_beauty": AgentDef(
        "agent_beauty",
        "Cafe & Beauty Agent",
        "cafe_beauty",
        "employee",
        ("crm.read", "calendar.read", "agent.execute"),
        ("/workspace/cafe",),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("booking",),
        "vertical",
        "beauty",
    ),
    "agent_legal": AgentDef(
        "agent_legal",
        "Legal Agent",
        "legal",
        "employee",
        ("knowledge.read", "agent.execute"),
        ("/workspace/legal",),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("contracts",),
        "vertical",
        "legal",
    ),
    "agent_marketplace": AgentDef(
        "agent_marketplace",
        "Marketplace Agent",
        "ai_marketplace",
        "partner",
        ("crm.read", "agent.execute"),
        ("/marketplace",),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("catalog",),
        "platform",
        "marketplace",
    ),
    "agent_production": AgentDef(
        "agent_production",
        "Production Agent",
        "manufacturing",
        "operator",
        ("erp.read", "studio.generate", "agent.execute"),
        ("/production-studio",),
        DEFAULT_UI_CLIENTS + (ClientId.AI.value,),
        "platform-default",
        ("pipeline",),
        "vertical",
        "production",
    ),
    "agent_construction": AgentDef(
        "agent_construction",
        "Construction Agent",
        "construction",
        "manager",
        ("crm.read", "agent.execute"),
        ("/workspace/construction",),
        (ClientId.WEB.value, ClientId.DESKTOP.value, ClientId.MOBILE.value, ClientId.AI.value),
        "platform-default",
        ("sites",),
        "vertical",
        "construction",
    ),
    "agent_medical": AgentDef(
        "agent_medical",
        "Medical Agent",
        "medical",
        "employee",
        ("crm.read", "calendar.read", "agent.execute"),
        ("/workspace/medical",),
        (ClientId.WEB.value, ClientId.DESKTOP.value, ClientId.MOBILE.value, ClientId.AI.value),
        "platform-default",
        ("clinic",),
        "vertical",
        "medical",
    ),
}


def all_agents() -> list[AgentDef]:
    return list(AGENT_REGISTRY.values())


def agent_by_id(aid: str | None) -> AgentDef | None:
    if not aid:
        return None
    return AGENT_REGISTRY.get(str(aid).strip().lower())
