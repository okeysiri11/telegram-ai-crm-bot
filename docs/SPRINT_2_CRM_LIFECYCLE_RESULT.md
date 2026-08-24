# Sprint 2 — Auto Marketplace CRM Production CRUD + Lifecycle

## What shipped

Production Web Auto CRM (`/api/auto/v1/crm` and frozen `/api/v1` leads/clients/crm deals) now has a complete repository-backed lifecycle for leads, customers, and deals. PostgreSQL remains the production source of truth (Sprint 1 persistence). Tests continue to use `AUTO_CRM_PERSISTENCE=memory`.

Additive Auto CRM routes (existing POST/qualify/advance/win/lose unchanged):

- GET/PATCH/DELETE `/api/auto/v1/crm/leads/{lead_id}`
- POST `/api/auto/v1/crm/leads/{lead_id}/convert`
- PATCH/DELETE `/api/auto/v1/crm/customers/{customer_id}`
- GET/PATCH/DELETE `/api/auto/v1/crm/deals/{deal_id}`

Lead → deal conversion is durable and idempotent via existing `lead.metadata["converted_deal_id"]`. No public schema fields were added. No Alembic migration.

## Architectural decisions

- **No second CRM / pipeline store.** Deals remain the durable pipeline; in-memory `opportunities` stay compatibility/cache.
- **No schema change.** Cross-entity link uses existing JSONB `metadata` instead of a `lead_id` column on deals.
- **Category A memory paths replaced.** Portal, auth registration, lead intelligence, customer intelligence, KPI/analytics/statistics/forecasting/visualizations/executive dashboard now read/write CRM through `get_crm_persistence()`.
- **Left in place:** `MemoryCRMPersistence` (tests), `crm/service.py` foundation `Lead` (different domain), `application.py` store counts (compatibility dashboard overlay), MarketplaceStore collections themselves.

## Intentionally deferred

- Dual-write of CRM entities into MarketplaceStore for the application health dump
- Telegram CRM (`ClientRequestCrmEngineV1`) — separate domain; regression-tested only
- Stale Alembic head pin in `tests/test_database_stabilization_37_1.py` (Sprint 48.1)
