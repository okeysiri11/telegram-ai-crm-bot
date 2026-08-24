# Sprint 6 — CRM Legacy Memory Path Elimination

## Starting HEAD

`371610cbb425af83850759a0179f16ae338011c6` on `develop` (Sprint 5 accepted and pushed).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery classification

| Path | Class | Action |
| --- | --- | --- |
| `MemoryCRMPersistence` using `MarketplaceStore` CRM collections | **A/C mix** | Decoupled: memory backend now private (C only) |
| `MarketplaceStore.crm_leads/crm_deals/crm_tasks/customer_profiles/phone_calls/email_messages/meetings/reminders/interactions` | **A** production-available shadow | Removed from production store |
| `CustomerProfileService._sync_legacy_customer` dual-write to `store.customers` | **A** | Removed |
| HTTP `/customers/{id}/recommendations` reading only `store.customers` | **B** | Delegates to durable CRM first |
| `analytics/service.py` / `health()` CRM counts | already durable snapshot (Sprint 5) | Unchanged |
| `CRMEngine` / Web CRM services | already `get_crm_persistence()` | Unchanged |
| `MemoryCRMPersistence` | **C** | Retained, isolated from MarketplaceStore |
| Foundation `crm/service.py` Lead/Deal/appointment/negotiation/reservation | **D** | Distinct marketplace domain; left |
| `health()["foundation"]["crm"]` | **D** | Foundation CRMService metrics |
| Sprint 13.0 `dashboard.py` AutoDashboard | **D** | Separate dict dashboard (not Web CRM) |
| Dealer CRM `dc_*` / EA CRM `ea_*` | **D** | Untouched |
| Telegram `ClientRequestCrmEngineV1` | **D** | Separate Postgres request CRM |
| Vehicle `maintenance_reminders` | **D** | Untouched |
| `intelligence_profiles` | **D** | Derived analysis cache, not CRM SoT |
| Foundation `store.customers` / `store.leads` / `store.deals` | **D** | Marketplace catalog customers/leads |
| Agro CRM store collections | **D** | Other vertical |
| `store.opportunities` | **E** | Already removed in Sprint 5 |

## Migrated / hardened

- Production `MarketplaceStore` no longer exposes Web CRM collections. Accidental `store.crm_leads.count()` is impossible.
- `MemoryCRMPersistence` keeps isolated `EntityStore` bags used only when `AUTO_CRM_PERSISTENCE=memory`.
- Production default remains PostgreSQL (`AUTO_CRM_PERSISTENCE` unset).
- Web CRM customer create/update/delete no longer shadows `store.customers`.
- Recommendations HTTP path reads durable `CustomerProfile` first, then foundation `store.customers` for marketplace-only customers.

## Adapters retained

- Foundation `CRMService` (buyer requests, appointments, negotiations, reservations, foundation Lead/Deal).
- Sync `recommend_for_customer()` for foundation marketplace customers.
- `CRMMetricsService` snapshot for sync health.

## Test-only memory retained

`MemoryCRMPersistence` behind `AUTO_CRM_PERSISTENCE=memory` (`tests/conftest.py`).

## Non-CRM stores untouched

Vehicles, payments, finance, BI dashboards, portal users, Dealer/EA CRM, Agro, Telegram request CRM, maintenance reminders, intelligence profile cache.

## PostgreSQL source of truth

Production `get_crm_persistence()` returns `PostgresCRMPersistence`. Restart tests collect metrics from a new persistence instance. Overlay test asserts MarketplaceStore has no `crm_leads`/`crm_deals`. Dual-write test asserts a Web CRM customer is absent from `store.customers`.

## Tenant / auth

Existing CRM security tests plus metrics tenant isolation remain green.

## Migration

`MIGRATION_REQUIRED=NO` — Alembic head remains `s8n901234567`.

## Tests

Targeted (75 passed):

- `tests/test_auto_marketplace_crm_metrics.py`
- `tests/test_auto_marketplace_crm_postgres.py`
- `tests/test_auto_marketplace_crm_workflow.py`
- `tests/test_auto_marketplace_crm_communications.py`
- `tests/test_crm_engine.py`
- `tests/test_crm_api_security_40_1.py`

Broader (123 passed, includes targeted): plus BI, portal, API freeze, manager dashboard, CRM foundation.

## Known pre-existing debt

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` 401 under CRM mutation gate

Frontend build was not run: no frontend files changed.
