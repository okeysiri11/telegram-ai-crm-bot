# Foundation Completion — Sprint 35.1

**Status:** Complete — Enterprise Foundation LOCKED  
**Date:** 2026-08-03  
**Depends on:** 34.2A–D · 35.0 Stabilization

---

## Verdict

The Enterprise Foundation is **officially completed and frozen**.

| Registry | Canonical |
|----------|-----------|
| Identity | `platform_identity` |
| Navigation / Menus | `platform_registry` |
| Permissions | `platform_identity` registries + IAM |
| Services | `platform_architecture.canonical_services` (+ discovery query API) |
| Events (bus) | `events.event_bus.PlatformEventBus` |
| Events (store) | `platform_state.event_store` (JSONL · optional Postgres) |
| State / Sync / Version | `platform_state` |

No parallel SoR. Projections and adapters remain labeled and non-authoritative.

---

## Completed requirements

1. **TD-54** — VersionMixin retrofit across persistent SQLAlchemy models (~293 classes / 110 files)
2. **VersionMixin** — collision-safe (no String `tenant_id`); core Alembic migration
3. **Registry-driven navigation** — Web Menu API Bridge + static fallback
4. **ISAM** — `platform_identity.hub_bridge` adapter (no Hub auth rewrite)
5. **Web Menu API Bridge** — `menuApiBridge.ts` → `/management/v1/platform-registry/navigation`
6. **HA version headers** — `warm_start` + optional heads checkpoint
7. **Canonical Service Registry** — foundation_locked flags + discovery entry
8. **Service Discovery** — `PlatformServiceDiscovery` over CANONICAL_SERVICES
9. **Identity registration** — discovery identity_registration()
10. **Permission sync** — `permission_sync.sync_permission_registry`
11. **Event Store abstraction** — JSONL SoR + optional Postgres dual-write
12. **Postgres event table** — migration `platform_state_events` (API unchanged)
13. **Duplicate registries** — marked as projections (not deleted)
14. **JSONL compatibility** — verified in tests
15. **34.2A–D backward compatibility** — regression suite green
16. **Docs** — this file + EVENT_STORE / TECH_DEBT / RESULT updates
17–19. **Tests** — `tests/test_foundation_35_1.py` + prior foundation suites
20. **Report** — `docs/SPRINT_35_1_RESULT.md`

---

## Frozen rule

Sprint **36.x** may begin only against this locked foundation.  
Do not add parallel identity, menu, event-bus, or versioning SoRs.
