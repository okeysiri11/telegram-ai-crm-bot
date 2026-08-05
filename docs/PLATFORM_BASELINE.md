# ADOS Platform Baseline — v0.9.4-rc1

**Frozen:** 2026-08-05 (Sprint 38.4)  
**Policy:** [`docs/DEVELOPMENT_POLICY.md`](DEVELOPMENT_POLICY.md)  
**Result:** [`docs/SPRINT_38_4_RESULT.md`](SPRINT_38_4_RESULT.md)

This document is the recovery and certification record for the Release Candidate.
Do not edit casually — update only in an infrastructure sprint.

---

## Git freeze

| Item | Value |
|------|-------|
| Tag | `v0.9.4-rc1` |
| Release branch | `release/0.9.4` |
| Working branch | `develop` |
| Pre-freeze tip (before freeze commit) | `574d168460f517b893fbb20d19c920f142a67e8d` |

---

## Component versions (workstation at freeze)

| Component | Version |
|-----------|---------|
| Python (host / venv) | 3.14.6 |
| Docker Engine | 28.4.0 (build d8eb465) |
| Docker Compose | v2.39.4-desktop.1 |
| Node.js | v24.18.0 |
| npm | 11.16.0 |
| PostgreSQL (container) | 16.14 (postgres:16-alpine) |
| Redis (container) | 7.4.10 (redis:7-alpine) |
| Alembic head revision | `u4o567890123` (`u4o567890123_version_mixin_full_backfill.py`) |
| Nginx image | nginx:1.27-alpine |
| Prometheus image | prom/prometheus:v2.54.1 |
| Grafana image | grafana/grafana:11.2.0 |
| Bot image (local) | `telegrambotcourse-bot:latest` (~2.15GB) |

---

## Docker images (local freeze inventory)

| Image | Notes |
|-------|-------|
| `telegrambotcourse-bot:latest` | Application (API + Telegram bot) |
| `postgres:16-alpine` | Primary datastore |
| `redis:7-alpine` | Cache / bus adjunct |
| `nginx:1.27-alpine` | SPA front door |
| `prom/prometheus:v2.54.1` | Metrics |
| `grafana/grafana:11.2.0` | Dashboards |

---

## Health / ready (validated at freeze)

| Endpoint | HTTP | Payload |
|----------|------|---------|
| `GET /health` | 200 | `status=healthy`, `ready=true`, `ok=true` |
| `GET /ready` | 200 | `status=ready`, `ready=true` |
| `GET /readiness` | 200 | alias of ready contract |
| `GET /liveness` | 200 | process alive |

Compose services at freeze: **postgres, redis, bot, nginx, prometheus, grafana — all Healthy**.

---

## Migrations

| Item | Value |
|------|-------|
| Location | `migrations/versions/` |
| File count | 129 |
| Head file | `u4o567890123_version_mixin_full_backfill.py` |
| Head file SHA-256 | `5b75f48c65285811ed0828571a20b41991dd028d68541d58d6312a799efd3d66` |
| Tree SHA-256 (name+file hashes) | `f3b5d0010673e34654e8095111565098f5555f22f18f868c27ca372a83d7dd92` |
| Detail JSON | [`docs/baseline_migration_checksums_38_4.json`](baseline_migration_checksums_38_4.json) |
| Apply path | `docker-entrypoint.sh` → `scripts/ensure_local_schema.py` → `alembic upgrade head` |

---

## Test gates at freeze

| Gate | Result |
|------|--------|
| `scripts/validate_platform_protections.py` | **PASS** |
| `scripts/pre_merge_gate.py --with-docker` | **PASS** |
| `scripts/smoke_platform_rc.py` | **32/32 PASS** |
| `scripts/run_rc_test_suite.py` | **PASS** (RC critical suite) |
| Full historical pytest | LEGACY version-pin failures remain (see Sprint 38.3); not RC blockers |

---

## Recovery contract

```bash
git clone <repo-url>
cd telegram-ai-crm-bot   # or local path
git checkout v0.9.4-rc1  # immutable baseline
# or: git checkout develop  # ongoing work
cp .env.example .env     # set BOT_TOKEN and secrets
docker compose up --build
```

Expected without manual schema steps:

1. Postgres + Redis healthy  
2. Bot runs migrations then serves API  
3. `/health` and `/ready` return 200  
4. nginx / prometheus / grafana healthy  

---

## Protection tooling

| Script | Purpose |
|--------|---------|
| `scripts/validate_platform_protections.py` | Empty modules, shadowing, health/ready, migrations, registries |
| `scripts/pre_merge_gate.py` | Ruff + protections + RC pytest (+ optional docker smoke) |
| `scripts/smoke_platform_rc.py` | Full stack smoke |
| `docs/DEVELOPMENT_POLICY.md` | Human-enforceable rules |

---

## Freeze declaration

Infrastructure for **ADOS v0.9.4-rc1** is **FROZEN**.

Subsequent sprints must follow `DEVELOPMENT_POLICY.md`: minimal diffs, no mass renames,
no API renames, no architecture rewrites unless scheduled as an infrastructure sprint.
