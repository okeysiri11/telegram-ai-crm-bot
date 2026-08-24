# Sprint Lawyer 3.3 RESULT — Legal External Data / Court Monitoring / Calendar Integration

**Status:** COMPLETE  
**Date:** 2026-08-12  
**Do not start the next sprint automatically.**

---

## FEATURE | STATUS | REAL/MOCK | PROVIDER | LIMITATION

| FEATURE | STATUS | REAL/MOCK | PROVIDER | LIMITATION |
|---------|--------|-----------|----------|------------|
| Nav «Мониторинг» + sub-tabs | **DONE** | REAL UI | — | — |
| LegalDataProvider interface | **DONE** | REAL | registry | — |
| Manual import / check workflow | **DONE** | REAL | `manual_import` | Lawyer-supplied state only |
| ЄДРСР auto fetch | **NOT DONE** | Honest **UNAVAILABLE** | `ua_edrsr` | No public API claimed; no scrape/fake |
| Enforcement auto fetch | **PARTIAL** | Honest **REQUIRES_CONFIGURATION** | `ua_enforcement` | Manual CRUD module ready |
| Watchlist + fingerprint/diff | **DONE** | REAL | manual_import | Diff only on imported state |
| Change Center + dedupe | **DONE** | REAL | — | Unique `(org, dedupe_key)` |
| Automation (calendar/task/AI record) | **DONE** | REAL | — | AI analyze creates analysis only |
| Scheduler jobs 09:00/18:00 Kyiv | **DONE** | REAL hooks | `pg_scheduler_engine` | Cron seeded UTC approx; org settings editable |
| Google Calendar status honesty | **DONE** | REAL | google adapter | — |
| Google OAuth callback + token file | **DONE** | REAL plumbing | google | Secrets server-side |
| Google live Calendar HTTP | **PARTIAL** | Offline adapter default | google | Live when `LEGAL_OPS_GCAL_LIVE=1` + credentials |
| ADOS → Google sync + mapping | **DONE** | Adapter / live flag | google | Bidirectional deferred |
| Google → ADOS / bidirectional | **NOT DONE** | Documented limit | google | Risk/complexity |
| Calendar origin filters | **DONE** | REAL UI | — | ADOS/Google/Court/Deadline |
| AI handoff from change | **DONE** | REAL | Lawyer 3.2 pipeline | No second AI |
| Fake gov registry API | **REJECTED** | — | — | Explicitly not built |

---

## DONE

- Provider architecture with statuses: CONNECTED / REQUIRES_CONFIGURATION / MANUAL / UNAVAILABLE / ERROR
- Watchlist, monitor changes, enforcement, calendar mappings, monitor settings (migration `f5z678901234`)
- Monitoring engine: normalize → fingerprint → diff → persist change → optional automation
- Change Center actions: mark read / task / calendar / AI-анализ
- `pg_scheduler_engine` jobs `legal.monitor.morning` / `legal.monitor.evening` (no second scheduler)
- Google: callback route, token store path, mapping upsert, duplicate prevention on re-sync
- UI Monitoring panel + calendar filters/origin badges
- Tests + smoke evidence `/tmp/sprint_lawyer_3_3_e2e.json`

## PARTIAL

- Live Google Calendar API HTTP (opt-in `LEGAL_OPS_GCAL_LIVE=1`)
- Official UA court/enforcement machine APIs (honest unavailable / needs config)

## NOT DONE (next sprint)

- Contracted ЄДРСР / enforcement data feeds
- Bidirectional Google sync
- Per-tenant encrypted vault for OAuth (file/env today; SecretManager recommended for prod)
- Counterparty external KYC registries

---

## Architectural decisions

| Decision | Choice | Rejected |
|----------|--------|----------|
| External courts | Honest MANUAL/UNAVAILABLE providers + import | Fake «реестр» responses |
| Scheduler | Extend `pg_scheduler_engine` | New Legal-only scheduler |
| Google direction | ADOS → Google first | Full bidirectional in 3.3 |
| AI | Reuse Lawyer 3.2 `/ai/analyze` | Second analyzer |
| Tokens | Server-side env/file | Frontend secrets |

### Official sources assessed (no fake integration)

