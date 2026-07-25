"""Enterprise Vertical Federation — Sprint 27.3."""

from __future__ import annotations

VERSION = "9.4.0"
API_PREFIX = "/api/verticals/v1"
WEB_PATH = "src/web/vertical-federation"
SPRINT = "27.3"
HUB = "enterprise_vertical_federation"

ARCHITECTURE = (
    "vertical_registry",
    "vertical_executive_ai",
    "cross_vertical_communication",
    "unified_dashboard",
    "vertical_marketplace",
    "knowledge_federation",
)

CORE_VERTICALS = (
    "Auto",
    "Beauty",
    "Medical",
    "Construction",
    "Manufacturing",
    "Agriculture",
    "Real Estate",
    "Logistics",
    "Port",
    "Crypto",
    "Finance",
    "Legal",
    "Education",
    "Retail",
    "Hospitality",
    "Marketplace",
    "Drone",
)

CROSS_VERTICAL_LINKS = (
    ("CRM", "Finance"),
    ("Finance", "ERP"),
    ("ERP", "Logistics"),
    ("Beauty", "CRM"),
    ("Medical", "Analytics"),
    ("Construction", "Marketplace"),
    ("Agro", "Drone"),
    ("Drone", "AI Vision"),
    ("Crypto", "Finance"),
)

MARKETPLACE_ASSET_TYPES = (
    "applications",
    "ai_agents",
    "dashboards",
    "automation",
    "workflows",
    "templates",
    "widgets",
)

KNOWLEDGE_SCOPES = (
    "shared",
    "industry",
    "local",
    "ai_memory",
    "semantic",
)

KPI_TARGETS = {
    "vertical_registry_ready": True,
    "vertical_executive_ai_ready": True,
    "cross_vertical_communication_ready": True,
    "unified_dashboard_ready": True,
    "vertical_marketplace_ready": True,
    "knowledge_federation_ready": True,
}

PRINCIPLES = (
    "single_vertical_registry",
    "per_vertical_ai_director",
    "federated_cross_vertical_bus",
    "unified_ops_visibility",
    "publishable_vertical_assets",
    "federated_knowledge_search",
    "phase4_vertical_federation",
)
