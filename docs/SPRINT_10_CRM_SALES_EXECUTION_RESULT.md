# Sprint 10 — CRM Sales Execution Engine + SLA + Escalations + Manager Priority Queue

## Baseline

`4aedfc8e16707681862e08edc9fa8116cc673889` on `develop` (Sprint 9 accepted, committed, pushed). Local HEAD matched `origin/develop`. Worktree was clean. Alembic head `s8n901234567` (count 1).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery

PostgreSQL remains the Web CRM source of truth. Sprint 8 already stores follow-ups as reminders and exposes `DUE_WINDOW_SECONDS` (1 hour) plus 7-day urgent overdue in `calculate_priority`. Sprint 9 already derives score, temperature, Next Best Action, and stale opportunities.

Owners already exist: `lead.assigned_agent_id`, `deal.owner_agent_id`, reminder/task assignees. Closed states remain `closed_won` / `closed_lost` / lead `lost`.

No CRM SLA or escalation engine existed. Support-module SLA hours are a different product and were not reused. The Sprint 8 action queue is follow-up-only and was not replaced.

**Decision:** derived execution at `applications/auto_marketplace/crm/execution.py`. Consume Sprint 8 automation and Sprint 9 intelligence. No new table. No second scheduler. No NBA rewrite.

## Architecture

`CRMExecutionEngine` is constructed by `CRMEngine` with the same tenant-scoped intelligence, automation, lead, deal, and task services.

Reads only. Evaluating execution never schedules follow-ups, never creates tasks, never restages deals, and never sends messages.

`execution_id` is deterministic: `exec:{entity_type}:{entity_id}`. Tenant comes from `current_crm_tenant()`.

## Priority algorithm

Reason codes are emitted only from durable facts:

- FOLLOW_UP_OVERDUE
- TASK_OVERDUE
- HOT_LEAD
- HIGH_SCORE (score >= 75)
- STALE_OPPORTUNITY
- NO_RECENT_ACTIVITY
- DEAL_REQUIRES_ACTION
- SLA_BREACHED

`priority_score` is the sum of fixed weights. Labels:

- critical: score >= 70, or SLA breached with hot/stale opportunity
- high: score >= 40, or SLA breached
- medium: score >= 20
- low: otherwise

Closed entities are forced to low / not queued.

## SLA model

Centralized in `execution.py`, reusing Sprint 8 timing:

- ON_TIME: due after the 1-hour due window
- DUE_SOON: due within `DUE_WINDOW_SECONDS`
- OVERDUE: past due, or 7+ days of inactivity without a due date
- BREACHED: 7+ days past due (`SLA_BREACH_SECONDS`, same cutoff as automation URGENT), or stale 14+ days with no due date

Injected `now` is required in tests.

## Escalation model

- none
- attention: overdue, due soon, or stale
- manager: SLA breach, overdue hot work, or stale valued deal
- critical: SLA breach plus hot lead or stale valued opportunity

Reading execution never communicates or mutates CRM state.

## Manager queue

Active entities only. Sort:

1. escalation severity
2. SLA (breached, overdue, due soon, on time)
3. priority score descending
4. due_at
5. entity_id

Filters: owner, priority, temperature, overdue, sla_status, escalation_level, entity_type.

## Reason codes

See priority algorithm. Escalation copies the subset that justified the level into `escalation_reasons`.

## API / read path

Authenticated, tenant-scoped, read-only:

- `GET /api/auto/v1/crm/execution`
- `GET /api/auto/v1/crm/execution/queue`
- `GET /api/auto/v1/crm/leads/{id}/execution`
- `GET /api/auto/v1/crm/deals/{id}/execution`

Unauthenticated reads return 401. Mutation gates are unchanged.

## Tenant isolation

`X-Tenant-Id` / `bind_crm_tenant`. Tenant B cannot read tenant A execution detail, queue items, or summary counts.

## Restart behavior

Derived from PostgreSQL CRM rows. After engine restart, identical facts plus the same `now` yield the same priority, SLA, escalation, reason codes, and queue order.

## Tests

`tests/test_auto_marketplace_crm_execution.py` covers SLA labels, priority reason codes, ordering, filters, closed-deal safety, NBA and automation consumption, read side effects, API auth, API tenant isolation, executive summary widget, and PostgreSQL restart.

Sprint 7–9 CRM suites remain in the regression gate.

Targeted CRM gate: 108 passed. Broader CRM/BI/portal/manager/API freeze gate: 156 passed.

## Migration decision

`MIGRATION_REQUIRED=NO`

Alembic head remains `s8n901234567` (count 1).

## Known pre-existing failures

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` → 401 (expected mutation gate)

Frontend build was not run: no frontend files changed.

## Architectural decisions

- **Derived, not snapshotted.** Execution is a read model over Sprint 8–9 facts.
- **Reuse Sprint 8 due window and 7-day breach cutoff** instead of inventing a new SLA calendar.
- **Do not replace `GET /automation/queue`.** That remains the follow-up work queue. Sprint 10 is the sales execution queue.
- **Auth on execution reads**, matching Sprint 9 intelligence.

## Files changed

- `applications/auto_marketplace/crm/engine.py`
- `applications/auto_marketplace/api/crm_handlers.py`
- `applications/auto_marketplace/api/register.py`
- `applications/auto_marketplace/executive_dashboard/service.py`

## Files created

- `applications/auto_marketplace/crm/execution.py`
- `tests/test_auto_marketplace_crm_execution.py`
- `docs/SPRINT_10_CRM_SALES_EXECUTION_RESULT.md`

## Final status

Sprint 10 PASS. Safe to commit after explicit acceptance. Do not start Sprint 11 until this work is accepted.
