# Release Notes — Platform Core v1.0.0-rc1

**Tag:** `platform-core-v1.0.0-rc1`  
**Date:** 2026-07-19  
**Sprint:** 1.5 — Platform Certification & RC1

## Summary

Platform Core reaches Release Candidate 1. This is the **frozen architectural baseline** for all future verticals (Auto, Agro, Port, Legal, Beauty, Cafe, Marketplace, ERP, AI Agents). No new features were added in this sprint — only certification, cleanup, documentation, and test stabilization.

## Certification Verdict

| Metric | Result |
|--------|--------|
| Certification score | **100.0 / 100** |
| Gates passed | **12 / 12** |
| Architecture score | **99.5 / 100** |
| Security | **PASS** |
| Dependency governance | **PASS** (strict cycles = 0) |
| PlatformEventBus | **PASS** |
| SDK isolation | **PASS** |
| Release readiness | **PASS** |

## What Changed Since Sprint 1

1. **Legacy admin routers deleted** — `routers/admin/` removed (already unregistered from `api/server.py`).
2. **Event bus migration completed** — internal events route through `PlatformEventBus`; CRM outbox via `events/crm_publisher.py`.
3. **Architecture baseline frozen** — graphs in `docs/architecture_baseline/`.
4. **CI pipeline expanded** — PR checks for pytest, architecture, security, dependency, certification, RC build.
5. **Test suite stabilized** — 497 tests pass; certification excludes slow recursive scan.

## Upgrade / Validation

```bash
.venv/bin/python -m pytest tests/ -q -m "not slow"
.venv/bin/python scripts/validate_architecture.py
.venv/bin/python scripts/validate_legacy_migration.py
.venv/bin/python scripts/generate_architecture_baseline.py
.venv/bin/python scripts/run_platform_certification.py
```

Expected certification output: `certification_verdict=PASS score=100.0 release=PASS gates=12/12`

## Known Technical Debt (Deferred to Sprint 2)

See `docs/TECH_DEBT.md`. Legacy `services/pg_*` dependency cycles remain isolated behind compatibility adapters; handler DB direct access is allowlisted and tracked.

## API Surfaces (Unchanged)

- Management: `/management/v1/*` (authenticated)
- Public: `/api/v1/*` (frozen contract)
- No unauthenticated admin routes
