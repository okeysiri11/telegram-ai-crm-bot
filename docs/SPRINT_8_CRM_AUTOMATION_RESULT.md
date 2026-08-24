# Sprint 8 — CRM Automation Engine + Follow-up Scheduler

## Baseline

`6a81aac1fe6fa6d734ff6c502de144163eb0ee60` on `develop` (Sprint 7 accepted, committed, pushed).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery findings

Production Web CRM already had durable PostgreSQL tasks, reminders, and activities (Sprints 3–7). `GET /crm/follow-up` is a read-only board. `CRMWorkflowBridge.schedule_follow_up` only started an in-memory `platform_workflow` overlay. `CalendarService.trigger_due_reminders()` existed but was not an automation engine.

Tenant scoping remains `bind_crm_tenant` / `X-Tenant-Id`. Activity idempotency uses `get_activity_by_idempotency`. Closed deals are `closed_won` / `closed_lost`; lost leads are `lost`.

**Decision:** reuse `Reminder` as the durable follow-up record and `CRMTask` for actionable work. No new table. No frontend. No second in-memory SoT.

## Architecture used

`CRMAutomationEngine` (`applications/auto_marketplace/crm/automation.py`) composes existing Lead/Deal/Task/Calendar/Activity services.

- Follow-up = durable `Reminder` with `action_type`, `source`, `priority`, `idempotency_key` stored in existing JSONB `payload`.
- Next action is the earliest open follow-up for a lead/deal/customer, also snapshotted on `lead.metadata["next_action"]`.
- `evaluate_due_actions(now)` classifies upcoming/due/overdue, creates at most one automation task per follow-up, and cancels follow-ups on closed entities.
- Priority is deterministic (`LOW`/`NORMAL`/`HIGH`/`URGENT`) from overdue duration, deal stage, lead status, and explicit priority. No AI scoring.
- Manager queue is a read model ordered: urgent overdue, high overdue, other overdue, due now, upcoming.
- Time is UTC unix timestamps; ISO-8601 inputs are parsed as UTC (naive timestamps treated as UTC).

## Follow-up model

Operations: `schedule_follow_up`, `reschedule_follow_up`, `complete_follow_up`, `cancel_follow_up`, `get_due_follow_ups`, `get_overdue_follow_ups`.

Open reminder statuses: `pending`, `triggered`. Completed → `completed`. Cancelled → `dismissed` mapped to action status `cancelled`.

Default intake key: `follow_up:{entity_id}:{action_type}` (open rows only).

## Automation / idempotency strategy

- Schedule reuses an open follow-up with the same idempotency key.
- Automation tasks keyed by `task.metadata["automation_reminder_id"]` and activity `automation_task:{reminder_id}`.
- Timeline keys: `follow_up_scheduled:{id}`, `follow_up_rescheduled:{id}:{due_ts}`, `follow_up_completed:{id}`, `follow_up_cancelled:{id}`.
- Re-running evaluate with unchanged state does not create duplicate tasks or timeline rows.

## Priority rules

- Upcoming beyond 1 hour: LOW
- Due within 1 hour: NORMAL
- Overdue 1–24 hours: HIGH
- Overdue 1–7 days: HIGH
- Overdue ≥ 7 days: URGENT
- Deal `approval`: at least URGENT; `negotiation`/`proposal`: at least HIGH
- New lead due/overdue: at least HIGH
- Explicit priority is the max of computed vs requested

## Manager queue behavior

`GET /api/auto/v1/crm/automation/queue` returns tenant-scoped items with entity, action, due_at, status, priority, overdue_seconds, assignee, and source. No UI.

## API additions

Additive under `/api/auto/v1/crm`:

- `GET/POST /follow-ups`
- `GET/PATCH /follow-ups/{follow_up_id}`
- `POST /follow-ups/{follow_up_id}/complete`
- `POST /follow-ups/{follow_up_id}/cancel`
- `GET /automation/queue`
- `POST /automation/evaluate`

Existing `GET /follow-up` board and `GET /leads/{id}/next-action` remain. Next-action response adds `next_action` (durable) beside heuristic `next_best_action`.

Mutations use the existing CRM auth gate (`crm.write`). Unauthenticated POST returns 401.

## Migration decision

`MIGRATION_REQUIRED=NO`

New follow-up fields live in existing reminder/task JSONB payload. Alembic head remains `s8n901234567` (count 1).

## Security checks

Unauthenticated follow-up/evaluate mutations return 401. Tenant B cannot read, reschedule, or evaluate tenant A follow-ups. Automation evaluation is tenant-bound.

## Tests executed

Targeted (93 passed):

- `tests/test_auto_marketplace_crm_automation.py` (7 new)
- Sprint 3–7 CRM suites
- `tests/test_crm_api_security_40_1.py` (added mutation paths)

Broader (141 passed, includes targeted): BI, portal, API freeze, manager dashboard, CRM foundation.

## Known pre-existing debt

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` → 401 (expected mutation gate)

Frontend build was not run: no frontend files changed.

## Architectural decisions

- **No new CRM table.** Follow-ups are reminders; generated work items are tasks.
- **No new global scheduler process.** Durable rows plus `evaluate_due_actions` are restart-safe; a future worker can call the same engine.
- **Workflow bridge overlay retained.** In-memory `platform_workflow` remains optional; durable schedule runs first when the lead/customer exists.
