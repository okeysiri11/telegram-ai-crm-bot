# GlobeFly Readiness — Sprint 40.0 / updated through 41.1

**Client:** GlobeFly (first commercial onboarding candidate)  
**Platform baseline:** `v0.9.4-rc1`  
**Date:** 2026-08-06  
**MODE:** FEATURE (40.0–40.3) + AUTH FIX (40.4) + FIRST CLIENT UX (41.1)

This checklist answers: *can we connect the GlobeFly website/traffic to ADOS today?*  
**UX journey (41.1):** see [`docs/SPRINT_41_1_FIRST_CLIENT_JOURNEY.md`](SPRINT_41_1_FIRST_CLIENT_JOURNEY.md).

Status values: **READY** · **PARTIAL** · **NOT READY**

**Sprint 40.1:** ACC-40-001 / ACC-40-003 fixed.  
**Sprint 40.2:** Public `/api/v1/leads|clients|reports|crm/deals` live.  
**Sprint 40.3:** ACC-40-004/005/009 nav+route aliases fixed. See `docs/SPRINT_40_3_RESULT.md`.  
**Sprint 40.4:** ISAM opaque session / login redirect loop fixed. See `docs/SPRINT_40_4_RESULT.md`.  
**Sprint 41.1:** View Modes + GlobeFly demo Client journey + RU Client chrome. Demo login: `client@globefly.demo` / `demo`.

---

## Checklist

| Capability | Status | Notes |
|------------|--------|-------|
| CRM | READY | UI `/crm` (+ aliases `/deals|/clients|/companies|/leads`); shell nav uses `/crm` (40.3). API auth on mutating auto CRM (40.1). |
| Pipeline | READY | `GET /api/auto/v1/crm/pipeline` returns stages; CRM has pipelines tab. |
| Leads | READY | Public `/api/v1/leads` CRUD (40.2); UI `/crm?view=leads` + `/leads` alias (40.3). |
| Deals | READY | Create/list via `/api/auto/v1/crm/deals`; UI `/crm?view=deals` + `/deals` alias. |
| Contacts | READY | Customers API + CRM clients/contacts tabs (`/crm?view=clients`). |
| Tasks | READY | `/tasks` UI + `/api/auto/v1/crm/tasks` create/list. |
| Documents | PARTIAL | `/documents` route exists (Drive module). Public `/api/v1/documents` requires auth; GlobeFly upload path not acceptance-proven end-to-end. |
| Analytics | PARTIAL | `/analytics` hub; `/reports` aliases here (40.3). Not a dedicated GlobeFly funnel board. |
| UTM | PARTIAL | UTM fields exist in lead/marketing engines; website→API mapping for GlobeFly not wired/documented as a turnkey connector. |
| Webhook | PARTIAL | Management integrations + inbound `POST /integrations/inbound/{webhook_id}` exist; requires auth/config. Not GlobeFly-specific. |
| Telegram | READY | Live bot `@UnoCachio_bot` polling; getMe/OWNER chat validated in Sprint 39.1. |
| Email | PARTIAL | SMTP connector present; outbound not confirmed configured for GlobeFly. |
| AI | READY | `/ai-agents`, `/ai-studio` routes; OpenRouter hub path available via ENV. |
| Dashboard | READY | `/dashboard` (+ role dashboards) served; stack healthy. |
| Google Tag Manager | NOT READY | No GTM integration in frontend/repo. |
| Meta Pixel | NOT READY | No Meta Pixel / `fbq` integration found. |
| GA4 | NOT READY | No GA4 / gtag integration found. |

---

## Recommended GlobeFly integration path (when FIX REQUIRED items clear)

1. Website forms → authenticated webhook or `/api/auto/v1/crm/leads` with validated `source` + UTM fields.  
2. Secure CRM API (gateway API key / JWT) before public internet exposure.  
3. Telegram notifications for new leads (existing bot).  
4. Add GTM/GA4/Meta on the **GlobeFly site** (marketing) and optionally mirror events into ADOS webhooks.  
5. Operator UI: `/crm?view=leads|deals|clients` (canonical); top-level `/leads|/deals|/clients|/reports` redirect correctly (40.3).

---

## Blocking for commercial go-live

1. ~~**ACC-40-001** — invalid lead source → 500~~ **FIXED in 40.1** (→ 400)  
2. ~~**ACC-40-003** — unauthenticated CRM writes~~ **FIXED in 40.1** (→ 401)  
3. ~~**ACC-40-004 / 005 / 009** — route aliases + shell nav drift + City Soon~~ **FIXED in 40.3**  
4. Marketing tags (GTM/GA4/Meta) if GlobeFly requires them **inside** ADOS web (else own site)  
5. Analytics/report depth (ACC-40-006) and SMTP proof (ACC-40-008)

---

## Summary score (GlobeFly-specific)

| READY | PARTIAL | NOT READY |
|------:|--------:|----------:|
| 11 | 5 | 3 |

**Recommendation (after 41.1):** Operator **Client View Mode** + GlobeFly demo tenant are ready for a **guided pilot** (~**86%** UX journey). Public CRM APIs remain in place from 40.2. Remaining for unsupervised commercial READY: documents E2E, analytics depth, marketing tags, SMTP proof.
