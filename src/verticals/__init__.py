"""Business vertical registry — auto, agro, realty, legal, logistics."""

from __future__ import annotations

from src.verticals.base import VerticalDefinition

VERTICALS: dict[str, VerticalDefinition] = {
    "auto": VerticalDefinition(
        code="auto",
        title="Automotive",
        domain_package="src.domains.automotive",
        legacy_service_prefix="pg_auto",
        maturity="production",
        manager_role="AUTO_MANAGER",
        description="Client/dealer/manager CRM, inventory, VIN, billing.",
        capabilities=(
            "client_requests",
            "dealer_onboarding",
            "inventory",
            "vin",
            "marketing",
            "billing",
            "partner_hub",
        ),
    ),
    "agro": VerticalDefinition(
        code="agro",
        title="Agro",
        domain_package="src.domains.crm",  # agro leads share CRM pipeline
        legacy_service_prefix="pg_lead",
        maturity="partial",
        manager_role="AGRO_MANAGER",
        description="Farmer/supplier leads, deal lifecycle, pipeline boards.",
        capabilities=("lead_ingest", "pipeline_boards", "deal_lifecycle"),
    ),
    "realty": VerticalDefinition(
        code="realty",
        title="Realty",
        domain_package="src.domains.crm",
        legacy_service_prefix="pg_lead",
        maturity="partial",
        manager_role="REALTY_MANAGER",
        description="Rent, buy, sell, new builds, property management.",
        capabilities=("lead_ingest", "client_requests", "photo_upload"),
    ),
    "legal": VerticalDefinition(
        code="legal",
        title="Legal",
        domain_package="src.domains.legal",
        legacy_service_prefix="pg_lead",
        maturity="scaffold",
        manager_role=None,
        description="Legal services hub category and deep-link entry.",
        capabilities=("hub_category", "lead_ingest"),
    ),
    "logistics": VerticalDefinition(
        code="logistics",
        title="Logistics",
        domain_package="src.domains.logistics",
        legacy_service_prefix="pg_lead",
        maturity="scaffold",
        manager_role=None,
        description="Transport and delivery services via auto hub.",
        capabilities=("hub_category", "lead_ingest"),
    ),
}

VERTICAL_CODES = frozenset(VERTICALS)


def get_vertical(code: str) -> VerticalDefinition:
    try:
        return VERTICALS[code]
    except KeyError as exc:
        raise KeyError(f"Unknown vertical: {code}") from exc


def list_verticals(*, maturity: str | None = None) -> list[VerticalDefinition]:
    items = list(VERTICALS.values())
    if maturity is not None:
        items = [v for v in items if v.maturity == maturity]
    return sorted(items, key=lambda v: v.code)
