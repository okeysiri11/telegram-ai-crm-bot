# Agriculture Integration Guide — Sprint 31.1

## Principle

Do **not** invent a parallel Agriculture OS. Agro Marketplace and Agro Enterprise Supply Chain already provide farm CRM, harvest, warehouse, marketplace trade, export, and logistics. Sprint 31.1 activates them as the fourth pilot.

## API prefixes (existing)

| Prefix | Role |
|--------|------|
| `/api/agro/v1` | Farmers, farms, fields, products, harvest, warehouse, inventory, CRM, marketplace, orders, export shipments, containers, tracking, analytics, KPI |
| `/api/agro-supply-chain/v1` | Elevator, quality, export contracts/docs, logistics freight/route/delivery, dashboards |
| `/api/agro-enterprise/v1` | Enterprise health |
| `/api/agro-finance/v1` | Finance health |
| `/api/ai-agronomist/v1` | AI Agronomist health |

## Shared platform (no forks)

Authentication · Authorization/RBAC · Workspace · Mission Control · CRM patterns · Workflow engine (`ecosystem-template`) · Knowledge · Notification Center · AI Team · Concierge · Analytics · Telemetry/OBS

## Web wiring

- `webConfig.agroPrefix` (+ supply-chain / enterprise / finance / ai-agronomist)
- `hubIntegrations.agro*`
- Routes `/workspace/agro` (+ `/:sub`) before module catch-all
- Module registry thickened to operational pilot
