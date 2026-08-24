# Sprint Lawyer 3.2 RESULT — AI Lawyer Workspace / Legal Intelligence

**Status:** COMPLETE  
**Date:** 2026-08-12  
**Do not start the next sprint automatically.**

---

## DONE

| Area | Status | Notes |
|------|--------|-------|
| Split AI-анализ vs AI-юрист (UI + API) | **DONE** | Nav: AI-анализ / AI-юрист / История AI; concepts in `/ai/catalog` |
| AI-анализ sources (CRM object / file / paste / question) | **DONE** | Attachment control; PDF/DOC/JPG/PNG/WebP/TEXT; honest extraction |
| Quick actions (single service layer) | **DONE** | 9 actions → `POST /ai/analyze` + `ai_workspace` |
| Structured analysis sections | **DONE** | summary…recommended_actions; «Источник не подтвержден» for external law |
| Post-result actions | **DONE** | save / attach case / task / calendar / draft / handoff (`confirm=true`) |
| AI-юрист modes + context + run | **DONE** | consult…research; context inspector; exclude sources |
| AI Draft documents + statuses | **DONE** | ai_draft / in_review / approved / archived; never auto-final |
| Draft editor workspace | **DONE** | edit / regenerate fragment / save / save-as-new / link case |
| Tenant-scoped context pack | **DONE** | `build_context_pack` org-scoped; no cross-tenant |
| Sources / Evidence panel | **DONE** | internal docs / case data; external = not connected (no fake registries) |
| AI analysis history | **DONE** | `legal_ops_ai_analyses` + open/replay/archive |
| Safety / audit | **DONE** | activity on analyze/lawyer/task/calendar/draft; mutations need confirm |
| Acceptance A–E | **DONE** | `/tmp/sprint_lawyer_3_2_e2e.json` |
| Tests (mocked LLM) | **DONE** | pytest + vitest; no live LLM |

## PARTIAL

| Area | Status | Notes |
|------|--------|-------|
| Live LLM refinement | **PARTIAL** | Deterministic structured result + optional `MockAIProvider`; production LLM wiring deferred |
| PDF/DOCX full extract | **PARTIAL** | PDF heuristic ASCII; DOC/DOCX asks for paste/text export — no fake parser |
| Image OCR/vision | **PARTIAL** | Honest `needs_vision` flag; existing vision pipeline not auto-invoked for Legal Ops yet |
| Export draft to DOCX/PDF | **PARTIAL** | Content persisted as Legal document payload; binary export uses existing file formats when uploaded |

## NOT DONE (deferred)

- External government legal registries / court practice APIs (Sprint 3.3+)
- Production OpenAI/Claude provider for Legal Ops (use platform_ai when configured)
- Full PDF text + DOCX XML extraction productization
- Automatic vision OCR for JPG/PNG/WebP in Legal Ops desk

---

## Architectural decisions

| Decision | Choice | Rejected |
|----------|--------|----------|
| Scope | Extend `legal_ops` + Lawyer cabinet only | New standalone AI Lawyer product |
| AI layer | `services/legal_ops/ai_workspace.py` + `ai_ops.py` mixin | Duplicate platform_ai / new legal-aa endpoints for desk |
| LLM in CI | Deterministic + MockAIProvider | Flaky live API tests |
| OCR | Honest `needs_vision` / no text | Fake OCR strings |
| External sources | Explicit «не подключены» / «Источник не подтвержден» | Simulated court/registry hits |
| Mutations | User `confirm=true` follow-ups via existing create APIs | Autonomous AI writes/deletes/sends |
| Persistence | New table `legal_ops_ai_analyses` | Activity-only payload history |

---

## Migrations

- `migrations/versions/e4y567890123_legal_ops_ai_3_2.py` (revises `d3x456789012`)
- Table: `legal_ops_ai_analyses`
- Applied via `scripts/ensure_local_schema.py`

---