| Source | Availability | Access | Auth | Limits |
|--------|--------------|--------|------|--------|
| ЄДРСР (reyestr.court.gov.ua) | Public web UI | No free mass API in this sprint | Contract/partner if any | Rate/legal scrape risk — not used |
| Enforcement open data / АСВП | Unclear without contract | Requires configuration | TBD | Module is manual until connected |
| Google Calendar API | Available with OAuth | Official Google API | OAuth2 offline refresh | Quotas; live HTTP gated |

---

## Migrations

- `migrations/versions/f5z678901234_legal_ops_monitor_3_3.py` (revises `e4y567890123`)
- Tables: `legal_ops_watchlist`, `legal_ops_monitor_changes`, `legal_ops_enforcement`, `legal_ops_calendar_mappings`, `legal_ops_monitor_settings`

## API (additive `/api/legal-ops/v1`)

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | sprint **`3.3`** + providers |
| `GET /providers` | Provider catalog + honest status |
| `GET\|POST /monitoring/watchlist` | Watchlist |
| `POST /monitoring/watchlist/{id}/check` | Check now (+ optional imported_state) |
| `GET /monitoring/changes` | Change Center |
| `POST /monitoring/changes/{id}/actions` | Follow-ups |
| `GET\|POST /monitoring/enforcement` | ИП module |
| `GET\|POST /monitoring/settings` | Schedule + Google sync prefs |
| `GET /integrations/google-calendar/callback` | OAuth callback |
| `POST /calendar/{event_id}/sync-google` | Mapped ADOS→Google sync |

## Background jobs

- `legal.monitor.morning` — cron `0 6 * * *` (≈ 09:00 Europe/Kyiv)
- `legal.monitor.evening` — cron `0 15 * * *` (≈ 18:00 Europe/Kyiv)
- Org can store preferred crons in `legal_ops_monitor_settings`

## OAuth / env (no secrets)

```
GOOGLE_CALENDAR_CLIENT_ID=
GOOGLE_CALENDAR_CLIENT_SECRET=
GOOGLE_CALENDAR_REFRESH_TOKEN=
GOOGLE_CALENDAR_REDIRECT_URI=http://127.0.0.1:8080/api/legal-ops/v1/integrations/google-calendar/callback
LEGAL_OPS_GCAL_LIVE=0
LEGAL_OPS_GCAL_TOKEN_PATH=data/legal_ops_gcal_tokens.json
```

Documented in `.env.example`.

## Tests

```bash
.venv/bin/python -m pytest tests/test_sprint_lawyer_3_3_monitoring.py \
  tests/test_sprint_lawyer_3_2_ai.py tests/test_sprint_lawyer_3_1_crm.py \
  tests/test_sprint_51_1_lawyer_desk.py tests/test_sprint_51_0_lawyer_ops.py -q
# 40 passed

cd src/web && npm run test -- sprint_lawyer_3_3_monitoring.test.tsx \
  sprint_lawyer_3_2_ai.test.tsx sprint_51_0_lawyer_desk.test.tsx
# 8 passed
```

## Acceptance smoke

Evidence: `/tmp/sprint_lawyer_3_3_e2e.json`

| Step | Result |
|------|--------|
| Health 3.3 | PASS |
| Providers honest statuses | PASS |
| Case + watchlist | PASS |
| Check now + diff changes | PASS |
| Task / calendar / AI from change | PASS |
| Google status without fake connected | PASS (`needs_config` without creds) |
| Audit actions present | PASS |
| Frontend legal workspace | 200 |

## Production readiness

| Area | Ready? |
|------|--------|
| Monitoring CRM + Change Center | Yes (manual/import) |
| Auto court/enforcement feeds | No — needs official access |
| Google Calendar product sync | Partial — OAuth + mapping ready; enable live flag + credentials |
| Tenant isolation / RBAC / audit | Yes (tests) |
| Resilience | Provider failure returns status + last_error; vertical stays up |

## Local stack (left running)

| Service | URL |
|---------|-----|
| API | http://127.0.0.1:8080 · Legal Ops sprint **3.3** |
| Web | http://localhost:5180/workspace/legal |

Demo: `owner@demo.corp` / `demo`
