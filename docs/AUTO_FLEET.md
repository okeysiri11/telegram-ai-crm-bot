# Auto Marketplace — Fleet, Rental & Corporate Mobility (Sprint 10.7)

Fleet operations for **Auto Marketplace 4.1.7-enterprise**.

| Field | Value |
|-------|-------|
| Application version | `4.1.7-enterprise` |
| `fleet_engine` | `1.0` |
| `rental_engine` | `1.0` |
| `operations_engine` | `1.0` |

**Hard constraint:** AI Platform Core, AI Ecosystem, Agro Marketplace, and Port ERP are not modified.

## Domain facade

```python
from applications.auto_marketplace import auto_marketplace

assert auto_marketplace.config.fleet_engine == "1.0"
metrics = auto_marketplace.fleet_ops.metrics()
```

## Fleet Management

Registry, driver assignment, fuel/tires, accidents, maintenance planning, profitability analytics.

## Rental Engine

Short-term, long-term, and corporate rentals with availability, pricing, contracts, returns, and damage reports.

## Fleet Leasing

Operational and financial leasing with payment schedules, residual value, buyout, approvals, and insurance — under `/api/auto/v1/leasing/fleet/*` (purchase leasing remains at `/leasing/quote`).

## Corporate Mobility

Company fleets, employee assignments, pool bookings, travel requests, department analytics.

## Dispatch & Telematics

Vehicle/driver/task dispatch with AI queue optimization; GPS/OBD/fuel/mileage/behavior/EV battery.

## Executive Dashboard & AI Operations

KPIs, live map, AI assistant; predictive maintenance, demand/pricing/utilization forecasts, risk scoring, driver recommendations.

## REST API

| Prefix | Capability |
|--------|------------|
| `/api/auto/v1/fleet` | Registry, vehicles, analytics |
| `/api/auto/v1/rental` | Availability, pricing, reserve/return |
| `/api/auto/v1/leasing` | Purchase leases + `/leasing/fleet/*` |
| `/api/auto/v1/drivers` | Driver profiles & ratings |
| `/api/auto/v1/dispatch` | Fleet dispatch jobs |
| `/api/auto/v1/operations` | Executive, AI, telematics, corporate |

## Modules

`fleet/` · `rental/` · `leasing/` · `subscriptions/` · `corporate/` · `dispatch/` · `telematics/` · `drivers/` · `operations/` · `executive/` · `mobility/` · `ai_operations/`
