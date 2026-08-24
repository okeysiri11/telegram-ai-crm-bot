# SPRINT LAWYER 3.5 — RESULT

## Status

**COMPLETE**

Production UX polish for Lawyer desk: attachments actions, CRUD consistency, calendar Month/Week/Day detail, Settings → Источники данных, ADOS notifications for legal changes, Russian copy, scheduler noise fix. No fake court/enforcement data. No new parallel storage/scheduler.

## Implemented

- Attachments on CRM cards: filename / type / size / uploaded_at / linked entity; Открыть, Скачать, Переименовать, Перепривязать, Удалить (soft archive + confirm)
- File rename API; link validation for client/case/contract/document/task/hearing/enforcement/ai_analysis
- Global CRUD: consistent Открыть / Изменить / Удалить; confirm «Удалить объект?» with soft archive
- Watch edit / pause / delete; enforcement update / archive
- Calendar: Месяц / Неделя / День (+ повестка); filters including Договоры; event detail card; sync / related object actions
- Settings → Источники данных (honest statuses, no secrets)
- Monitoring morning/evening reuses existing jobs; scheduler no longer overwrites last import with noisy metadata
- Meaningful changes → Lawyer notifications + `LEGAL_MONITOR_CHANGE` platform event + NotificationCenter push stub; deeplink to monitoring
- Russian UI pass on calendar/monitoring/settings

## Modified files

### Backend
- `services/legal_ops/notifications.py` (new)
- `services/legal_ops/monitoring.py`
- `services/legal_ops/desk_ops.py`
- `services/legal_ops/service.py`
- `applications/legal_enterprise/api/ops_handlers.py`
- `applications/legal_enterprise/api/register.py`

### Frontend
- `src/web/workspace/legal/LawyerCalendarBoard.tsx`
- `src/web/workspace/legal/LawyerMonitoringPanel.tsx`
- `src/web/workspace/legal/LawyerBusinessPage.tsx`
- `src/web/workspace/legal/LawyerRowMenu.tsx`
- `src/web/workspace/legal/lawyerLabels.ts`

### Tests / docs
- `tests/test_sprint_lawyer_3_5.py`
- `src/web/workspace/legal/sprint_lawyer_3_5.test.tsx`
- Health asserts 3.1–3.4 accept sprint `3.5`
- `docs/SPRINT_LAWYER_3_5_RESULT.md`

## Database changes

**None.** Reused Lawyer 3.1–3.4 schema (head `h7c890123456`). Notifications are org-bag / activity + platform events (no duplicate table).

## API endpoints

| Method | Path | Notes |
|--------|------|-------|
| POST | `/files/{id}/rename` | Rename attachment |
| GET | `/notifications` | Lawyer change notifications + deeplink |
| POST | `/monitoring/enforcement/{id}` | Update enforcement |

Existing: watch CRUD/check, change actions, GCal, files link/content, entity archive.

## UI routes

- `/workspace/legal?view=monitoring`
- `/workspace/legal?view=calendar`
- `/workspace/legal?view=settings` → Источники данных + СОСТОЯНИЕ ИНТЕГРАЦИЙ
- `/workspace/legal?view=tasks`
- Deep-link: `/workspace/legal?view=monitoring&change={id}`

## Tests

- Backend Lawyer 3.1–3.5: **PASS**
- Frontend 3.3–3.5: **PASS** (6 tests)
- No migration required for 3.5

## Security checks

- Tenant isolation preserved
- Soft delete / archive (no unsafe hard delete)
- OAuth secrets scrubbed; not shown in Settings sources
- SSRF / HTTPS URL validation from 3.4 preserved
- High-impact delete requires confirmation
- Notifications do not log document contents / tokens

## Google Calendar status

- Without credentials: «Не настроен администратором» — ADOS calendar works
- With credentials: ADOS → Google sync + mapping; duplicate sync prevented
- Bidirectional still not enabled

## Legal provider status

| Provider | Status |
|----------|--------|
| Manual Import | Доступно |
| Судебные данные | Не подключено / UNAVAILABLE |
| Исполнительные производства | Не подключено / REQUIRES_CONFIGURATION |

## Known limitations

- Relink/rename UX uses prompt dialogs (production can later use drawers)
- Google → ADOS sync still deferred
- Contracted court/enforcement providers still required for live data
- NotificationCenter telegram delivery depends on bot/owner config; in-app list always available via `/notifications`

## Manual test instructions

A–G acceptance from sprint brief: create TEST-001 watch → check now → import change once → task / calendar / AI handoff → Google absent shows honest status.

## Next recommended sprint

**LAWYER 3.6** (not started): contracted provider adapters, Google→ADOS conflict UX, richer attachment drawers, Unified Intent inbox wiring for legal notifications.

---

**STOP AFTER LAWYER 3.5.**
