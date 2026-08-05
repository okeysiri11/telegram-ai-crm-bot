# Changelog — Platform Core

## [0.9.4-rc1] — 2026-08-05

Sprint 38.3 — Platform Stabilization & Release Candidate (no feature surface changes).

### Stabilization

- Restored `.github/workflows/architecture.yml` (was emptied; CI disabled)
- Added RC smoke pipeline: `scripts/smoke_platform_rc.py`
- Added RC pytest gate: `scripts/run_rc_test_suite.py`
- Added pytest failure classifier (CURRENT vs LEGACY): `scripts/classify_pytest_failures.py`
- Health contract: `GET /ready` aliases `/readiness`
- Ruff critical rules in CI; fixed undefined annotation names (`Partner` → `PartnerEnginePartner`, `OwnerVerticalNote` import)
- `ExternalAiGuard` signing secret prefers `AI_REQUEST_SIGNING_SECRET` / `IAM_JWT_SECRET`
- Release docs: `RELEASE_NOTES.md`, `TECHNICAL_DEBT.md`, `docs/SPRINT_38_3_RESULT.md`

### Known

- Historical sprint suites still pin old versions (classified LEGACY FAIL; not RC blockers)
- See `TECHNICAL_DEBT.md` for Sprint 39 follow-ups

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
