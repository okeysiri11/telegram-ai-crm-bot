# Hercules API

## Prefixes

- `/management/v1/hercules/*` (canonical)
- `/management/hercules/*` (legacy dual)
- `/api/hercules/*` (additive public mount)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | Health stub |
| GET | `/dashboard` | Full Control Center payload |
| GET | `/metrics` | Jobs/sec, latency, cost |
| GET | `/resources` | CPU/GPU/RAM |
| GET | `/queues` | Lane depths |
| GET | `/workers` | Worker registry |
| GET | `/runtime` | Domains + recent jobs |
| GET | `/telemetry` | Diagnostics |
| GET | `/jobs` | Job list |
| GET | `/jobs/{id}` | Job status |
| POST | `/jobs` | Submit AI job `{prompt, modality, vertical}` |
| POST | `/jobs/{id}/cancel` | Cancel |
| POST | `/jobs/{id}/retry` | Retry |

Roles: READ_ONLY for GET; ADMINISTRATOR for POST.
