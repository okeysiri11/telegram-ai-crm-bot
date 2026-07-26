# Legal Integration Guide — Sprint 31.2

## Principle

Do **not** invent a parallel Legal OS. Legal Enterprise already provides registry CRM, case management, document intelligence, compliance counterparties, AI Legal Assistant, and executive analytics. Sprint 31.2 activates them as the fifth pilot.

## API prefixes (existing)

| Prefix | Role |
|--------|------|
| `/api/legal-enterprise/v1` | Registry (entities, individuals, attorneys), foundation health |
| `/api/legal-cm/v1` | Cases, calendar/hearings, tasks, deadlines, case documents, signatures |
| `/api/legal-di/v1` | Templates, contracts, drafting |
| `/api/legal-cp/v1` | Companies + counterparties (client CRM) |
| `/api/legal-aa/v1` | AI Lawyer / research / opinion |
| `/api/legal-ei/v1` | Owner executive dashboards + analytics |

## Pitfall

Use **CM cases** (`/api/legal-cm/v1/cases`) for hearings/tasks/docs. Foundation `/legal-enterprise/v1/cases` is a separate store — IDs do not mix.

## Shared platform

Authentication · Authorization/RBAC · Workspace · Mission Control · Knowledge · Workflow engine · Notification Center · AI Team · Concierge · Analytics · Telemetry · Audit Log
