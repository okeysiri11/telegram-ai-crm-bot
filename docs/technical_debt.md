# Technical Debt Report

Night architecture audit — read-only analysis of production codebase.

## 1. Cyclic / fragile imports

| Issue | Detail | Risk |
|-------|--------|------|
| Cross-router imports | `auto_client_router` ↔ `auto_hub_router` | Medium |
| Lazy import soup | Many `from services.X import` inside methods | Medium (opaque graph) |
| Root `events.py` name | Blocks clean `events/` package | Medium |
| Duplicate Role/Permission ORM | Historical mapper collisions | High |

**Mitigation started:** domain events live in `src/events/`; DI via `container.py`.

## 2. Overloaded / god classes

| File | Lines | Problem |
|------|------:|---------|
| `database_legacy.py` | ~11k | Legacy catch-all |
| `handlers.py` | ~5k | All menus/domains |
| `keyboards.py` | ~2k | UI god module |
| `auto_vertical_handlers.py` | ~1.2k | Vertical + billing + AI |
| Large `pg_*` engines | 700–1000+ | Multi-concern services |

## 3. Logic duplication

- Notification stacks (2–3 generations)
- Storage providers duplicated (`services/storage` + `src/platform/storage`)
- Multiple inventory concepts (dealer vehicles vs marketplace inventory vs listings)
- Dual event buses + new domain dispatcher
- Dual audit tables
- Dual SLA systems
- Multiple RBAC generations (`permission_engine`, `rbac_v2`, hierarchical)

## 4. Performance bottlenecks

| Area | Note |
|------|------|
| Sync OpenRouter calls in request finish | Adds latency to lead create |
| Escalation loop every 60s full table scan | OK for low volume; needs indexes/pagination at scale |
| N+1 risk in manager “clients” listing | Derived from leads list |
| Media group delivery | Batched by 10 — fine; local cache growth unbounded |
| `configure_mappers()` failures | Blocks some introspection tooling |

## 5. Scalability risks

1. **Monolithic process** — bot polling + API + scheduler + escalation in one process.
2. **In-memory vertical flow state** (`auto_vertical_flow` dict) — lost on restart / multi-replica unsafe.
3. **FSM MemoryStorage fallback** — multi-instance unsafe without Redis.
4. **God handlers** — hard to horizontal-scale teams/modules.
5. **Schema sprawl** — 100+ models without clear bounded contexts.

## 6. Security / ops debt

- Default `JWT_SECRET` placeholder
- Email/SMS providers stubs
- Sentry optional / often unset
- Owner/manager IDs env-dependent

## Priority backlog (recommended next sprint)

1. Extract shared menu helpers to break router cross-imports (**low risk**).
2. Wire `container.py` for storage/notifications only (**opt-in**).
3. Dual-emit `src.events` from CRM submit path behind feature flag.
4. Split `handlers.py` by domain files without changing callbacks.
5. Enforce Redis for FSM in production (`REDIS_REQUIRED=true`).
6. Consolidate RBAC to `permission_engine_*` only.
7. Move auto_vertical in-memory flow to Redis/FSM.
8. Process split: bot worker / API / scheduler.

## Explicitly out of scope (this night)

- No FSM changes
- No router behavior changes
- No lead/manager scenario changes
- No deletions of existing files
