# Sprint 11 — CRM Customer 360 + Unified Timeline + Relationship Intelligence

## Baseline

`4d11f2c1674f895ee4ec340ffd5c3aa2057a74b7` on `develop` (Sprint 10 accepted, committed, pushed). Local HEAD matched `origin/develop`. Worktree was clean. Alembic head `s8n901234567` (count 1).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery

Canonical identity is `CustomerProfile.customer_id`. Leads and deals hang off `customer_id`. Opportunities remain a deal projection. Owners are `customer.owner_agent_id`, `lead.assigned_agent_id`, and `deal.owner_agent_id`.

Timeline facts already live as durable `Interaction` rows (plus calls/emails/meetings recorded as activities). Sprint 8 follow-ups are reminders. Sprint 9/10 intelligence and execution are derived read models.

Existing `GET /crm/customers/{id}/timeline` returns raw activity buckets. Sprint 11 adds a coherent 360 read model without replacing that route.

Tenant boundary remains `bind_crm_tenant` / `X-Tenant-Id`. PostgreSQL is the CRM source of truth.

## Customer 360 model

`Customer360Service` (`applications/auto_marketplace/crm/customer_360.py`) loads one customer plus related leads/deals, then consumes Sprint 8–10 services for that customer only.

Missing domains degrade to empty lists / `NO_ACTION` / `on_time` / `none`.

## Timeline event sources

Normalized from durable activities only. No fabricated score/SLA/NBA history.

Mapped types include lead_created, opportunity_created, stage_changed, communication, note_added, task_created, task_completed, follow_up_scheduled, follow_up_completed, automation_action, deal_won, deal_lost.

Sort: `-occurred_at`, `event_type`, `event_id`.

## Relationship intelligence

Score starts at 50 with explainable weights for recency, hot lead, open deal, overdue follow-up/task, SLA, stale opportunity, and escalations.

- strong >= 75
- healthy >= 55
- attention >= 35
- at_risk < 35

## Attention signals

Deduped, sorted codes: FOLLOW_UP_OVERDUE, TASK_OVERDUE, NO_RECENT_CONTACT, SLA_AT_RISK, SLA_BREACHED, ESCALATED, STALE_OPPORTUNITY, HOT_LEAD_NO_ACTION, HIGH_VALUE_DEAL_AT_RISK.

Reads do not create automation actions.

## API / security

Authenticated:

`GET /api/auto/v1/crm/customers/{customer_id}/360`

Unauthenticated → 401. Cross-tenant → 404. Mutation gates unchanged.

Sales manager dashboard adds a `customer_360` widget pointing at this read model. It does not reimplement 360 logic.

## Tenant isolation / restart

Tenant B cannot read tenant A 360. Restart with the same PostgreSQL facts and `now` returns equivalent health, signals, timeline ids, NBA, and SLA.

## Migration

`MIGRATION_REQUIRED=NO`

Alembic head remains `s8n901234567` (count 1).

## Tests

`tests/test_auto_marketplace_crm_customer_360.py` covers minimal/open/closed customers, timeline ordering and tie-break, relationship explanations, unique signals, Sprint 8–10 integration, idempotent reads, API auth, tenant isolation, dashboard widget, and PostgreSQL restart.

Sprint 7–10 CRM suites remain in the regression gate.

Targeted CRM gate: 113 passed. Broader CRM/BI/portal/manager/API freeze gate: 161 passed.

## Known pre-existing failures

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` → 401 (expected mutation gate)

Frontend was not changed.

## Architectural decisions

- **Derived 360, no snapshot table.** Underlying CRM rows remain SoT.
- **Activities are the timeline source.** Calls/emails/meetings already emit activities; duplicating them would double events.
- **Do not fabricate historical NBA/SLA events.** Those are current derived state on the 360 snapshot.
- **Auth on `/360`**, matching intelligence/execution reads.

## Files changed

- `applications/auto_marketplace/crm/engine.py`
- `applications/auto_marketplace/api/crm_handlers.py`
- `applications/auto_marketplace/api/register.py`
- `applications/auto_marketplace/executive_dashboard/service.py`

## Files created

- `applications/auto_marketplace/crm/customer_360.py`
- `tests/test_auto_marketplace_crm_customer_360.py`
- `docs/SPRINT_11_CRM_CUSTOMER_360_RESULT.md`

## Final status

Sprint 11 PASS. Safe to commit after explicit acceptance. Do not start Sprint 12 until this work is accepted.
