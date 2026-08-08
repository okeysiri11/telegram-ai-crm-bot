# Sprint 40.1 — Critical Readiness Fixes

**MODE:** BUGFIX  
**BASELINE:** v0.9.4-rc1  
**Date:** 2026-08-05  
**Status:** COMPLETE  
**Next:** READY FOR SPRINT 40.2

No architecture, Docker, CI, or infrastructure code was changed. Scope limited to ACC-40-001 and ACC-40-003.

---

## 1. Root causes

### BUG 1 — ACC-40-001 (`LeadSource` → HTTP 500)

**Cause:** `CRMLead(source=LeadSource(raw))` raised bare `ValueError` on invalid enum values. `crm_error_middleware` existed in code but was **never registered** on the aiohttp app, so validation failures surfaced as unhandled 500.

**Fix:**
- Parse source via `_parse_lead_source()` → `ValidationError` (HTTP 400).
- Register `crm_error_middleware` (maps `ValidationError`/`ValueError` → 400, `NotFoundError` → 404, auth errors → 401/403).
- Same safe parsing for lead status / deal stage query filters.

### BUG 2 — ACC-40-003 (CRM POST without auth → 201)

**Cause:** `_check_perm` treated missing `principal` as `{}` and defaulted role to `SALES_AGENT`, so unauthenticated mutating calls were authorized.

**Fix:**
- Mutating permissions (`.write` / `.manage` / `.create` / `.update` / `.delete`) require `principal["authenticated"]` or raise `AuthenticationError` (401).
- `crm_mutating_auth_middleware` gates **all** `POST|PUT|PATCH|DELETE` under `/api/auto/v1/crm` (engine + foundation routes).
- GET remains under existing read policy (no new auth requirement).

---

## 2. Files changed

| File | Change |
|------|--------|
| `applications/auto_marketplace/shared/exceptions.py` | Added `AuthenticationError` |
| `applications/auto_marketplace/api/crm_handlers.py` | LeadSource parse; mutating auth in `_check_perm`; CRM error + mutating-auth middlewares |
| `applications/auto_marketplace/api/register.py` | Register CRM middlewares (error → auth → mutating gate) |
| `tests/test_crm_api_security_40_1.py` | **New** — unit/integration coverage for both bugs |
| `docs/SPRINT_40_1_RESULT.md` | This report |

---

## 3. Tests added

`tests/test_crm_api_security_40_1.py`:

- Invalid `LeadSource` → **400**
- Valid `LeadSource` + Bearer → **201**
- Missing lead (`next-action`) → **404**
- Unauthenticated qualify → **401**
- Parametrized unauthenticated POST (leads/deals/customers/tasks/activities/calendar + foundation requests/appointments/negotiations/reservations) → **401**
- GET pipeline without auth still **200** (current read policy)
- Invalid deal stage filter → **400**

Regression: `tests/test_crm_engine.py` (incl. `test_crm_api_create_lead` with Bearer) — green.

---

## 4. Checks performed

| Gate | Result |
|------|--------|
| Ruff (touched CRM files) | PASS |
| pytest BUGFIX (`test_crm_api_security_40_1` + `test_crm_engine`) | **27 passed** |
| RC suite (`scripts/run_rc_test_suite.py`) | **63 passed**, 1 skipped |
| Smoke (`scripts/smoke_platform_rc.py --skip-down --no-rebuild`) | **32/32 PASS** |
| `docker compose up --build -d bot` | PASS (image rebuilt with fixes) |
| Compose services Healthy | PASS |
| `GET /health` | **200** |
| `GET /ready` | **200** |

### Live verification (post-rebuild)

| Probe | Result |
|-------|--------|
| `POST /api/auto/v1/crm/{leads,deals,customers,tasks,requests}` without `Authorization` | **401** `Authentication required` |
| Isolated auto-CRM app (same handlers/middleware as registered): invalid source + Bearer | **400** |
| Isolated: valid source + Bearer | **201** |
| Isolated: missing lead next-action | **404** |

Note: Full-stack `Authorization: Bearer <non-IAM JWT>` is rejected by **platform_builder** identity middleware (`authentication_required`) before the handler — that is pre-existing global auth behavior, not a regression of these two bugs. Handler-level LeadSource/404 mapping is covered by pytest + in-container isolated registration.

---

## 5. Remaining until GlobeFly

Critical blockers from Sprint 40.0 for CRM public exposure are **closed**.

Still open (Major / Minor from 40.0 — **not** in 40.1 scope):

| ID | Item |
|----|------|
| ACC-40-002 | `/api/v1/leads` reserved 501 vs auto CRM path |
| ACC-40-004 | Top-level `/deals` `/clients` `/companies` `/reports` App routes |
| ACC-40-005 | Shell nav `/workspace/*` vs `/crm` path drift |
| ACC-40-006 | Analytics/reports operator UX |
| ACC-40-007 | GTM / GA4 / Meta Pixel |
| ACC-40-008 | Email/SMTP proof for GlobeFly |
| ACC-40-009 | City “coming soon” nav badge consistency |

See `docs/GLOBEFLY_READINESS.md` for the commercial checklist. Next sprint should continue product/readiness work (40.2+), not re-open these Critical API bugs.

---

## Architectural decisions

- **Extend** existing CRM handlers/middleware; no new packages.
- Global CRM mutating gate scoped to `/api/auto/v1/crm` only (webhooks / dealer-crm prefixes untouched).
- `AuthenticationError` added beside existing `AuthorizationError` (401 vs 403).

---

## End-of-sprint gates

| Gate | Result |
|------|--------|
| Ruff | PASS |
| RC | 63 passed, 1 skipped |
| Smoke | 32/32 PASS |
| Compose Healthy | PASS |
| `/health` | 200 |
| `/ready` | 200 |
| BUGFIX pytest | 27 passed |

**STATUS: SPRINT 40.1 COMPLETE**  
**READY FOR SPRINT 40.2**
