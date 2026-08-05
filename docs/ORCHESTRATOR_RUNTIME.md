# Enterprise Orchestrator Runtime

**Sprint:** 29.8  
**Package:** `src/web/src/runtime/orchestrator`  
**Policy:** Additive coordination only — does **not** replace existing runtimes.

## Purpose

Central orchestration layer that registers, orders, health-checks, schedules, and routes events across Enterprise Runtimes already implemented (Business Network → … → Intelligence).

## Components

| Module | Role |
|--------|------|
| `EnterpriseOrchestrator` | Facade |
| `RuntimeRegistry` | Runtime self-registration |
| `RuntimeDependencyGraph` | Read-only DAG · cycle detection · topological order |
| `RuntimeHealth` | Per-runtime + platform health |
| `RuntimeScheduler` | startup/shutdown/reload/rebuild/warm_cache/refresh/sync |
| `RuntimeDispatcher` | Dispatch orchestration intents |
| `WorkflowCoordinator` | EventBus → runtime routing (observe + optional refresh) |

## Canonical chain

`Business → Citizen → Assets → Life → Spatial → Visualization → Interaction → Intelligence`

(+ Workflow / Automation as foundational services)

## UI / API

- Dashboard: `/orchestrator`
- REST: `/api/enterprise-orchestrator/v1`
- EventBus: `orchestrator_runtime_update`
