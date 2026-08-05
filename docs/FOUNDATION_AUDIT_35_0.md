# Foundation Audit — Sprint 35.0

**Date:** 2026-08-03  
**Mode:** Stabilization (no architecture rewrite)  
**Canonical baseline:** Sprints 34.2A–34.2D

---

## Executive verdict

34.2A–D foundation is **real and canonical**. Sprint 35.0 does not replace it.

Primary issues found:

1. **Critical (fixed):** `PlatformEventStore` used `sqlite3` — violated `scripts/check_no_sqlite.py` (POSTGRES_ONLY). Stabilized to JSONL backend; **public API unchanged**.
2. **High (docs fixed):** Architecture reviews still claimed SyncEngine / TD-54 missing after they shipped.
3. **Medium (thinned):** `PlatformStateAudit` dual-wrote a second timeline list — now hot buffer + AuditService bridge only.
4. **Allowlisted (kept):** TD-20 EventBuses, Hub ISAM, Hub EventStore, web shell menu projections — adapters, not deleted.

---

## Canonical map

| Capability | Canonical | Status |
|------------|-----------|--------|
| Identity | `platform_identity/` | ✅ 34.2A |
| Registry / menus / navigation | `platform_registry/` | ✅ 34.2B |
| Platform State / client runtimes | `platform_state/` | ✅ 34.2C |
| Sync Engine | `platform_state.sync_engine` | ✅ 34.2C |
| Version Engine + VersionMixin | `version_engine` + `mixins.VersionMixin` | ✅ 34.2D (model retrofit open) |
| Event Store | `platform_state.event_store` | ✅ 34.2D / JSONL 35.0 |
| Event Bus | `events.event_bus.PlatformEventBus` | ✅ |
| Conflict (platform) | `conflict_engine` (`conflict.py` shim) | ✅ |
| Workflow | `platform_workflow/` | ✅ (legacy adapters remain) |
| Knowledge | `platform_enterprise_knowledge_graph/` | ✅ |
| Permissions / routing / navigation | Identity + Registry | ✅ |

Registered in `platform_architecture/canonical_services.py` (Sprint 35.0).

---

## Duplicates — keep vs allowlist

| Item | Action |
|------|--------|
| Allowlisted EventBuses (TD-20) | **allowlist** — no new buses |
| Hub / ecosystem EventStore | **allowlist** — not platform SoR |
| Hub ISAM vs Identity Core | **allowlist** — fold-in later |
| Web menuCatalog / shellModuleRegistry | **bridge later** — keep projections |
| `entity_versions` vs VersionEngine | **keep** facade |
| `conflict.py` vs `conflict_engine.py` | **keep** shim |
| Collaboration ConflictResolver | **keep** — separate domain |
| `audit.py` dual timeline | **thinned** 35.0 |

---

## Cyclic imports

| Risk | Mitigation |
|------|------------|
| `platform_state` package `__init__` eager graph | **Lazy `__getattr__` exports** (35.0) |
| `cache` → `service` | Already lazy function imports |

---

## Dead / misleading claims

| Claim | Action |
|-------|--------|
| ARCHITECTURE_REVIEW_34_2C §7.1 SyncEngine missing | Supersession banner |
| TECH_DEBT TD-54 “no VersionMixin” | Marked PARTIAL |
| CANONICAL_SERVICES omitting 34.2 foundations | Extended |
| UNIFIED_PLATFORM_STATE layout stuck at 34.2C | Extended |

---

## Safe cleanups performed (35.0)

1. Event Store → JSONL (remove sqlite3)
2. Audit dual-write thinning
3. Lazy `platform_state` package exports
4. Canonical services registry + docs sync
5. Debt / review / layout doc synchronization
6. Register `realtime.channel.platform_state` in IAM (channel added in 34.2C but permissions missing — compatibility break fixed)

## Explicitly NOT done (risky)

- Deleting TD-20 buses, Hub ISAM, shell registries
- Moving packages
- Changing public HTTP/client APIs
- Rewriting business logic

---

## Remaining technical debt (for 35.1+)

1. Retrofit `VersionMixin` onto SQLAlchemy models (TD-54 remainder)
2. Bridge Web menu catalogs to Registry API (eliminate hand-mirrored TS)
3. Opportunistic TD-20 EventBus cutover
4. Hub ISAM → Identity Core fold-in
5. Multi-instance durable VersionEngine heads (HA)
6. Optional Postgres-backed Event Store table (when scaling beyond JSONL)
