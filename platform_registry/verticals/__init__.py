"""Canonical vertical registry — Sprint 34.2B."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerticalDef:
    id: str
    title: str
    icon: str
    description: str
    workspace: str
    default_roles: tuple[str, ...] = ()
    enabled_modules: tuple[str, ...] = ()
    enabled_agents: tuple[str, ...] = ()
    enabled_features: tuple[str, ...] = ()
    web_path: str | None = None
    telegram_entry: str | None = None


VERTICAL_REGISTRY: dict[str, VerticalDef] = {
    "company_core": VerticalDef(
        id="company_core",
        title="Company Core",
        icon="building",
        description="HR, departments, KPI",
        workspace="company_core",
        default_roles=("owner", "administrator", "manager", "employee"),
        enabled_modules=("crm", "erp", "analytics", "tasks", "calendar"),
        enabled_agents=("agent_owner", "agent_manager"),
        enabled_features=("core_hr", "kpi"),
        web_path="/workspace/company-core",
        telegram_entry="company_core",
    ),
    "crypto_otc": VerticalDef(
        id="crypto_otc",
        title="Crypto OTC",
        icon="crypto",
        description="OTC trading vertical",
        workspace="crypto_otc",
        default_roles=("owner", "manager", "dealer", "client"),
        enabled_modules=("crm", "marketplace", "analytics", "finance"),
        enabled_agents=("agent_crypto",),
        enabled_features=("otc", "rates"),
        web_path="/workspace/crypto",
        telegram_entry="crypto",
    ),
    "drone": VerticalDef(
        id="drone",
        title="Drone Engineering",
        icon="drone",
        description="Drone engineering vertical",
        workspace="drone",
        default_roles=("owner", "manager", "operator", "client"),
        enabled_modules=("crm", "projects", "production", "analytics"),
        enabled_agents=("agent_drone",),
        enabled_features=("engineering",),
        web_path="/workspace/drone",
        telegram_entry="drone",
    ),
    "agro": VerticalDef(
        id="agro",
        title="Agro Trading",
        icon="agro",
        description="Agriculture trading",
        workspace="agro",
        default_roles=("owner", "manager", "partner", "client"),
        enabled_modules=("crm", "erp", "marketplace", "analytics"),
        enabled_agents=("agent_agro",),
        enabled_features=("trading", "logistics"),
        web_path="/workspace/agro",
        telegram_entry="agro",
    ),
    "cafe_beauty": VerticalDef(
        id="cafe_beauty",
        title="Cafe & Beauty",
        icon="beauty",
        description="Hospitality and beauty",
        workspace="cafe_beauty",
        default_roles=("owner", "manager", "employee", "client"),
        enabled_modules=("crm", "calendar", "tasks", "marketplace"),
        enabled_agents=("agent_beauty",),
        enabled_features=("booking", "loyalty"),
        web_path="/workspace/cafe",
        telegram_entry="cafe_beauty",
    ),
    "legal": VerticalDef(
        id="legal",
        title="Legal",
        icon="legal",
        description="Legal enterprise",
        workspace="legal",
        default_roles=("owner", "manager", "employee", "client"),
        enabled_modules=("crm", "documents", "knowledge", "tasks"),
        enabled_agents=("agent_legal",),
        enabled_features=("contracts",),
        web_path="/workspace/legal",
        telegram_entry="legal",
    ),
    "auto": VerticalDef(
        id="auto",
        title="Automotive",
        icon="auto",
        description="Auto marketplace and CRM",
        workspace="auto",
        default_roles=("owner", "manager", "dealer", "client"),
        enabled_modules=("crm", "marketplace", "erp", "analytics", "finance"),
        enabled_agents=("agent_auto",),
        enabled_features=("dealer", "vin", "leads"),
        web_path="/workspace/auto",
        telegram_entry="auto_client",
    ),
    "manufacturing": VerticalDef(
        id="manufacturing",
        title="Manufacturing",
        icon="factory",
        description="Manufacturing / production",
        workspace="manufacturing",
        default_roles=("owner", "manager", "operator"),
        enabled_modules=("erp", "production", "analytics", "tasks"),
        enabled_agents=("agent_production",),
        enabled_features=("mrp",),
        web_path="/erp?view=production",
        telegram_entry=None,
    ),
    "construction": VerticalDef(
        id="construction",
        title="Construction",
        icon="construction",
        description="Construction vertical",
        workspace="construction",
        default_roles=("owner", "manager", "operator", "partner"),
        enabled_modules=("crm", "projects", "documents", "analytics"),
        enabled_agents=("agent_construction",),
        enabled_features=("sites",),
        web_path="/workspace/construction",
        telegram_entry=None,
    ),
    "medical": VerticalDef(
        id="medical",
        title="Medical",
        icon="medical",
        description="Medical vertical",
        workspace="medical",
        default_roles=("owner", "manager", "employee", "client"),
        enabled_modules=("crm", "calendar", "documents", "knowledge"),
        enabled_agents=("agent_medical",),
        enabled_features=("clinic",),
        web_path="/workspace/medical",
        telegram_entry=None,
    ),
    "ai_marketplace": VerticalDef(
        id="ai_marketplace",
        title="Future AI Marketplace",
        icon="ai",
        description="AI agent marketplace",
        workspace="ai_marketplace",
        default_roles=("owner", "administrator", "partner", "client"),
        enabled_modules=("marketplace", "ai_studio", "knowledge"),
        enabled_agents=("agent_marketplace",),
        enabled_features=("agent_store",),
        web_path="/marketplace",
        telegram_entry=None,
    ),
}


def all_verticals() -> list[VerticalDef]:
    return list(VERTICAL_REGISTRY.values())


def vertical_by_id(vid: str | None) -> VerticalDef | None:
    if not vid:
        return None
    return VERTICAL_REGISTRY.get(str(vid).strip().lower())