## API (additive on `/api/legal-ops/v1`)

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | sprint **`3.2`** + `ai` catalog |
| `GET /ai/catalog` (`/ai/actions`, `/ai/modes`) | Actions, modes, draft kinds, concepts |
| `GET\|POST /ai/context` | Tenant context pack + inspector |
| `POST /ai/analyze` | Structured AI-анализ (persisted) |
| `POST /ai/lawyer/run` | AI-юрист run (+ optional AI Draft) |
| `GET /ai/analyses` | History |
| `GET /ai/analyses/{id}` | Detail |
| `POST /ai/analyses/{id}/archive` | Soft archive |
| `POST /ai/analyses/{id}/actions` | Confirmed follow-ups |
| `POST /ai/drafts/{document_id}` | Update draft / status / link |
| `POST /ai/drafts/{document_id}/regenerate` | Fragment preview (no auto-save) |

---

## Changed / new files (key)

**Backend:** `services/legal_ops/ai_workspace.py`, `services/legal_ops/ai_ops.py`, `services/legal_ops/service.py`, `services/legal_ops/desk_ops.py`, `repositories/legal_ops_repository.py`, `database/models/legal_ops.py`, `migrations/versions/e4y567890123_legal_ops_ai_3_2.py`, `applications/legal_enterprise/api/ops_handlers.py`, `applications/legal_enterprise/api/register.py`

**Frontend:** `LawyerAiAnalysisPanel.tsx`, `LawyerAiLawyerPanel.tsx`, `LawyerBusinessPage.tsx`

**Tests:** `tests/test_sprint_lawyer_3_2_ai.py`, `src/web/workspace/legal/sprint_lawyer_3_2_ai.test.tsx`

---

## Tests

```bash
.venv/bin/python -m pytest tests/test_sprint_lawyer_3_2_ai.py \
  tests/test_sprint_lawyer_3_1_crm.py tests/test_sprint_51_1_lawyer_desk.py \
  tests/test_sprint_51_0_lawyer_ops.py -q
# 31 passed

cd src/web && npm run test -- sprint_lawyer_3_2_ai.test.tsx \
  sprint_lawyer_3_1_crm.test.tsx sprint_51_0_lawyer_desk.test.tsx sprint_51_1_lawyer_desk.test.tsx
# 14 passed
```

Coverage: AI permissions, tenant isolation, file context (no fake OCR), analysis persistence, task/calendar creation, draft + case link, audit actions.

---

## Manual acceptance smoke

Evidence: `/tmp/sprint_lawyer_3_2_e2e.json` · org `lex-3-2-ffed9026`

| Flow | Result |
|------|--------|
| A. Upload text + «Кратко объяснить» → saved analysis | **PASS** |
| B. Case + «Найти сроки» → create task | **PASS** |
| C. Calendar event from AI (`20.08.2026`) | **PASS** |
| D. AI Lawyer claim draft → edit → on case card | **PASS** |
| E. List analyses/tasks/calendar after ops | **PASS** |
| Health sprint | **3.2** |
| Frontend `/workspace/legal` | **200** |

---

## Security / permissions

- Observer cannot `POST /ai/analyze` (403)
- Context pack and analyses are organization-scoped
- Destructive/external AI actions blocked; mutating follow-ups require `confirm=true`
- AI does not auto-delete Legal records or send documents

---

## Known limitations

- Analysis quality is deterministic stub (+ mock LLM note), not court-grade legal research
- Images/DOCX need better extractors before full attachment-only workflows
- External legal integrations not started (honest empty external sources)

## Готовность к external legal integrations

Foundation ready: sources panel separates external_legal; analyses store `sources` + `provider_meta`; context pack is pluggable. Next sprint can add real providers without inventing a second AI product.

---

## Local stack (left running)

| Service | URL |
|---------|-----|
| API | http://127.0.0.1:8080/health · Legal Ops sprint **3.2** |
| Web | http://localhost:5180/workspace/legal |

Demo: `owner@demo.corp` / `demo`
