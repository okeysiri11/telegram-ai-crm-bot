# Sprint Lawyer 3.1 RESULT — Legal CRM Core / Production Workflow

**Status:** COMPLETE  
**Date:** 2026-08-12  
**Do not start the next sprint automatically.**

---

## DONE

| Area | Status | Notes |
|------|--------|-------|
| Client cardoteka (person/company, fields, filters, tabs) | **DONE** | Additive columns + `LawyerCrmCard` tabs + search filters |
| Case card + related + quick actions | **DONE** | `/entities/case/{id}/related` + CRM card actions |
| Contract card (amount/currency/type) | **DONE** | Persisted amount/currency; deadline→calendar link kept |
| Documents/files (WebP, multi-upload, PDF preview) | **DONE** | `files.py` WebP; multi file input; iframe PDF preview |
| Task manager (statuses/priorities/views) | **DONE** | new/in_progress/waiting/done/overdue/cancelled + today/week/overdue/done |
| Hearings (judge/room/format/video/result) | **DONE** | Internal only — no gov registry |
| Physical calendar month/week/day | **DONE** | Existing board retained; honest Google needs_config |
| Activity / audit timeline | **DONE** | `legal_ops_activity` on create/edit/file/archive/calendar |
| Soft archive (no cascade destroy) | **DONE** | Confirm dialog; restore via Архив |
| Persistence after reload | **DONE** | Postgres + live smoke |
| Tenant isolation / RBAC | **DONE** | Tests + observer 403 |

## PARTIAL

| Area | Status | Notes |
|------|--------|-------|
| Client avatar UX | **PARTIAL** | Upload + `avatar_file_id` + preview in CRM card; dedicated replace/delete avatar controls are via file row actions |
| Hard «Удалить» vs archive | **PARTIAL** | UI «Удалить» on tasks maps to soft archive (safe default for legal records) |
| Contract multi-attach UX | **PARTIAL** | Files link to contract entity; multi-upload on documents form; not a separate contract attachment gallery |
| Google/Microsoft live sync | **NOT in scope** | Adapter foundation from 51.1; **no fake sync** in 3.1 |

## NOT DONE (deferred to later sprints)

- Government court registries (Sprint 3.3)
- Live Google OAuth productization / Microsoft Graph
- Push notification worker for reminders
- Full hard-delete with cascade confirmation workflow

---

## Architectural decisions

| Decision | Choice | Rejected |
|----------|--------|----------|
| Scope | Extend `/api/legal-ops/v1` + Lawyer cabinet only | New app / duplicate Legal CM APIs |
| Schema | Additive migration `d3x456789012` | Destructive rewrite |
| Related tabs | `GET /entities/{kind}/{id}/related` | N+1 frontend-only joins without API |
| Soft delete | Soft archive remains default | Cascade hard delete |
| Calendar providers | Keep adapters; no fake Google sync | Claiming «synced» without OAuth |

---

## Migrations

- `migrations/versions/d3x456789012_legal_ops_lawyer_3_1.py` (revises `c2w345678901`)
- Additive columns on clients / cases / contracts / documents / tasks / hearings
- Empty downgrade (protect production data)

Applied locally via `scripts/ensure_local_schema.py`.

---

## API endpoints (new / extended)

| Endpoint | Change |
|----------|--------|
| `GET /api/legal-ops/v1/health` | sprint `3.1` |
| `GET /clients?q=&client_type=&status=&responsible=&tag=` | Search/filters |
| `GET /entities/{kind}/{id}/related` | **NEW** client/case related bundle |
| Existing CRUD/archive/files/calendar | Extended field sets |

---

## Changed / new files (key)

**Backend:** `database/models/legal_ops.py`, `migrations/versions/d3x456789012_legal_ops_lawyer_3_1.py`, `repositories/legal_ops_repository.py`, `services/legal_ops/desk_ops.py`, `services/legal_ops/service.py`, `services/legal_ops/files.py`, `applications/legal_enterprise/api/ops_handlers.py`, `applications/legal_enterprise/api/register.py`

**Frontend:** `LawyerBusinessPage.tsx`, `LawyerCrmCard.tsx` (new), `lawyerLabels.ts`, `sprint_lawyer_3_1_crm.test.tsx` (new)

**Tests:** `tests/test_sprint_lawyer_3_1_crm.py`

---

## Tests

```bash
.venv/bin/python -m pytest tests/test_sprint_lawyer_3_1_crm.py \
  tests/test_sprint_51_1_lawyer_desk.py tests/test_sprint_51_0_lawyer_ops.py -q
# 24 passed

cd src/web && npm run test -- sprint_lawyer_3_1_crm.test.tsx sprint_51_1_lawyer_desk.test.tsx
# 8 passed
```

---

## Manual acceptance smoke

Evidence: `/tmp/sprint_lawyer_3_1_e2e.json` · org `lex-3-1-9666b278`

1. Create client — **PASS** (201)
2. Add photo / avatar_file_id — **PASS**
3. Create case linked to client — **PASS**
4. Upload PDF to case — **PASS**
5. Create contract with amount — **PASS** (250000.0)
6. Create task/deadline — **PASS**
7. Create hearing → appears in calendar — **PASS**
8. Edit calendar meeting — **PASS**
9. Related case bundle — **PASS**
10. Archive meeting — **PASS**
11. Activity actions present — **PASS**
12. Frontend `/workspace/legal` — **PASS** (200)

---

## Local stack (left running)

| Service | URL |
|---------|-----|
| API | http://127.0.0.1:8080 (`scripts/run_api_local.py`) |
| Web | http://localhost:5180 |
| Health | `/api/legal-ops/v1/health` → sprint `3.1` |
| UI | `/workspace/legal` |

Demo: `owner@demo.corp` / `demo`

---

## Known limitations

- Google Calendar remains honest `needs_config` without OAuth secrets.
- Reminders are in-app list window (`GET /reminders`), not push.
- Inbox remains minimal (unlinked files + bind).
- Case/client «Удалить» in product language is soft archive for legal safety.

---

## Prepared for Sprint 3.2

- Related-bundle API ready for deeper cross-entity workflows
- Hearing courtroom fields ready for registry enrichment (3.3) without schema rewrite
- Calendar provider adapters ready for real OAuth connect UI polish
- Contract amount/currency ready for billing/finance hooks
