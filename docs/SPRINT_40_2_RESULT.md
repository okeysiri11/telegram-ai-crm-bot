# Sprint 40.2 — CRM Foundation Completion

**MODE:** FEATURE  
**BASELINE:** v0.9.4-rc1  
**Date:** 2026-08-05  
**Status:** COMPLETE  
**Next:** READY FOR SPRINT 40.3

Infrastructure / Docker / CI / compose / architecture were **not** modified.

---

## Implemented endpoints

### Leads — `/api/v1/leads` (ACC-40-002 closed)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/leads` | Pagination, filter (`status`, `source`, `dealer_id`, `customer_id`), sort |
| GET | `/api/v1/leads/{lead_id}` | 404 when missing |
| POST | `/api/v1/leads` | Validates `LeadSource`; UTM fields → metadata; **201** |
| PATCH | `/api/v1/leads/{lead_id}` | Partial update |
| DELETE | `/api/v1/leads/{lead_id}` | Hard delete via CRM store |

### Clients — `/api/v1/clients`

| Method | Path | Notes |
|--------|------|-------|
| GET/POST | `/api/v1/clients` | List (segment/email filter) / create |
| GET/PATCH/DELETE | `/api/v1/clients/{client_id}` | Full CRUD; `client_id` alias of `customer_id` |

### Deals

**Exchange deals** (existing `DealWorkflowService` — additive CRUD):

| Method | Path |
|--------|------|
| GET/POST | `/api/v1/deals` (existing) |
| GET/PATCH/DELETE | `/api/v1/deals/{deal_id}` — get / status update / soft-cancel (`CANCELLED`) |

**CRM sales deals** (GlobeFly pipeline — does not replace exchange deals):

| Method | Path |
|--------|------|
| GET/POST | `/api/v1/crm/deals` |
| GET/PATCH/DELETE | `/api/v1/crm/deals/{deal_id}` |

### Reports — `/api/v1/reports`

| Method | Path | Payload |
|--------|------|---------|
| GET | `/api/v1/reports` | Catalog: `pipeline`, `forecast`, `conversion`, `crm-metrics` |
| GET | `/api/v1/reports/{report_id}` | Live CRM engine analytics (no placeholders) |

### Auth / RBAC / OpenAPI

- All mutating + list/get CRM foundation routes use `require_api_auth`.
- Gateway permissions: `lead.*`, `client.*`, `deal.*`, `report.read` (defaults updated).
- Paths recorded in public OpenAPI → `/api/v1/openapi.json` + Swagger UI `/api/v1/docs`.

Bridge: `api/v1/crm_foundation.py` → `auto_marketplace.crm_engine` (extend existing services; `delete`/`update` added on Lead/Customer/Deal services).

---

## Remaining TODOs (out of 40.2 scope)

| Item | Notes |
|------|-------|
| `/api/v1/managers`, `/inventory/crm`, `/analytics/crm` | Still **501** reserved stubs |
| App shell routes `/deals` `/clients` `/reports` (ACC-40-004) | Frontend routing — Sprint 40.3+ |
| Nav drift `/workspace/*` vs `/crm` (ACC-40-005) | UI |
| GTM / GA4 / Meta Pixel (ACC-40-007) | Marketing |
| SMTP proof (ACC-40-008) | Ops |
| Postgres-backed CRM persistence | Engine remains in-memory marketplace store (existing design) |

---

## Test summary

| Suite | Result |
|-------|--------|
| `tests/test_crm_foundation_40_2.py` | **8 passed** (CRUD, validation, RBAC 403, OpenAPI, docs, no 501) |
| CRM regression (`test_crm_api_security_40_1` + foundation) | **25 passed** |
| RC suite | **64 passed** |
| API v1 freeze | green (included in RC) |

---

## PASS/FAIL gates

| Gate | Result |
|------|--------|
| Ruff (touched files) | **PASS** |
| Unit / feature tests (40.2) | **PASS** |
| CRM regression | **PASS** |
| RC | **PASS** (64) |
| Smoke | **PASS** (32/32) |
| `/health` | **PASS** 200 |
| `/ready` | **PASS** 200 |
| Swagger `/api/v1/docs` | **PASS** 200 |
| OpenAPI includes leads/clients/reports/crm/deals | **PASS** |
| `GET /api/v1/leads` unauthenticated | **401** (not 501) |

---

## Files changed

| File | Role |
|------|------|
| `api/v1/crm_foundation.py` | **New** CRM public handlers |
| `api/v1/public_router.py` | Route + OpenAPI registration |
| `api/v1/__init__.py` | Removed leads/clients from 501 stubs |
| `api/handlers.py` | Exchange deal GET/PATCH/DELETE |
| `applications/auto_marketplace/leads/service.py` | `delete` |
| `applications/auto_marketplace/customers/profile_service.py` | `delete` |
| `applications/auto_marketplace/deals/service.py` | `update`, `delete` |
| `services/pg_api_gateway_engine.py` | CRM permissions + path normalization |
| `tests/test_crm_foundation_40_2.py` | **New** feature tests |
| `docs/API_MAP.md` | Route map update |
| `docs/SPRINT_40_2_RESULT.md` | This report |

---

## Architectural decisions

1. **Extend** Auto Marketplace CRM engine behind `/api/v1` instead of a new `platform_*` package.
2. Keep **exchange** `/api/v1/deals` semantics; add **CRM** deals at `/api/v1/crm/deals` to avoid breaking the frozen exchange contract.
3. Reports are real CRM pipeline/forecast/conversion/metrics — not stub strings.

---

## GlobeFly readiness

| Lens | ~Score |
|------|-------:|
| After 40.1 (Critical API safety) | ~70% |
| After 40.2 (public CRM foundation) | **~82%** |

Public leads/clients/reports no longer 501; authenticated CRM API is usable for GlobeFly connectors. Remaining gap is primarily UX routes, marketing tags, and email proof.

---

**STATUS: SPRINT 40.2 COMPLETE**  
**READY FOR SPRINT 40.3**
