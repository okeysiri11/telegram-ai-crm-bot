# Platform Architecture

ADOS is a modular Enterprise AI Operating System. This document is the Sprint **37.0** architecture snapshot for the unified platform control plane.

## Layers

```
Customer Applications
        ↑
Vertical Solutions
        ↑
Business Modules (CRM · ERP · Analytics · Knowledge · Creative · …)
        ↑
AI Services (Runtime · Agents · Skills · Voice · Memory · Context · Workflow)
        ↑
Providers (LLM · media · messaging · SCM)
        ↑
Platform Kernel / Enterprise City Runtime (orchestration · registry · search · sessions)
```

## Canonical Systems of Record (selected)

| Capability | Canonical package | Sprint |
|------------|-------------------|-------|
| AI Runtime / Voice / Skills / Creative | `platform_ai` | 36.x–36.9 |
| Multi-Agent + City Runtime control plane | `platform_orchestrator` | 36.7 / **37.0** |
| Project Memory / Context | `platform_memory` | 36.5+ |
| Event Bus | `events` + enterprise control plane | 36.1 |
| Service Builder | `platform_service_builder` | 36.0 |
| Spatial City map (presentation) | `src/web/src/enterprise-city` | CG / EP-05 |

**Rule:** never create a parallel SoR (`platform_city`, `platform_creative`, …). Extend the canonical package.

## Enterprise City Runtime (37.0)

Control plane that **connects** modules — it does not replace module engines.

- Registry of all services (Sprint 1 → 36.9+)
- Unified workspace routing
- Shared sessions (context, memory, permissions, events)
- Global search + command center
- Executive dashboard + health + readiness

Entry: `platform_orchestrator.city_runtime_service.enterprise_city_runtime_service`

UI:

- Control console: `/platform`
- Spatial adapter: `/enterprise-city`

## API surface (platform)

- `/api/platform/*`
- `/api/dashboard/*`
- `/api/search/*`
- `/management/v1/platform/*`

## Data

Persistence tables for registry, sessions, metrics, health, usage, configuration — Alembic `t3n456789012`.

## Integration policy

Modules communicate through:

1. Service façades (typed Python services)
2. Enterprise Event Bus
3. Shared platform session context
4. Management / REST contracts (versioned)

Business logic stays inside domain packages; City Runtime orchestrates and observes.

## Related docs

- `docs/ENTERPRISE_CITY_RUNTIME.md`
- `docs/CITY_RUNTIME.md` (spatial adapter rules)
- `docs/SPRINT_37_0_RESULT.md`
- `platform_architecture/canonical_services.py`
