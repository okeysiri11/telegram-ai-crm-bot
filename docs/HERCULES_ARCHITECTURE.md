# Hercules Architecture — Epic 1.0

**Package:** `platform_hercules/`  
**Role:** Unified Enterprise Execution Engine for ADOS

## Principle

One runtime for CRM, ERP, AI Studio, verticals (Beauty/Auto/Crypto/…), Telegram, Agents, Desktop.

Hercules **orchestrates**; it does **not** duplicate:
- `platform_jobs` (JobEngine / unified_queue)
- `platform_ai.UnifiedAiPipeline` (generation)
- `platform_orchestrator` (multi-agent)

## Layers

```
Channels (Telegram / Desktop / REST / Agents)
        ↓
HerculesRuntime / Orchestrator
        ↓
Scheduler · Queue · Workers · ResourceManager
        ↓
TaskExecutor / PipelineExecutor
        ↓
platform_ai · platform_jobs · HTTP · Event Bus · Workflow
```

## Package map

| Dir | Responsibility |
|-----|----------------|
| `core/` | Models, ResourceManager |
| `scheduler/` | Priority / delayed / lane dispatch |
| `executor/` | Backends (pipeline, HTTP, telegram, …) |
| `runtime/` | HerculesRuntime, SessionRuntime, UniversalRuntime |
| `queue/` | Logical lanes |
| `workers/` | Worker registry |
| `gpu/` `cpu/` | Pools + detect |
| `memory/` `cache/` | Task memory + multi-domain cache |
| `metrics/` `telemetry/` | Dashboard + health |
| `orchestrator/` | Plan → execute → store |
| `security/` | Rate limit, audit |
| `api/` | `/management/v1/hercules`, `/api/hercules` |

## Domains (UniversalRuntime)

crm, erp, ai_studio, beauty, auto, crypto, agro, drone, construction, production, knowledge, marketplace, telegram, agents, desktop
