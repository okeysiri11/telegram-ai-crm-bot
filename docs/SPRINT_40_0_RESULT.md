# Sprint 40.0 — Platform Acceptance & GlobeFly Readiness

**MODE:** FEATURE (acceptance / documentation only)  
**BASELINE:** v0.9.4-rc1  
**Date:** 2026-08-05  
**Status:** COMPLETE  
**Client recommendation:** **FIX REQUIRED** (controlled pilot possible after Critical fixes)

No architecture, Docker, CI, or infrastructure code was changed. Bugs were **recorded**, not fixed.

---

## What was checked

### Startup
- All compose services Healthy (postgres, redis, bot, nginx, grafana, prometheus)
- `GET /health` → 200 healthy
- `GET /ready` → 200 ready

### WEB acceptance (route presence via nginx SPA)

| Area | Result |
|------|--------|
| Login `/login` | PASS (shell serves) |
| Logout `/auth/logout` | PASS |
| Dashboard `/dashboard` | PASS |
| CRM `/crm` | PASS |
| Deals `/crm?view=deals` | PASS (canonical) |
| Clients `/crm?view=clients` | PASS |
| Companies `/crm?view=companies` | PASS |
| Tasks `/tasks` | PASS |
| Calendar `/calendar` | PASS |
| AI `/ai-agents` | PASS |
| Knowledge `/knowledge` | PASS |
| Documents `/documents` | PASS |
| Reports | FAIL as `/reports` (404 in-app); PARTIAL via `/workspace/reports/weekly` |
| Analytics `/analytics` | PARTIAL (generic hub page) |
| Notifications `/notifications` | PASS |
| Settings `/settings` | PASS |

Probe artifact: `docs/acceptance_40_0_probe.json` · runner: `scripts/acceptance_probe_40_0.py`

### API acceptance

| Check | Result |
|-------|--------|
| Auto CRM GET customers/leads/deals/pipeline/tasks | 200 |
| POST deal/customer/task | 201 |
| POST lead (`source=web` + UTM) | 201 |
| POST lead invalid source | **500** (bug) |
| `/api/v1/leads` | **501** |
| `/api/v1/deals` unauthenticated | 401 (expected) |
| `/management/v1/*` unauthenticated | 401 (expected) |
| Unknown path | 404 |

### GlobeFly checklist
See `docs/GLOBEFLY_READINESS.md` — **6 READY / 8 PARTIAL / 3 NOT READY**.

---

## Bug list (not fixed)

### Critical
| ID | Summary |
|----|---------|
| ACC-40-001 | Invalid `LeadSource` on create lead → HTTP **500** instead of 400 |
| ACC-40-003 | `/api/auto/v1/crm/*` writes succeed **without authentication** |

### Major
| ID | Summary |
|----|---------|
| ACC-40-002 | `/api/v1/leads` reserved 501; real API is auto CRM |
| ACC-40-004 | `/deals` `/clients` `/companies` `/reports` not App routes → in-app 404 |
| ACC-40-005 | Shell nav `/workspace/*` vs catalog `/crm` path drift |
| ACC-40-006 | Analytics/reports UX incomplete for operators |
| ACC-40-007 | No GTM / GA4 / Meta Pixel in platform web |

### Minor
| ID | Summary |
|----|---------|
| ACC-40-008 | Email/SMTP not proven configured for GlobeFly |

### Cosmetic
| ID | Summary |
|----|---------|
| ACC-40-009 | City “coming soon” badge inconsistency in shell nav |

---

## Passed vs failed (summary)

| Passed | Failed / incomplete |
|--------|---------------------|
| Infrastructure startup & health | Lead validation error handling |
| Core CRM deals/contacts/tasks APIs | CRM API auth for public exposure |
| Telegram readiness (prior sprint) | Marketing tags (GTM/GA4/Meta) |
| Dashboard / CRM / Tasks / Calendar / AI / Knowledge / Documents / Notifications / Settings routes | Dedicated reports route; analytics depth |
| Auth required on `/api/v1` & `/management/v1` | Top-level alias routes for deals/clients |

---

## Platform readiness

| Lens | Score |
|------|------:|
| Infrastructure (from 39.1) | ~96% |
| Operator WEB acceptance | ~78% |
| GlobeFly commercial connect | ~62% |
| **Overall for first-client go-live** | **~70%** |

**Recommendation:** **FIX REQUIRED**  
Do **not** expose auto CRM publicly until ACC-40-001 and ACC-40-003 are resolved (BUGFIX sprint).  
A **closed pilot** (VPN / authenticated operators only) can proceed using `/crm` + Telegram.

---

## End-of-sprint gates

| Gate | Result |
|------|--------|
| Ruff | PASS |
| RC | 64 passed |
| Smoke | 32/32 PASS |
| Compose Healthy | PASS |
| `/health` | 200 |
| `/ready` | 200 |

**STATUS: SPRINT 40.0 COMPLETE**

## Files added

- `docs/GLOBEFLY_READINESS.md`
- `docs/SPRINT_40_0_RESULT.md`
- `docs/acceptance_40_0_probe.json`
- `scripts/acceptance_probe_40_0.py`
