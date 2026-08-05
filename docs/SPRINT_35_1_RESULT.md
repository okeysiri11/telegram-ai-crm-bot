# Sprint 35.1 — Foundation Completion Result

**Date:** 2026-08-03  
**Principle:** Complete remaining foundation debt. No new business features. No public API breaks.

---

## Files changed (summary)

### Database / TD-54
- `database/models/mixins.py` — VersionColumnsMixin / VersionMixin (no String tenant_id)
- `database/models/*.py` — VersionMixin on ~293 persistent entity classes
- `migrations/versions/h1b234567890_td54_version_mixin_and_event_store.py`

### Platform runtime
- `platform_state/version_engine.py` — HA warm_start + checkpoint
- `platform_state/event_store.py` — optional Postgres dual-write hook
- `platform_state/event_store_postgres.py` — Postgres backend helper
- `platform_state/enterprise.py` — foundation_locked flag

### Identity / architecture
- `platform_identity/hub_bridge.py` — ISAM adapter bridge
- `platform_identity/permission_sync.py`
- `platform_architecture/service_discovery.py`
- `platform_architecture/canonical_services.py` — locked foundation entries

### Web navigation
- `src/web/src/platform-registry/menuApiBridge.ts`
- `src/web/src/platform-registry/menuCatalog.ts` — fallback labeling
- `src/web/src/ux-revolution/intelligentNavGroups.ts` + `index.ts`
- `src/web/src/navigation/Sidebar.tsx` — prefetch
- shell/module catalogs — projection labels

### Docs / tests
- `docs/FOUNDATION_COMPLETION_35_1.md`
- `docs/SPRINT_35_1_RESULT.md`
- `docs/TECH_DEBT.md` (TD-54 resolved)
- `tests/test_foundation_35_1.py`

---

## Compatibility

Public APIs unchanged. Sprint 34.2A–D surfaces remain. JSONL Event Store remains default.

Optional: `ADOS_EVENT_STORE_BACKEND=postgres` dual-writes to `platform_state_events`.

---

## Test evidence

`tests/test_foundation_35_1.py` + 34.2A/B/C/D regression suite.

---

## Foundation lock

| Single SoR | Package |
|------------|---------|
| Identity | `platform_identity` |
| Navigation | `platform_registry` |
| Permissions | `platform_identity` |
| Services | `canonical_services` + discovery |
| Event Bus | `PlatformEventBus` |
| Event Store | `platform_state.event_store` |
| Versioning | `VersionMixin` + `VersionEngine` |

**Sprint 36.x may begin.**
