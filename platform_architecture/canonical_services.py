# Canonical Platform Services — Sprint 32.3.
# One responsibility = one canonical owner. Adapters remain; new SoR engines are forbidden.

from __future__ import annotations

from typing import Any

# capability → single canonical service (extend existing packages only).
CANONICAL_SERVICES: dict[str, dict[str, Any]] = {
    "deal_pipeline": {
        "canonical": "database.models.deal_pipeline_engine + services.pg_deal_pipeline_engine",
        "path": "database/models/deal_pipeline_engine.py",
        "entry": "services/canonical_deal_pipeline.py",
        "debt": ["TD-47"],
        "legacy_adapters": [
            "database/models/deals.py",
            "database/models/deal.py",
            "database/models/deal_engine_v1.py",
            "database/models/lead_engine.py",
            "database/models/automotive_sales.py",
        ],
    },
    "workflow_engine": {
        "canonical": "platform_workflow",
        "path": "platform_workflow/",
        "debt": ["TD-22", "TD-37", "TD-48"],
        "sprint_ops": "36.2",
        "note": "Sprint 36.2 adds graph runtime/registry/API inside SoR — no second engine package",
        "legacy_adapters": [
            "platform_workflows/",
            "platform_workflow_intelligence/",
            "src/web/src/runtime/workflowRuntime/",
            "src/kernel/workflow/",
        ],
    },
    "knowledge_base": {
        "canonical": "platform_enterprise_knowledge_graph",
        "path": "platform_enterprise_knowledge_graph/",
        "debt": ["TD-49"],
        "legacy_adapters": [
            "applications/enterprise_hub/knowledge/",
            "applications/enterprise_hub/knowledge_platform/",
            "applications/ecosystem/knowledge.py",
            "platform_ai/memory/knowledge_base.py",
        ],
    },
    "ai_runtime_queue": {
        "canonical": "platform_jobs (lane=ai) + src/web enterprise-runtime jobManager",
        "path": "platform_jobs/unified_queue.py",
        "debt": [],
    },
    "ai_runtime": {
        "canonical": "platform_ai",
        "path": "platform_ai/",
        "sprint_ops": "36.3",
        "note": "Sprint 36.3 productizes runtime engine/providers/prompts/tools inside SoR — no platform_ai_runtime package",
        "entry": "platform_ai.service.ai_runtime_service",
        "apis": ["/api/ai-runtime", "/api/llm", "/api/prompts", "/management/v1/ai-runtime"],
        "legacy_adapters": [
            "src/kernel/ (TS mirror)",
            "applications/enterprise_hub/ai_provider_hub/",
        ],
    },
    "context_engine": {
        "canonical": "platform_memory",
        "path": "platform_memory/",
        "sprint_ops": "36.4",
        "note": "Sprint 36.4 productizes Enterprise Context Engine inside SoR — no platform_context package",
        "entry": "platform_memory.service.context_engine_service",
        "apis": ["/api/context", "/api/context-engine", "/management/v1/context"],
        "legacy_adapters": [
            "platform_ai/context_builder.py",
            "platform_enterprise_knowledge_graph/context/",
        ],
    },
    "project_memory": {
        "canonical": "platform_memory",
        "path": "platform_memory/",
        "sprint_ops": "36.5",
        "note": "Sprint 36.5 productizes Project Memory Engine inside SoR — no platform_project_memory package",
        "entry": "platform_memory.project_memory_service.project_memory_service",
        "apis": ["/api/project-memory", "/api/memory", "/management/v1/project-memory"],
        "legacy_adapters": [
            "platform_memory/repositories/project_memory_repository.py",
            "platform_memory/search/memory_search_service.py",
        ],
    },
    "voice_runtime": {
        "canonical": "platform_ai",
        "path": "platform_ai/",
        "sprint_ops": "36.6",
        "note": "Sprint 36.6 productizes Voice Command Center inside SoR — no platform_voice package; Node src/voice remains kernel mirror",
        "entry": "platform_ai.voice_service.voice_runtime_service",
        "apis": ["/api/voice", "/api/voice-runtime", "/management/v1/voice"],
        "legacy_adapters": [
            "src/voice/",
            "platform_console/src/pages/VoiceCenterPage.tsx",
        ],
    },
    "multi_agent_runtime": {
        "canonical": "platform_orchestrator",
        "path": "platform_orchestrator/",
        "sprint_ops": "36.7",
        "note": "Sprint 36.7 productizes Multi-Agent Runtime inside SoR — no platform_multi_agent package",
        "entry": "platform_orchestrator.multi_agent_service.multi_agent_runtime_service",
        "apis": ["/api/agents", "/api/multi-agent", "/management/v1/agents"],
        "legacy_adapters": [
            "applications/enterprise_hub/ai_os/enterprise_multi_agent.py",
            "src/web/src/runtime/orchestrator/",
        ],
    },
    "skills_sdk": {
        "canonical": "platform_ai",
        "path": "platform_ai/",
        "sprint_ops": "36.8",
        "note": "Sprint 36.8 productizes AI Skills & SDK inside SoR — extends platform_ai.skills",
        "entry": "platform_ai.skills_sdk_service.skills_sdk_service",
        "apis": ["/api/skills", "/api/sdk", "/management/v1/skills"],
        "legacy_adapters": [
            "platform_ai/skills/",
            "platform_ai/skills_router.py",
            "platform_console/src/pages/AiSkillsPage.tsx",
        ],
    },
    "creative_factory": {
        "canonical": "platform_ai",
        "path": "platform_ai/",
        "sprint_ops": "36.9",
        "note": "Sprint 36.9 productizes Creative Factory inside SoR — no platform_creative package; ai-production-studio remains legacy UI adapter",
        "entry": "platform_ai.creative_service.creative_factory_service",
        "apis": ["/api/creative", "/api/campaigns", "/api/media", "/management/v1/creative"],
        "legacy_adapters": [
            "src/web/src/ai-production-studio/",
            "database/models/content_factory_engine.py",
            "database/models/cross_posting_engine.py",
        ],
    },
    "enterprise_city_runtime": {
        "canonical": "platform_orchestrator",
        "path": "platform_orchestrator/",
        "sprint_ops": "37.0",
        "note": "Sprint 37.0 productizes Enterprise City Runtime control plane inside SoR — spatial map remains src/web/src/enterprise-city adapter; no platform_city package",
        "entry": "platform_orchestrator.city_runtime_service.enterprise_city_runtime_service",
        "apis": ["/api/platform", "/api/dashboard", "/api/search", "/management/v1/platform", "/city"],
        "legacy_adapters": [
            "src/web/src/enterprise-city/",
            "src/web/src/enterprise-runtime/",
        ],
    },
    "event_bus": {
        "canonical": "events.event_bus.PlatformEventBus",
        "path": "events/event_bus.py",
        "debt": ["TD-20"],
        "forbidden_new": ["class *EventBus"],
        "policy": "All cross-module communication MUST publish/subscribe via PlatformEventBus",
        "enterprise_control_plane": "platform_enterprise_event_bus",
        "sprint_ops": "36.1",
        "note": "platform_enterprise_event_bus wraps PlatformEventBus — topics/DLQ/replay/API/UI; not a second SoR",
    },
    "event_aggregator": {
        "canonical": "events/handlers + platform_observability (metrics aggregation)",
        "path": "events/handlers/",
        "note": "Aggregators consume PlatformEventBus; they are not second buses",
    },
    "notification_pipeline": {
        "canonical": "platform_communications_hub + services/notification_center.py",
        "path": "platform_communications_hub/",
        "debt": ["TD-53"],
        "queue_lane": "notification",
    },
    "unified_queue": {
        "canonical": "platform_jobs.unified_queue.UnifiedQueueArchitecture",
        "path": "platform_jobs/unified_queue.py",
        "lanes": ["ai", "workflow", "background", "notification", "render"],
        "features": ["retry", "dead_letter"],
    },
    "secret_policy": {
        "canonical": "platform_security.secret_policy + jwt_secrets + ConfigurationCenter",
        "path": "platform_security/secret_policy.py",
        "debt": ["TD-57"],
    },
    "enterprise_metrics": {
        "canonical": "platform_observability.enterprise_metrics",
        "path": "platform_observability/enterprise_metrics.py",
    },
    "enterprise_runtime_web": {
        "canonical": "src/web/src/enterprise-runtime (orchestration hub)",
        "path": "src/web/src/enterprise-runtime/",
        "debt": ["TD-59", "TD-60"],
        "consumes": [
            "aiAgentRuntime",
            "jobManager",
            "productionRuntime",
            "workflowRuntime (adapter)",
        ],
    },
    "security_center": {
        "canonical": "platform_security.security_center.EnterpriseSecurityCenter",
        "path": "platform_security/security_center.py",
        "debt": [],
        "adapters": [
            "ISAM",
            "middleware/security_middleware",
            "prompt_firewall",
        ],
    },
    # --- Sprint 34.2A–D foundation (canonical; Sprint 35.0 registered) ---
    "identity_core": {
        "canonical": "platform_identity",
        "path": "platform_identity/",
        "sprint": "34.2A",
        "foundation_locked": "35.1",
        "legacy_adapters": [
            "applications/enterprise_hub/security/",
            "platform_identity/hub_bridge.py",
            "platform_enterprise_identity_center/",
            "applications/ecosystem/identity.py",
        ],
    },
    "platform_registry": {
        "canonical": "platform_registry",
        "path": "platform_registry/",
        "sprint": "34.2B",
        "foundation_locked": "35.1",
        "note": "Menus, navigation, verticals, workspaces — single catalog SoR",
        "legacy_adapters": [
            "src/web/src/platform-registry/menuCatalog.ts (fallback projection)",
            "src/web/src/platform-registry/menuApiBridge.ts (API bridge)",
            "src/web/src/shell/enterprise/shellModuleRegistry.ts (UI projection)",
            "src/web/src/modules/moduleCatalog.ts (UI module metadata projection)",
        ],
    },
    "platform_state": {
        "canonical": "platform_state.PlatformStateService",
        "path": "platform_state/",
        "sprint": "34.2C",
        "foundation_locked": "35.1",
        "note": "Unified cross-client state facade; client runtimes are adapters",
    },
    "sync_engine": {
        "canonical": "platform_state.sync_engine.SyncEngine",
        "path": "platform_state/sync_engine.py",
        "sprint": "34.2C",
        "foundation_locked": "35.1",
        "consumes": ["event_bus", "platform_event_store"],
    },
    "version_engine": {
        "canonical": "platform_state.version_engine.VersionEngine + database.models.mixins.VersionMixin",
        "path": "platform_state/version_engine.py",
        "sprint": "34.2D",
        "foundation_locked": "35.1",
        "debt": [],
        "ha": "warm_start via Event Store replay + optional heads checkpoint",
    },
    "platform_event_store": {
        "canonical": "platform_state.event_store.PlatformEventStore",
        "path": "platform_state/event_store.py",
        "sprint": "34.2D",
        "foundation_locked": "35.1",
        "note": "JSONL default; optional Postgres dual-write via ADOS_EVENT_STORE_BACKEND=postgres",
        "legacy_adapters": [
            "applications/enterprise_hub/event_platform/event_store.py",
            "ecosystem/communication/event_store/",
        ],
    },
    "conflict_resolution_platform": {
        "canonical": "platform_state.conflict_engine.ConflictResolutionEngine",
        "path": "platform_state/conflict_engine.py",
        "sprint": "34.2D",
        "foundation_locked": "35.1",
        "note": "platform_state/conflict.py is a compatibility re-export",
        "separate_domain": ["platform_collaboration.conflict_resolver"],
    },
    "service_discovery": {
        "canonical": "platform_architecture.service_discovery.PlatformServiceDiscovery",
        "path": "platform_architecture/service_discovery.py",
        "sprint": "35.1",
        "note": "Query API over CANONICAL_SERVICES — not a second registry",
    },
    "service_builder": {
        "canonical": "platform_service_builder.ServiceBuilderService",
        "path": "platform_service_builder/",
        "sprint": "36.0",
        "note": (
            "Enterprise Service Builder — install/version/deploy platform services "
            "without modifying composed Core. Not platform_core/ (forbidden)."
        ),
        "consumes": ["event_bus", "platform_registry"],
        "extends": ["platform_architecture.service_constructor_foundation"],
    },
    "enterprise_event_bus": {
        "canonical": "platform_enterprise_event_bus.EnterpriseEventBusService",
        "path": "platform_enterprise_event_bus/",
        "sprint": "36.1",
        "consumes": ["event_bus", "platform_event_store"],
        "note": "Enterprise ops façade — does not replace PlatformEventBus",
    },
}


def list_canonical_services() -> list[dict[str, Any]]:
    return [{"service": k, **v} for k, v in CANONICAL_SERVICES.items()]


def canonical_for(service: str) -> dict[str, Any] | None:
    meta = CANONICAL_SERVICES.get(service)
    if not meta:
        return None
    return {"service": service, **meta}


def canonical_summary() -> dict[str, Any]:
    return {
        "count": len(CANONICAL_SERVICES),
        "services": list(CANONICAL_SERVICES.keys()),
        "principle": "one_responsibility_one_canonical_service",
        "sprint": "32.3_consolidation",
    }
