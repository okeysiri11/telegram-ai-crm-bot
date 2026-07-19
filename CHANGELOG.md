# Changelog — Platform Core

## [1.0.0-rc1] — 2026-07-19

Sprint 1.5 — Platform Certification & RC1. Platform Core is certified as the frozen architectural baseline for all future AI verticals.

### Certification

- Full platform certification: **PASS** (12/12 gates, score 100.0)
- Architecture audit: **PASS** (score 99.5)
- Security validation: **PASS**
- Dependency governance: **PASS** (strict governed cycles = 0)
- pytest: 497 passed (`-m "not slow"`)

### Architecture

- Removed deprecated unauthenticated `routers/admin/` package (routes were already unregistered in Sprint 1)
- Architecture baseline generated under `docs/architecture_baseline/`
- ORM naming collisions resolved (`LedgerEngineEntry`, `PartnerEnginePartner`)
- Lazy `database/__init__` bootstrap breaks config circular import during test collection
- RBAC model load order fixed in `database/migration_models.py`

### Event Bus

- CRM worker entry consolidated via `events/crm_publisher.get_crm_worker()`
- `startup.py` uses canonical CRM publisher (no direct `crm_event_bus` at call sites)
- Direct `crm_event_bus` imports in `services/pg_*`: **0**

### Workflows

- Workflow status comparison normalized (case-insensitive COMPLETED/FAILED)
- Resume path passes user input on first step after WAITING
- AI workflow definitions: lead qualification input mappings aligned with skill contracts
- `run_interactive()` accepts `**kwargs` for plugin compatibility

### CI

- `.github/workflows/architecture.yml`: multi-job pipeline (pytest, architecture, security, certification, rc-build)

### Tests

- Session RBAC model registration fixture
- Tests aligned with unified `PlatformEventBus` workflow events
- SDK vertical test mocks `RequestService.persist_crm_request`
- Certification pytest excludes `@pytest.mark.slow` to prevent recursive certification runs

### Documentation

- README synchronized with RC1 validation commands
- Certification reports regenerated under `docs/CERTIFICATION_*.md`
- `docs/ARCHITECTURE_BASELINE.md` frozen for RC1

### Preserved (Sprint 1)

All Sprint 1 architectural recovery commits remain intact: management SLA routes, admin security tests, SDK→Services boundary, Repository facade removal, governance CI, and configuration authorization hardening.
