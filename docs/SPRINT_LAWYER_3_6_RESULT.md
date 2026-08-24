# SPRINT LAWYER 3.6 — RESULT

## STATUS

**COMPLETE.** Detail drawers, safe cross-linking and explicit AI Lawyer handoff shipped as an
extension of Lawyer 3.1–3.5. No fake external legal data anywhere; unavailable providers keep
honest statuses.

## RUNTIME RECOVERY

Both local services were down at sprint start and were restarted:

- Backend API — `.venv/bin/python scripts/run_api_local.py` → http://127.0.0.1:8080
  (runs Alembic migrations automatically; Redis optional in local mode).
- Frontend — `cd src/web && npm run dev` → http://127.0.0.1:5180.

Stop: `Ctrl+C` in each terminal (or `kill <pid>` of `run_api_local.py` / the Vite process).
Both are left running after this sprint per acceptance requirements.

## FILES CHANGED

Backend:

- `services/legal_ops/desk_ops.py` — `related_bundle` generalized from client/case to all six
  drawer kinds (client, case, contract, document, task, hearing); anchors resolve through
  `case_id`/`client_id`; related now includes `clients`, `monitoring` (watch items), `changes`
  (monitor changes) and `ai` for every kind; unknown kinds are rejected with validation error.
- `services/legal_ops/ai_ops.py` — `build_context_pack` accepts `contract_id`, `hearing_id`,
  `change_id` anchors (with source de-dup); `ai_lawyer_run` accepts the same fields and returns
  `reply.source_classification` with four explicit buckets: Факты из данных ADOS /
  Данные пользователя / Внешние проверенные данные (пусто — не подключены) /
  Недостающая информация (DATA GAP).
- `applications/legal_enterprise/api/ops_handlers.py` — `/ai/context` passes the new anchors;
  health reports sprint `3.6`.

Frontend (`src/web/workspace/legal`):

- `LawyerDetailDrawer.tsx` — **new** common detail drawer (right-side panel, list context kept)
  for the six kinds with tabs Обзор / Файлы / Связи / Активность, per-kind overview fields
  (CASE: title, number, status, practice, client, responsible, court, judge, deadline, notes),
  navigable related lists, actions Изменить / Удалить / Передать AI-юристу.
- `LawyerBusinessPage.tsx` — «Открыть» on rows of the six kinds opens the drawer; drawer
  navigation between related objects; AI handoff switches to `view=ai` with context.
- `LawyerAiLawyerPanel.tsx` — accepts handoff context (documents, contract, hearing, change),
  shows explicit «Контекст: ✓ …» block, renders the source-classification (incl. DATA GAP).
- `LawyerMonitoringPanel.tsx` — Change Center «Передать AI-юристу» now also opens the AI Lawyer
  with the change context (backend handoff still recorded); fixed string/boolean typecheck issues.
- `lawyerLabels.ts` — removed duplicate `closed` key (typecheck fix).

## DATABASE / MIGRATIONS

None required. Existing Lawyer 3.1–3.5 schema reused; head unchanged (`h7c890123456`).

## API CHANGES (additive only)

- `GET /api/legal-ops/v1/entities/{kind}/{id}/related` — now supports `contract`, `document`,
  `task`, `hearing` (previously client/case only) and returns extra keys `clients`, `monitoring`,
  `changes` for all kinds.
- `POST /api/legal-ops/v1/ai/context` and `POST /api/legal-ops/v1/ai/lawyer/run` — new optional
  fields `contract_id`, `hearing_id`, `change_id`.
- `POST /ai/lawyer/run` response — new `reply.source_classification` block.
- `GET /health` — sprint `3.6`.

No existing contracts changed or removed.

## FRONTEND CHANGES

- Clicking a row (Клиенты, Дела, Договоры, Документы, Задачи, Заседания) opens the detail drawer
  without leaving the list. Common tabs: Обзор, Файлы, Связи, Активность.
- Связи tab cross-links: клиент ↕ дело ↕ договоры ↕ документы ↕ задачи/сроки ↕ заседания ↕
  календарь ↕ мониторинг ↕ AI-анализы; «Открыть» navigates between drawers. No fabricated
  related records — only genuinely linked rows.
