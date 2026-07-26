# Automotive Workflow Documentation — Sprint 30.6

## Route

`/workspace/auto` → `AutomotiveLiveWorkflowPage`

## Steps (existing APIs only)

| # | Step | API |
|---|------|-----|
| 1 | Customer authentication | `POST /api/auto/v1/portal/auth/register` or `/login` |
| 2 | Dashboard | `GET /api/auto/v1/dashboard` |
| 3 | CRM customer | portal `customer_id` or `POST /api/auto/v1/crm/customers` |
| 4 | Lead | `POST /api/auto/v1/crm/leads` (+ `next_best_action`) |
| 5 | AI Concierge | `POST/PATCH /api/platform-builder/v1/concierge/sessions` + preview |
| 6 | Task | `POST /api/auto/v1/crm/tasks` |
| 7 | Notification | `POST /api/enterprise-comms/v1/center` |
| 8 | Mission Control | `GET …/mission-control/status` + `/activity` |
| 9 | Analytics | `GET /dashboard`, `/crm/pipeline`, `/bi/dashboard` |
| 10 | Observability | OBS `/logs` + `/metrics` |

## UI

Shared EDS: Button, Input, Card, Badge, Table, EmptyState, WorkspaceLayout.

## Telemetry

`businessEvent`, `aiActivity`, `apiCall`, `audit`, `error` via existing OBS client.
