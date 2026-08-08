# Sprint 40.3 — Web UI Acceptance & Navigation Validation

**MODE:** FEATURE (Acceptance only)  
**BASELINE:** v0.9.4-rc1  
**Date:** 2026-08-05  
**Status:** COMPLETE  
**Next:** READY FOR SPRINT 40.4

No Docker / CI / architecture / infrastructure changes. UI redesign avoided. Fixes limited to broken routes and nav href alignment.

---

## Pages checked

| Section | Route(s) | Result |
|---------|----------|--------|
| Login | `/login` | PASS (SPA 200) |
| Logout | `/auth/logout` | PASS |
| Unauthorized | `/auth/unauthorized` | PASS |
| Dashboard | `/dashboard` | PASS |
| CRM | `/crm` | PASS |
| Leads | `/crm?view=leads`, alias `/leads` | PASS |
| Clients | `/crm?view=clients`, alias `/clients` | PASS |
| Companies | `/crm?view=companies`, alias `/companies` | PASS |
| Deals | `/crm?view=deals`, alias `/deals` | PASS |
| Tasks | `/tasks` | PASS |
| Calendar | `/calendar` | PASS |
| Reports | alias `/reports` → `/analytics` | PASS (hub; not dedicated report designer) |
| Knowledge | `/knowledge` | PASS |
| AI Agents | `/ai-agents` | PASS |
| AI Studio | `/ai-studio` | PASS |
| Administration | `/admin` | PASS |
| Settings | `/settings` | PASS |
| Profile | `/identity/profile`, alias `/profile` | PASS |
| Notifications | `/notifications` | PASS |
| Marketplace | `/marketplace` | PASS |
| Desktop | `/desktop` | PASS |
| Telegram | Bot live (API); no dedicated `/telegram` SPA page | PARTIAL — channel READY via bot, not a top-level web module |

Probe artifact: `docs/acceptance_40_3_probe.json` · runner: `scripts/acceptance_probe_40_3.py`

---

## Routes checked (aliases)

| From | To | Status |
|------|-----|--------|
| `/deals` | `/crm?view=deals` | Fixed (ACC-40-004) |
| `/clients` | `/crm?view=clients` | Fixed |
| `/companies` | `/crm?view=companies` | Fixed |
| `/leads` | `/crm?view=leads` | Fixed |
| `/reports` | `/analytics` | Fixed |
| `/profile` | `/identity/profile` | Fixed |
| `/workspace/crm` | `/crm` | Fixed (ACC-40-005) |
| `/workspace/erp` | `/erp` | Fixed |
| `/workspace/docs` | `/documents` | Fixed |
| `/workspace/analytics` | `/analytics` | Fixed |
| `/workspace/reports` | `/analytics` | Fixed |

OpenAPI / Swagger: `GET /api/v1/openapi.json` **200**, `GET /api/v1/docs` **200**.  
`GET /api/v1/leads` unauthenticated → **401** (not 501).

Auth: login/logout/unauthorized routes serve; protected hubs remain behind `ProtectedRoute`.

---

## UI issues fixed

1. **ACC-40-004** — Top-level `/deals|/clients|/companies|/reports|/leads` were in-app 404 → `Navigate` aliases in `App.tsx`.
2. **ACC-40-005** — `ENTERPRISE_SHELL_NAV` pointed at `/workspace/crm|erp|docs|analytics` and platform-builder AI/knowledge paths → aligned to canonical `/crm`, `/erp`, `/documents`, `/analytics`, `/ai-studio`, `/ai-agents`, `/knowledge`, `/marketplace`, `/projects`.
3. **ACC-40-009** — Removed Enterprise City `Soon` / `comingSoon` badge from shell nav (catalog already GA).
4. Workspace drift paths `/workspace/crm|erp|docs|analytics|reports` now redirect to hubs before the `:module` catch-all.

---

## Remaining issues

| ID / area | Notes |
|-----------|--------|
| Analytics depth (ACC-40-006) | `/analytics` is a generic hub; no GlobeFly funnel board |
| Dedicated `/reports` product UI | Alias goes to analytics; weekly workspace report shell still secondary |
| Telegram web module | Operator uses bot + notifications; no first-class `/telegram` page |
| Marketing tags (ACC-40-007) | GTM / GA4 / Meta still absent |
| Email/SMTP (ACC-40-008) | Not proven for GlobeFly |
| Deep-link catalogs | Some secondary catalogs (`favoritesManager`, twin, etc.) still mention `/workspace/crm` — covered by redirect, not all rewritten |
| Form/table E2E per page | Acceptance covered routes + aliases + auth surfaces; deep CRUD UI click-through deferred to 40.4+ if needed |

---

## Test / gate summary

| Gate | Result |
|------|--------|
| Vitest nav acceptance (`navigationAcceptance_40_3` + `enterpriseShell`) | **19 passed** |
| Web lint (`tsc -b`) | **PASS** |
| Web build | **PASS** (dist refreshed for nginx) |
| Ruff (probe script) | **PASS** |
| RC suite | **64 passed** |
| Smoke | **32/32 PASS** |
| `/health` `/ready` | **200** |
| Acceptance UI probe checks | **all true** |

---

## Files changed

| File | Change |
|------|--------|
| `src/web/src/App.tsx` | Alias + workspace redirects |
| `src/web/src/shell/enterprise/enterpriseNav.ts` | Canonical shell routes; City Soon removed |
| `src/web/src/shell/enterprise/navigationAcceptance_40_3.test.tsx` | **New** feature tests |
| `scripts/acceptance_probe_40_3.py` | **New** probe |
| `docs/acceptance_40_3_probe.json` | Probe output |
| `docs/SPRINT_40_3_RESULT.md` | This report |
| `docs/GLOBEFLY_READINESS.md` | Nav/route status update |

---

## Readiness percentage

| Lens | ~Score |
|------|-------:|
| After 40.2 (CRM API foundation) | ~82% |
| After 40.3 (nav + route acceptance) | **~88%** |

Operator navigation for CRM/leads/clients/deals/reports aliases is consistent with hubs. Remaining GlobeFly gap is mostly marketing tags, SMTP proof, and analytics depth.

---

**STATUS: SPRINT 40.3 COMPLETE**  
**READY FOR SPRINT 40.4**
