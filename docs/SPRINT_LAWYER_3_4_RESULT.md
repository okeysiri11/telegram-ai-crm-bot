# SPRINT LAWYER 3.4 — RESULT

## Status

**COMPLETE** — Manual/Import monitoring, Change Center workflow, Integrations Health, safe automation defaults, URL/SSRF guards, audit events. No fake court/enforcement registry data. Google Calendar remains honest `needs_config` without admin OAuth.

## Architecture reused

- Extended `services/legal_ops/` (3.1 CRM + 3.2 AI + 3.3 monitoring) — no new vertical, no second scheduler
- Fingerprint / normalize / diff from `services/legal_ops/providers.py` (Lawyer 3.3)
- Scheduler jobs `legal.monitor.morning` / `legal.monitor.evening` on existing `pg_scheduler_engine`
- Google adapter `services/legal_ops/google_calendar.py` + mapping table (ADOS → Google only)
- UI: existing EDS/`@/ui` + Lawyer cabinet patterns (no second design system)

## Files changed

### Backend
- `services/legal_ops/monitoring.py` — manual watch fields, change workflow, automation suggestions, integration health, audit names, scrub secrets
- `services/legal_ops/url_safety.py` — HTTPS URL validation + SSRF guards (`FETCH_USER_URLS=False`)
- `services/legal_ops/google_calendar.py` — `clear_org_refresh_token`
- `services/legal_ops/providers.py` — honest UNAVAILABLE / REQUIRES_CONFIGURATION messages
- `services/legal_ops/service.py` — scrubbed `gcal_status`
- `services/legal_ops/desk_ops.py` — watch/change field lists
- `repositories/legal_ops_repository.py` — persist new columns
- `database/models/legal_ops.py` — additive columns
- `applications/legal_enterprise/api/ops_handlers.py` — health sprint `3.4`, health/disconnect/watch update, OAuth state guard
- `applications/legal_enterprise/api/register.py` — new routes

### Frontend
- `src/web/workspace/legal/LawyerMonitoringPanel.tsx` — manual form, Change Center detail/actions, IntegrationHealthCard
- `src/web/workspace/legal/LawyerBusinessPage.tsx` — Settings → Integrations health

### Tests / docs
- `tests/test_sprint_lawyer_3_4.py`
- `src/web/workspace/legal/sprint_lawyer_3_4.test.tsx`
- Health asserts in 3.1–3.3 tests accept sprint `3.4`
- `docs/SPRINT_LAWYER_3_4_RESULT.md` (this file)

## Migrations

- `migrations/versions/h7c890123456_legal_ops_monitor_3_4.py` (revises `f5z678901234`)
  - Watchlist: `title`, `source_url`, `check_frequency`, `comment`, `counterparty`, `decision_ref`, `enforcement_id`, `active`
  - Changes: `workflow_status`, `summary`, `old_fingerprint`, `new_fingerprint`, `source_reference`, `enforcement_id`, `suggestions`

## New endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/legal-ops/v1/integrations/health` | Integration health dashboard |
| POST | `/api/legal-ops/v1/integrations/google-calendar/disconnect` | Clear org Google token |
| POST | `/api/legal-ops/v1/monitoring/watchlist/{id}` | Update / disable watch item |

Existing: watchlist create/check, changes actions, GCal connect/callback/status, providers, monitoring settings.

## New UI

- **Мониторинг → Судебные дела**: full Manual/Import form (тип, название, идентификатор, URL, частота, комментарий, активен) + Сохранить / Проверить сейчас
- **Мониторинг → Изменения**: statuses Новое / Просмотрено / Требует действия / Закрыто; detail + handoffs (задача, календарь, AI-юрист, просмотрено)
- **Настройки → СОСТОЯНИЕ ИНТЕГРАЦИЙ**: Google / судебные данные / ИП / контрагенты / Scheduler with text + icon status, last sync, errors 24h

## Google integration state

- Without admin credentials: `needs_config` / UI «Не настроен администратором»
- OAuth client without refresh: `needs_oauth`
- Tokens: server-side file/env only; scrubbed from API; never logged
- Sync direction: **ADOS → Google** only; bidirectional rejected
- Live HTTP: only with `LEGAL_OPS_GCAL_LIVE=1`
- ADOS calendar works without Google (fail-safe)

## Legal provider state

| Provider | Status |
|----------|--------|
| `manual_import` | MANUAL — fully usable |
| `ua_edrsr` | UNAVAILABLE — no fake data |
| `ua_enforcement` | REQUIRES_CONFIGURATION — no fake data |
| counterparties check | UNAVAILABLE |

User-provided source URLs are validated (HTTPS, SSRF blocklist) and stored as references — **not fetched** in production (`FETCH_USER_URLS=False`).

## Scheduler jobs

- Reuses `legal.monitor.morning` / `legal.monitor.evening`
- Flow: check → normalize → fingerprint → compare → `LegalChangeEvent` or update `checked_at` only

## Security checks

- Tenant isolation on watchlist/changes
- RBAC via existing legal_ops roles
- External API calls server-side only
- OAuth tokens never in frontend / API output (`scrub_secrets`)
- OAuth callback rejects unsafe `state` (`://`, `..`)
- Manual URL validation + SSRF guards
- No arbitrary website scraping

## Audit events

`GOOGLE_CONNECTED`, `GOOGLE_DISCONNECTED`, `GOOGLE_SYNC`, `GOOGLE_SYNC_FAILED`, `LEGAL_PROVIDER_CHECK`, `LEGAL_CHANGE_DETECTED`, `WATCH_ITEM_CREATED`, `WATCH_ITEM_UPDATED`, `WATCH_ITEM_DISABLED` (+ existing activity stream). Metadata only — no tokens.

## Tests

- Backend: `tests/test_sprint_lawyer_3_4.py` (+ 3.1–3.3 regression) — **36 passed**
- Frontend: `sprint_lawyer_3_4.test.tsx` (+ 3.3) — Integrations health + watch form
- Mocks only in tests; no real Google credentials required for CI

## Manual acceptance

| Flow | Expected |
|------|----------|
| A — Google not configured | Settings shows «Не настроен администратором», no crash |
| B — Local calendar | Заседание appears in ADOS calendar without Google |
| C — Monitoring | Manual watch + Проверить сейчас → Change Center on diff |
| D — Handoffs | Создать задачу / календарь / AI-юрист / просмотрено |

## Known limitations

- Google → ADOS / bidirectional sync not enabled (conflict risk)
- No live court/enforcement registries until contracted providers configured
- Manual URL is reference-only (no scrape)
- Automation defaults: notify + suggest; no auto calendar / auto AI unless explicitly enabled

## External credentials still required

- Google OAuth client id/secret (+ refresh or OAuth code exchange)
- Official/licensed court & enforcement data providers (when available)

## Next recommended sprint

**LAWYER 3.5** (not started): contracted provider adapters, optional Google→ADOS with conflict UX, bounded fetch provider design if product approves.

---

**STOP AFTER LAWYER 3.4.**
