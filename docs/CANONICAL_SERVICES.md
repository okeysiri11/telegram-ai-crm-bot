# Canonical Platform Services

**Sprint:** 32.3 (Enterprise Consolidation track)  
**Collision:** Historical UX track **32.3.1–32.3.7** remains authoritative for entry/Command Center/City/workspace — do not overwrite those docs.

**Executable registry:** `platform_architecture/canonical_services.py`

## Principle

One responsibility = one canonical service. Legacy duplicates stay as **adapters** until migrated; new SoR engines are forbidden.

| Capability | Canonical | Legacy adapters (not SoR) |
|---|---|---|
| Deal Pipelines | `deal_pipeline_engine` + `pg_deal_pipeline_engine` · entry `services/canonical_deal_pipeline.py` | `deals`, `deal`, `deal_engine_v1`, lead/auto sales (TD-47) |
| Workflow Engines | `platform_workflow/` | `platform_workflows`, intelligence, web `workflowRuntime`, TS kernel (TD-22/48) |
| Knowledge Base | `platform_enterprise_knowledge_graph` | hub KG/EKP, ecosystem knowledge, AI memory KB (TD-49) |
| AI Runtime queues | `platform_jobs` lane=`ai` + web `jobManager` | hub `ai_os/task_queue` |
| Event Bus | `events.event_bus.PlatformEventBus` | allowlisted legacy buses (TD-20) |
| Event Aggregators | `events/handlers` + observability | not second buses |
| Notification pipelines | `platform_communications_hub` + `notification_center` | hub/command-center copies, Auto adapters (TD-53) |
| Unified Queue | `platform_jobs.unified_queue` | — |
| Secrets | `secret_policy` + `jwt_secrets` + ConfigurationCenter | — |
| Metrics | `platform_observability.enterprise_metrics` | domain counters |
| Web orchestration | `src/web/src/enterprise-runtime` | other `*Runtime` folders as adapters |
| **Identity Core (34.2A)** | `platform_identity/` | Hub ISAM / Identity Center / ecosystem identity |
| **Platform Registry (34.2B)** | `platform_registry/` | Web menu projections / shell module registry |
| **Platform State (34.2C)** | `platform_state/` | Client `*_runtime` adapters only |
| **Sync Engine (34.2C)** | `platform_state.sync_engine` | — |
| **Version Engine (34.2D / 35.1)** | `platform_state.version_engine` + `VersionMixin` | TD-54 **resolved** |
| **Platform Event Store (34.2D / 35.1)** | `platform_state.event_store` (JSONL · optional Postgres) | Hub/ecosystem EventStores (not SoR) |
| **Conflict (platform)** | `platform_state.conflict_engine` | Collaboration ConflictResolver (separate domain) |
| **Service Discovery (35.1)** | `platform_architecture.service_discovery` | Query over canonical registry only |

**Sprint:** 32.3 consolidation · **Extended:** 34.2A–D · **Stabilized:** 35.0 · **Locked:** 35.1

## Rules

1. Extend the canonical path; never add a parallel engine package.
2. Cross-module effects go through the Event Bus (`docs/EVENT_BUS.md`).
3. Consolidation scan: `python scripts/architecture_consolidation_scan.py`

## Related

[`PLATFORM_CORE.md`](./PLATFORM_CORE.md) · [`QUEUE_ARCHITECTURE.md`](./QUEUE_ARCHITECTURE.md) · [`CORE_SERVICES.md`](./CORE_SERVICES.md)
