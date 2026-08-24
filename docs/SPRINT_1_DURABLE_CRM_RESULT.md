# Sprint 1 Durable CRM — result

**Branch:** `develop`
**Start HEAD:** `6862278bcc783981041d4ddc4d0d979f5445bf51`
**Commit:** not created (working tree left for human review)

## What shipped

Web Auto CRM (`/api/auto/v1/crm` and frozen `/api/v1` leads/clients/crm deals) now uses **PostgreSQL** as the production source of truth for customers, leads, and deals.

- Production default backend is Postgres (`AUTO_CRM_PERSISTENCE` unset).
- Isolated unit tests keep `AUTO_CRM_PERSISTENCE=memory` via `tests/conftest.py`.
- Tenant scoping is applied on every CRM read/write (`tenant_id`, default `"default"`).
- Restart durability is demonstrated: save → dispose engine → new session still returns the same rows.

Telegram CRM (`ClientRequestCrmEngineV1` / `client_requests`) was not modified.

## Architectural decisions

1. **Extend Auto Marketplace CRM services; do not create a new `platform_*` package.** The Web CRM already lived in `applications/auto_marketplace/{leads,deals,customers}`. Persistence was added under those services plus `repositories/auto_marketplace_crm_repository.py`.
2. **Do not merge Telegram CRM and Web Auto CRM tables.** They are different domains. Dual CRM remains: Telegram stays on `client_requests`; Web Auto CRM uses `auto_marketplace_crm_*`.
3. **In-memory `MarketplaceStore` remains for non-CRM collections** (vehicles, tasks, opportunities). Only `customer_profiles` / `crm_leads` / `crm_deals` moved off the production path.
4. **API contract is additive-only.** Response shapes (`customer_id`, `lead_id`, `deal_id`, `to_dict()`) are unchanged. Tenant is taken from principal / `X-Tenant-Id`, never required in JSON bodies.
5. **Rejected:** silent Postgres → memory fallback in production. Missing Postgres must fail rather than lose data.

## Tables

- `auto_marketplace_crm_customers`
- `auto_marketplace_crm_leads`
- `auto_marketplace_crm_deals`

Migration: `migrations/versions/q6l789012345_auto_marketplace_crm.py` (revises `p5k678901234`).

## Remaining risks

- Dealer portal / analytics / lead-intelligence modules still read `MarketplaceStore` CRM collections (not the `/api/auto/v1/crm` HTTP path).
- CRM tasks, opportunities, and communications remain in-memory.
- `PlatformBridge.authenticate_request` still does not emit `tenant_id`; isolation uses `"default"` unless a principal/header supplies it.
- Apply `alembic upgrade head` on each environment before production traffic hits the new tables.
