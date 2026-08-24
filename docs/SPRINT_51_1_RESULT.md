# Sprint 51.1 RESULT — Lawyer CRUD + Files + Visual Calendar + Calendar Integration Foundation

**Status:** COMPLETE  
**Date:** 2026-08-12  
**Do not start the next sprint automatically.**

---

## What shipped

Lawyer vertical only. Cases, contracts, documents, tasks, hearings, and calendar events are operational: view / edit / archive / restore, file and photo attachments, visual calendar (month / week / day / agenda), inbox, archive, activity, and a reusable calendar-integration adapter (Internal / Google / Microsoft).

Soft delete is the default. Hard delete is not the user workflow.

---

## Acceptance matrix

| Area | Result | Evidence |
|------|--------|----------|
| LAWYER CRUD | **PASS** | Open / Изменить / Архивировать on tables; case+contract edit HTTP 200 |
| FILES | **PASS** | `POST /files` 201; `GET /files/{id}/content` 200 (46 bytes PNG) |
| PHOTO UPLOAD | **PASS** | JPG/PNG upload + thumbnail/preview path; `lawyer-photo-input` |
| ARCHIVE | **PASS** | Confirm «Переместить объект в архив?»; list hides archived; restore |
| CALENDAR UI | **PASS** | Month/week/day/agenda; Сегодня / ← / → / month selector |
| CALENDAR CRUD | **PASS** | Create meeting 201; edit title; archive removes from list immediately |
| REMINDERS | **PASS** | 15/30/60/1440 min; `GET /reminders` 200 (in-app window) |
| GOOGLE CALENDAR FOUNDATION | **PASS** | Adapter + Settings → Интеграции → Календари; OAuth only |
| GOOGLE CALENDAR LIVE SYNC | **NEEDS_CONFIG** | Connect → 409 «Требуется настройка Google OAuth» (not faked) |
| INBOX | **PASS** | Nav «Входящие»; bind to client/case/contract; archive |
| ACTIVITY | **PASS** | created / edited / archived / restored / file_uploaded / calendar_* |
| PERSISTENCE | **PASS** | Notes «после правки» survived archive→restore (DB reload) |

Live evidence: `/tmp/sprint_51_1_e2e_evidence.json`  
Org: `lex-51-1-e2e-6984e071`

---

## Architectural decisions

| Decision | Choice | Rejected |
|----------|--------|----------|
| Persistence | Extend `legal_ops` + `_patch_mem` flush (mapped columns only) | Silent `except: pass` that hid failed updates |
| Files | Disk blobs `data/legal_ops_files/{org}/{id}` + `legal_ops_files` | Duplicate platform storage / Telegram-only refs |
| Soft delete | `archived_at` / `archived_by` / `archive_reason` | Hard delete as default |
| Calendar providers | `CalendarIntegrationService` + adapters | Google/MS logic inside Lawyer screens |
| Google | Honest `needs_config` until OAuth client+secret+refresh exist | Fake «synced» / password collection |
| Microsoft | `coming_soon` card only | Fake connection |
| Archive RBAC | archive/restore mapped to `edit` | Requiring `delete` for lawyers |

---

## Backend

### Migration

- `migrations/versions/c2w345678901_legal_ops_51_1.py` (revises `b1v234567890`)
- Additive: archive columns on CRM tables; case/contract/calendar extra fields; `legal_ops_files`

### Services

- `services/legal_ops/desk_ops.py` — update / archive / restore / files / inbox / linked calendar / reminders
- `services/legal_ops/calendar_integration.py` — Internal / Google / Microsoft adapters
- `services/legal_ops/files.py` — PDF/DOC/DOCX/JPG/PNG validation + blob IO
- Canonical calendar links: hearing, task deadline, contract end, case deadline (`source_kind` + `source_id`, no duplicates)

### API (`/api/legal-ops/v1`)

- `GET/POST /entities/{kind}/{id}`, `/archive`, `/restore`
- `POST /cases/{id}`, `POST /contracts/{id}`
- `/files`, `/files/{id}/content`, `/replace`, `/link`
- `/inbox`, `/archive`, `/reminders`
- `/integrations/calendars`, `POST /integrations/google-calendar/connect`

Health sprint field: `51.1`.

---

## Frontend

- `LawyerBusinessPage.tsx` — row actions, edit card, document card, photo/file attach, inbox, archive filters, integrations
- `LawyerCalendarBoard.tsx` — visual calendar + localStorage filter `lawyer_cal_filter_v1`
- `LawyerRowMenu.tsx`, `lawyerLabels.ts` (RU statuses)
- Nav: Входящие, Архив

---

## Tests

```bash
.venv/bin/python -m pytest tests/test_sprint_51_1_lawyer_desk.py tests/test_sprint_51_0_lawyer_ops.py -q
# 19 passed

cd src/web && npm run test -- sprint_51_1_lawyer_desk.test.tsx sprint_51_0_lawyer_desk.test.tsx
# 8 passed
```

Covered: case edit/archive/restore + rehydrate notes; contract edit/archive; file+image upload + relation + content; calendar CRUD; hearing→calendar; deadline→calendar; no duplicate source events; Google adapter boundary; RBAC observer 403; tenant isolation.

---

## Migrations

- `migrations/versions/c2w345678901_legal_ops_51_1.py`

---

## Local stack (left running)

| Service | URL | Status |
|---------|-----|--------|
| API | http://127.0.0.1:8080 | `scripts/run_api_local.py` |
| Web | http://localhost:5180 | Vite |
| Legal Ops health | `/api/legal-ops/v1/health` | sprint `51.1` |
| Lawyer UI | `/workspace/legal` | HTTP 200 |

Demo login: `owner@demo.corp` / `demo`

---

## Known limitations

- Google live HTTP sync is not executed: no OAuth client/secret/refresh in this environment. Adapter + connect UI are complete and refuse to claim «Подключено».
- Microsoft Calendar is architecture + «Скоро / Требуется настройка» only.
- In-app reminders are a `GET /reminders` time-window check, not a push worker.
- Inbox is a minimal foundation (unlinked files + bind to first client/case/contract).
- Case `deadline_at` is stored on the in-memory/API payload (and payload JSON); there is no extra `deadline_at` column beyond 51.1 case fields already migrated.

---

## Key files

**Backend:** `database/models/legal_ops.py`, `migrations/versions/c2w345678901_legal_ops_51_1.py`, `repositories/legal_ops_repository.py`, `services/legal_ops/desk_ops.py`, `services/legal_ops/calendar_integration.py`, `services/legal_ops/files.py`, `applications/legal_enterprise/api/ops_handlers.py`, `tests/test_sprint_51_1_lawyer_desk.py`

**Frontend:** `src/web/workspace/legal/LawyerBusinessPage.tsx`, `LawyerCalendarBoard.tsx`, `LawyerRowMenu.tsx`, `lawyerLabels.ts`, `sprint_51_1_lawyer_desk.test.tsx`, `src/web/workspace/business-ops/opsApi.ts`
