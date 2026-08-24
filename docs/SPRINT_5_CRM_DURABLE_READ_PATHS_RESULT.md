# Sprint 5 — CRM Durable Read Paths + Analytics + Health + Memory Overlay Cleanup

## Starting HEAD

`3af1f375802f4ed8b787973aea07500b75df71cf` on `develop` (Sprint 4 accepted and pushed).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery matrix

| Path | Class | Notes |
| --- | --- | --- |
| `application.py` `health()` `store.crm_leads` / `store.crm_deals` | **A** | Production overlay; now durable snapshot |
| `analytics/service.py` `store.leads` / `store.deals` / `store.customers` | **A** | Marketplace dashboard CRM counts; now durable snapshot |
| `dashboard/__init__.py` overview / `GET /analytics` / `GET /dashboard` | **A** | Sync readers of analytics service; HTTP now refreshes snapshot |
| `api/internal_handlers.py` pipeline | **A** | Now refreshes durable CRM pipeline snapshot |
| `crm/engine.py` `metrics()` | **A** | Already postgres; expanded with activities/opportunities/stage maps |
| `analytics/engine.py` workflow | **A** | Already postgres; expanded communications + deal-backed opportunities |
| `kpi/service.py`, `statistics/service.py`, `forecasting/service.py` | **A** | Already postgres for CRM entities; unchanged |
| `executive_dashboard/service.py` | **A** | Already consumed AnalyticsEngine/KPI (postgres CRM) |
| `customer_intelligence/service.py` | **A** | Already postgres for customers/activities/calls/emails |
| `GET /api/auto/v1/crm/metrics` | **A** | Already postgres via CRMEngine |
| `MemoryCRMPersistence` store collections | **C** | Test backend when `AUTO_CRM_PERSISTENCE=memory` |
| `store.phone_calls` / `email_messages` / `meetings` / `reminders` / `crm_tasks` / `interactions` | **C** | Internals of MemoryCRMPersistence only |
| `store.opportunities` | **E** | Unused leftover; initialization removed |
| `crm/service.py` `store.leads` / `store.deals` | **B** | Foundation marketplace CRM (appointments/negotiations/reservations); not Web CRM |
| `health()["foundation"]["crm"]` | **B** | Foundation `CRMService.metrics()`; separate domain |
| `dashboard.py` AutoDashboard `store.leads` | **B** | Sprint 13.0 dict-store dashboard, not Web CRM |
| Dealer CRM `dc_*` / Enterprise Automotive `ea_*` | **D** | Separate in-memory product suites |
| Agro `store.crm_leads` / `crm_tasks` | **D** | Other vertical |
| Telegram `ClientRequestCrmEngineV1` | **D** | Standalone Telegram request CRM (already Postgres of its own) |
| Vehicle `maintenance_reminders` | **D** | Service module, not CRM reminders |
| `intelligence_profiles` store | **B** | Analysis cache, not CRM source of truth |

## Health / counts

`health()` stays **synchronous**. It reads `CRMMetricsService.cached()`.

`CRMMetricsService.collect()` / `refresh()` query tenant-scoped `CRMPersistence` (PostgreSQL in production). HTTP `GET /api/auto/v1/health`, `/analytics`, `/dashboard`, and internal pipeline bind `X-Tenant-Id` and await refresh. No `asyncio.run()`, no second database architecture.

After process restart the snapshot is empty until the next async refresh (HTTP health or `crm_engine.metrics()`). Restart tests collect from a new persistence instance against PostgreSQL.

Additive health keys: `crm_customers`, `crm_tasks`, `crm_activities`, `crm_calls`, `crm_emails`, `crm_meetings`, `crm_reminders`, `crm_opportunities`. Existing `crm_leads` / `crm_deals` now come from the snapshot.

## Analytics / executive / intelligence

- `AnalyticsService.dashboard_metrics()` and `sales_pipeline()` read the CRM snapshot (leads/customers/deals/tasks/activities/communications/opportunities). Vehicles/payments/deliveries remain marketplace store collections (no CRM postgres equivalent).
- `AnalyticsEngine.workflow_analytics()` adds activities, calls, emails, and deal-backed opportunities.
- Executive dashboard already used AnalyticsEngine/KPI (durable CRM).
- Customer intelligence already used persistence.

## Opportunities

`store.opportunities` had no production read/write path. Initialization was removed. Durable opportunities remain a **deal projection** (`opportunities` count == `deals` count). No opportunities table.

## Telegram / foundation boundaries

- **Telegram `ClientRequestCrmEngineV1`**: separate Postgres-backed Telegram request CRM. Not an Auto Marketplace Web CRM overlay. Left untouched.
- **Foundation `crm/service.py`**: marketplace Lead/Deal/appointment/negotiation/reservation domain. Routing it through Web CRM tables would change behavior. Left as compatibility.

## Tenant isolation

`collect(tenant_id)` and HTTP health with `X-Tenant-Id` are tenant-scoped. Tenant B cannot see tenant A counts.

## Migration

`MIGRATION_REQUIRED=NO`

Read-path/service only. Alembic head remains `s8n901234567` (count 1).

## Tests

Targeted (74 passed):

- `tests/test_auto_marketplace_crm_metrics.py`
- `tests/test_auto_marketplace_crm_postgres.py`
- `tests/test_crm_engine.py`
- `tests/test_crm_api_security_40_1.py`
- `tests/test_auto_marketplace_crm_workflow.py`
- `tests/test_auto_marketplace_crm_communications.py`

Broader (122 passed, includes targeted):

- plus `tests/test_bi_engine.py`
- `tests/test_portal_engine.py`
- `tests/test_api_v1_freeze.py`
- `tests/test_manager_dashboard.py`
- `tests/test_crm_foundation_40_2.py`

## Remaining memory-backed paths

- `MemoryCRMPersistence` / store collections (tests)
- Foundation `crm/service.py` leads/deals/appointments
- Foundation health `foundation.crm` metrics
- Sprint 13.0 `AutoDashboard` dict store
- Dealer CRM / Enterprise Automotive CRM suites
- Telegram `ClientRequestCrmEngineV1` (separate durable domain)
- Vehicle maintenance reminders
- `intelligence_profiles` analysis cache
- Non-CRM store counts (vehicles, payments, finance, BI dashboards)

## Known pre-existing debt

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` 401 under CRM mutation gate

Frontend build was not run: no frontend files changed.