- «Передать AI-юристу» from case / contract / document / hearing drawers and from Change Center
  opens the AI Lawyer with the context pre-attached and an explicit «Контекст: ✓ …» list.
- AI reply shows source classification: ADOS facts, user-provided content, external verified
  (не подключены), DATA GAP list.

## TEST RESULTS

- Backend Lawyer suites 3.1–3.6 + 51.0/51.1: **72 passed**
  (`tests/test_sprint_lawyer_3_6.py` new: health, related bundles for all six kinds,
  monitoring/changes in bundles, unknown-kind rejection, AI handoff via change/contract/hearing,
  source classification + DATA GAP, tenant isolation, observer authorization).
- Frontend Lawyer suites: **24 passed / 8 files** (`sprint_lawyer_3_6.test.tsx` new: drawer tabs +
  overview, cross-link navigation incl. monitoring, AI handoff context payload, «Контекст» block).
- Other verticals regression (`test_sprint_49_1_ops_cabinets`, `test_sprint_50_5/50_6`,
  `test_vertical_nav_46_5`): **44 passed**.
- Typecheck `tsc -b`: no errors in `workspace/legal` (pre-existing errors in unrelated
  `ai-command`/`hercules`/`crypto chartProvider` untouched per "do not touch unrelated verticals").

## MANUAL ACCEPTANCE

Live API flow executed against the running stack (org `org-accept-36`):

1. `/workspace/legal` loads (HTTP 200).
2–7. Client / case / document / hearing / task / contract create + open verified via API and tests.
8. Calendar Месяц/Неделя/День — unchanged from 3.5, covered by existing tests.
9. Detail drawer opens with files tab (attachment infrastructure from 3.5 reused).
10–11. Watch item check produced exactly **1** change; Change Center actions intact.
12. Google Calendar honestly reports `needs_config` («Не настроен администратором»).
13. Providers honest: `manual_import=MANUAL`, `ua_edrsr=UNAVAILABLE`,
    `ua_enforcement=REQUIRES_CONFIGURATION`, `counterparties=UNAVAILABLE`.
14. AI handoff with `change_id` attached sources: case, client, document, hearing, monitor_change;
    `external_verified=[]`; 1 DATA GAP reported.
15. No fake legal/registry data anywhere (external buckets empty; unavailable providers stay so).

## CONNECTED PROVIDERS

- Manual / Import provider (MANUAL) — fully usable.
- Internal ADOS calendar, scheduler (`legal.monitor.morning` / `legal.monitor.evening`).

## UNCONFIGURED PROVIDERS

- Судебные данные (ua_edrsr) — UNAVAILABLE (official/licensed source required).
- Исполнительные производства — REQUIRES_CONFIGURATION.
- Контрагенты — UNAVAILABLE.

## GOOGLE CALENDAR STATUS

`needs_config` — requires `GOOGLE_CALENDAR_CLIENT_ID` / `GOOGLE_CALENDAR_CLIENT_SECRET`
(+ refresh token or OAuth code exchange). Internal ADOS calendar fully functional without it;
duplicate-prevention on sync verified by tests.

## KNOWN LIMITATIONS

- AI answers remain deterministic/mocked unless an LLM provider is configured; classification and
  DATA GAP reporting work regardless.
- Related bundles resolve through `case_id`/`client_id` anchors; entities created without those
  links show empty Связи (by design — no fabricated relations).
- Drawer edit reuses the existing edit cards (CRM card for client/case, entity card otherwise).

## ARCHITECTURAL DECISIONS

- **Extended `related_bundle` instead of a new endpoint** — the drawer consumes the existing
  `/entities/{kind}/{id}/related` contract additively; rejected a parallel `/drawer/...` API as
  duplication.
- **One shared `LawyerDetailDrawer` component** for all six kinds (config-driven overview fields)
  instead of six per-entity cards — keeps UI consistent and avoids component duplication.
- **Source classification computed server-side** in `ai_lawyer_run` so any client (web, agents)
  receives the same honest FACTS/USER/EXTERNAL/DATA-GAP split; frontend only renders it.

## NEXT RECOMMENDED SPRINT

LAWYER 3.7 — contracted court/enforcement providers behind the existing adapter layer,
Google→ADOS inbound sync conflict UX, drawer inline editing. **Not started.**
