# Platform Core service inventory — Sprint 32.2.
# Canonical ownership map. No second Platform Core package.

from __future__ import annotations

from typing import Any

# Capability → canonical owner (extend existing; do not invent parallel engines).
CORE_SERVICE_OWNERS: dict[str, dict[str, Any]] = {
    "event_bus": {
        "canonical": "events.event_bus.PlatformEventBus",
        "path": "events/event_bus.py",
        "debt": ["TD-20"],
        "forbidden_new": ["*EventBus"],
    },
    "workflow_runtime": {
        "canonical": "platform_workflow",
        "path": "platform_workflow/",
        "adapter": "services/workflow_engine.py",
        "debt": ["TD-22", "TD-37", "TD-48"],
    },
    "notification_service": {
        "canonical": "platform_communications_hub + services/notification_center.py",
        "path": "platform_communications_hub/",
        "debt": ["TD-53"],
        "vertical_adapters": ["applications/auto_marketplace/notifications/"],
    },
    "search_service": {
        "canonical": "services/search_service.py",
        "path": "services/search_service.py",
        "debt": [],
        "note": "Thin helper today; vector search not Core yet",
        "vertical_adapters": ["applications/auto_marketplace/search/"],
    },
    "permission_engine": {
        "canonical": "platform_security.permission_engine",
        "path": "platform_security/permission_engine/",
        "also": "services/permissions.py",
        "debt": ["TD-52"],
    },
    "catalog_engine": {
        "canonical": "marketplace / business_ecosystem catalogs",
        "path": "applications/platform_builder/business_ecosystem/catalogs.py",
        "debt": [],
        "note": "ServiceListing / USC foundation documents ownership",
    },
    "pricing_foundation": {
        "canonical": "services.pricing_engine.PricingEngine",
        "path": "services/pricing_engine.py",
        "also": ["services/pg_pricing_engine.py", "repositories/pricing_repository.py"],
        "debt": ["TD-61"],
        "vertical_adapters": ["applications/auto_marketplace/pricing/"],
    },
    "identity": {
        "canonical": "platform_identity",
        "path": "platform_identity/",
        "vertical_adapters": ["applications/auto_marketplace/authentication/"],
    },
    "ai_provider_hub": {
        "canonical": "platform_enterprise_ai_provider_hub",
        "path": "platform_enterprise_ai_provider_hub/",
    },
    "agent_runtime_web": {
        "canonical": "src/web/src/enterprise-runtime (aiAgentRuntime + agentOs + jobManager)",
        "path": "src/web/src/enterprise-runtime/",
        "debt": ["TD-59", "TD-60"],
    },
    "deal_pipeline": {
        "canonical": "database.models.deal_pipeline_engine + pg_deal_pipeline_engine",
        "path": "database/models/deal_pipeline_engine.py",
        "entry": "services/canonical_deal_pipeline.py",
        "debt": ["TD-47"],
    },
    "knowledge_base": {
        "canonical": "platform_enterprise_knowledge_graph",
        "path": "platform_enterprise_knowledge_graph/",
        "debt": ["TD-49"],
    },
    "unified_queue": {
        "canonical": "platform_jobs.unified_queue.UnifiedQueueArchitecture",
        "path": "platform_jobs/unified_queue.py",
        "lanes": ["ai", "workflow", "background", "notification", "render"],
    },
    "enterprise_metrics": {
        "canonical": "platform_observability.enterprise_metrics",
        "path": "platform_observability/enterprise_metrics.py",
    },
    "secret_policy": {
        "canonical": "platform_security.secret_policy",
        "path": "platform_security/secret_policy.py",
        "debt": ["TD-57"],
    },
    "security_center": {
        "canonical": "platform_security.security_center.EnterpriseSecurityCenter",
        "path": "platform_security/security_center.py",
        "zero_trust": "platform_security/zero_trust/",
        "adapters": [
            "applications/enterprise_hub/security (ISAM)",
            "middleware/security_middleware.py",
            "applications/enterprise_hub/ai_provider_hub/prompt_firewall.py",
        ],
        "forbidden": ["security SoR inside applications/* verticals"],
    },
}

# Auto must not own platform logic — adapters only.
AUTO_PLATFORM_BOUNDARY = {
    "application": "applications/auto_marketplace",
    "allowed": ["bridges", "vertical domain", "vehicle catalog UX"],
    "forbidden": [
        "second event bus",
        "second permission engine",
        "second notification center as SoR",
        "second pricing engine as SoR",
        "second security center / zero-trust engine as SoR",
    ],
    "bridge": "applications/auto_marketplace/integrations/platform_bridge.py",
}


def list_core_services() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, meta in CORE_SERVICE_OWNERS.items():
        rows.append({"service": key, **meta})
    return rows


def owner_for(service: str) -> dict[str, Any] | None:
    meta = CORE_SERVICE_OWNERS.get(service)
    if not meta:
        return None
    return {"service": service, **meta}


def inventory_summary() -> dict[str, Any]:
    return {
        "core_services": len(CORE_SERVICE_OWNERS),
        "services": list(CORE_SERVICE_OWNERS.keys()),
        "auto_boundary": AUTO_PLATFORM_BOUNDARY,
        "platform_core_package": None,
        "composed_core": True,
        "principle": "extend_existing_no_second_core",
    }
