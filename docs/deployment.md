# Agro Marketplace Deployment Guide

## Prerequisites

- Python 3.11+ with project virtualenv
- AI Platform Core v3.0 available on `PYTHONPATH` (unchanged)
- AI Ecosystem v1.5 available on `PYTHONPATH` (unchanged)
- Application package: `applications/agro_marketplace`

## Configuration verification

Confirm `applications/agro_marketplace/config.py` / `manifest.json`:

| Key | Expected |
|-----|----------|
| `application_version` | `2.0.0` |
| `application_status` | `Production Ready` |
| `release` | `Commercial` |

## Deploy steps

1. Install dependencies into the project venv.
2. Ensure Platform Core and Ecosystem imports resolve (do not patch them).
3. Mount agro routes via `register_agro_marketplace_routes(app)` (already wired from host `api/server.py` when enabled).
4. Verify:
   - `GET /api/agro/v1/health`
   - `GET /api/agro/v1/ops/health`
   - `GET /api/agro/v1/ops/version`
   - `POST /api/agro/v1/ops/readiness`
5. Run commercial certification: `POST /api/agro/v1/ops/release`

## Deployment verification

```bash
.venv/bin/python -m pytest tests/test_agro_*.py -q
```

Or via API: `POST /api/agro/v1/ops/deploy/verify`

## Rollback notes

- Application state is in-memory (`AgroStore`). Restart clears operational data.
- Version pin is configuration-only; revert `config.py` / `manifest.json` if needed.
- Never roll back by editing Platform Core or Ecosystem.

## Disaster recovery (summary)

| Scenario | Action |
|----------|--------|
| Process crash | Restart host API; re-seed via portals/ops as needed |
| Bad config | Restore `config.py` / `manifest.json` to `2.0.0` Production Ready |
| Bridge outage | Agro remains up with fallbacks; check `/ops/health` component section |
| Data loss | Rebuild from partner/ERP sync hooks and re-import catalog/CRM |

Full operational procedures: [OPERATIONS.md](OPERATIONS.md).
