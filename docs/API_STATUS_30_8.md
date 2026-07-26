# API Status — Sprint 30.8

## Beauty domain (production-mounted, reused)

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/enterprise-bos/v1/health` | Ready |
| POST | `/api/enterprise-bos/v1/bootstrap` | Ready |
| POST | `/api/enterprise-bos/v1/customers` | Ready |
| POST | `/api/enterprise-bos/v1/employees` | Ready |
| POST | `/api/enterprise-bos/v1/services` | Ready |
| POST | `/api/enterprise-bos/v1/appointments` | Ready |
| GET | `/api/enterprise-bos/v1/dashboard` | Ready |
| GET | `/api/enterprise-bws/v1/health` | Ready |
| POST | `/api/enterprise-bws/v1/bootstrap` | Ready |
| GET/POST | `/api/enterprise-bws/v1/schedule` | Ready |
| GET | `/api/enterprise-bws/v1/dashboard` | Ready |
| GET | `/api/enterprise-bws/v1/notifications` | Ready |
| GET | `/api/enterprise-bcj/v1/health` | Ready |
| POST | `/api/enterprise-bcj/v1/book` | Ready |
| POST | `/api/enterprise-bcj/v1/journey` | Ready |
| POST | `/api/enterprise-bcj/v1/assistant` | Ready |
| GET | `/api/enterprise-amo/v1/health` | Ready |
| POST | `/api/enterprise-amo/v1/bootstrap` | Ready |

## Shared platform APIs (unchanged ownership)

| Area | Prefix |
|------|--------|
| Concierge | `/api/platform-builder/v1/concierge/*` |
| Mission Control | `/api/platform-builder/v1/mission-control/*` |
| Comms | `/api/enterprise-comms/v1/center` |
| Observability | `/api/enterprise-obs/v1/*` |
| Automotive CRM | `/api/auto/v1/*` (reference; unchanged) |

No Beauty-specific forks of Concierge, Comms, OBS, or Mission Control.
