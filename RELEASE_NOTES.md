# Release Notes — ADOS Platform v0.9.4-rc1

**Tag:** `v0.9.4-rc1`  
**Date:** 2026-08-05  
**Sprint:** 38.3 — Platform Stabilization & Release Candidate

## Summary

ADOS local platform is stabilized as a Release Candidate after Sprint 38.2
infrastructure recovery. This RC does **not** add product features — it locks
startup, health, CI, smoke, and critical-path correctness so Sprint 39 can
resume feature work on a known-good baseline.

## What works

- `docker compose up --build` brings up postgres, redis, bot/API, nginx, prometheus, grafana
- All compose services report **healthy**
- `GET /health`, `/liveness`, `/readiness`, `/ready` respond 200 when the stack is up
- Alembic reaches `head` via `docker-entrypoint.sh` before the bot process starts
- Critical Python modules import cleanly (engines, AuditTrail, AIRouter, startup)
- RC pytest gate (`scripts/run_rc_test_suite.py`) is green
- Platform Core CI workflow restored and extended with lint, RC tests, docker smoke

## Highlights since 38.2

| Area | Change |
|------|--------|
| Health contract | Added `/ready` alias → readiness handler |
| CI | Restored emptied `.github/workflows/architecture.yml`; RC jobs + docker smoke |
| Smoke | `scripts/smoke_platform_rc.py` — full compose lifecycle automation |
| Static analysis | Ruff critical rules on services/api; F821 annotation fixes |
| Security | `ExternalAiGuard` signing secret prefers env (`AI_REQUEST_SIGNING_SECRET` / `IAM_JWT_SECRET`) |
| Tests | Infrastructure smoke covers `/ready`; failure classifier separates LEGACY vs CURRENT |

## Known limitations (not RC blockers)

- ~350 historical sprint tests still assert frozen milestone versions (LEGACY FAIL)
- `mypy` / `pyright` are not yet project standards (documented debt)
- Workflow condition evaluator still uses sandboxed `eval` (see TECHNICAL_DEBT)
- Production secrets in `.env.production` remain placeholders (`CHANGE_ME`)
- Docker Desktop on 8 GB hosts remains resource-sensitive during cold builds

## Upgrade / run

```bash
docker compose down
docker compose up --build
# or automated:
python scripts/smoke_platform_rc.py
```

## Verdict

**READY FOR SPRINT 39** — feature development may resume on this RC baseline.
