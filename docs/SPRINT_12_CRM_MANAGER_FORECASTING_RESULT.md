# Sprint 12 — CRM Manager Command Center + Pipeline Forecasting + Revenue Intelligence + Team Performance

## Baseline

`b3b64a300e11938249e5fe5523060d78015721a5` on `develop` (Sprint 11 accepted, committed, pushed). Local HEAD matched `origin/develop`. Worktree was clean. Alembic head `s8n901234567` (count 1).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery

PostgreSQL remains the Auto Marketplace Web CRM source of truth. Durable `CRMDeal` rows are the pipeline: `amount`, `stage`, `probability`, `owner_agent_id`, `customer_id`, `created_at`, `closed_at`, `win`. Opportunities remain a deal projection. There is **no deal currency field**, so totals are grouped under `unspecified`. No FX rates are invented.

Stages: prospect, qualification, proposal, negotiation, approval, closed_won, closed_lost.

Sprint 7–11 engines are consumed, not rewritten:

- Sprint 8 automation / follow-ups
- Sprint 9 scoring, temperature, NBA, stale detection
- Sprint 10 execution priority, SLA, escalations, manager queue
- Sprint 11 Customer 360, timeline, `score_relationship()`

Existing `GET /crm/pipeline` and BI `forecasting/service.py` are left as-is. BI weekly growth forecasts are not CRM revenue truth.

Tenant boundary remains `bind_crm_tenant` / `X-Tenant-Id`.

**Decision:** derived manager intelligence at `applications/auto_marketplace/crm/manager_intelligence.py`. No second CRM store, no snapshot table, no durable forecast columns.

## Architecture

`ManagerIntelligenceService` is constructed by `CRMEngine` as `crm_engine.manager`.

Reads only. Command center / forecast / team performance never schedule follow-ups, never create tasks, never restage deals, and never write CRM rows.

Pipeline snapshots are a read model built from `list_deals()` plus Sprint 10 `execution.evaluate(deal_id=...)`. Customer 360 is not called per deal (avoids an extra N+1 360 pass). Relationship health reuses `score_relationship()` from Sprint 11.

## Forecasting

Deterministic, rule-based, no ML, no random, no external AI.

Base probability matches existing stage semantics (prospect 0.10 … approval 0.85, won 1.0, lost 0.0), then fixed adjustments for temperature, lead score, relationship health, staleness, SLA, escalation, overdue follow-up, and hot-lead-without-action. Result is clamped to `[0.0, 1.0]` and explained with reason codes.

`weighted_value = deal_value * forecast_probability` for open deals only. Missing/zero amount yields 0. Closed won/lost are excluded from weighted open pipeline.

Categories: commit, likely, upside, pipeline, at_risk (plus closed_won / closed_lost on snapshots). High/critical risk or stale/low-probability open deals are at_risk.

## Deal risk and workload

Risk flags are derived from execution, automation, and relationship signals: STALE_DEAL, NO_RECENT_CONTACT, FOLLOW_UP_OVERDUE, TASK_OVERDUE, SLA_AT_RISK, SLA_BREACHED, ESCALATED, LOW_RELATIONSHIP_HEALTH, HOT_LEAD_NO_ACTION, HIGH_VALUE_DEAL_NEGLECTED, OWNER_OVERLOADED.

Levels: low / medium / high / critical.

Workload is an operational signal only (normal / elevated / high / critical). No fake quotas or productivity claims. `team_performance.targets` is always `null`.

## Manager surfaces

Command Center aggregates: pipeline summary, revenue intelligence, team performance, top opportunities, top risks, action center, pipeline changes, next actions.

Action center reuses the Sprint 10 execution queue and only adds high/critical deal-risk items that are not already queued. No second scheduler.

Top opportunities sort: `-weighted_value`, `-forecast_probability`, `-deal_value`, `deal_id`.

Top risks sort: `-risk_level`, `-deal_value`, `deal_id`.

Pipeline change intelligence is **limited by existing history**: durable activity facts (deal created, stage changed, won, lost, follow-up scheduled/completed). Forecast-category history and historical SLA snapshots are not persisted and are not fabricated.

Reporting windows use real `created_at` / `closed_at` over 30 days.

## API / security

Authenticated:

- `GET /api/auto/v1/crm/manager/command-center`
- `GET /api/auto/v1/crm/manager/pipeline`
- `GET /api/auto/v1/crm/manager/forecast`
- `GET /api/auto/v1/crm/manager/team-performance`

Unauthenticated → 401. Cross-tenant → empty isolated results. Mutation gates unchanged.

Filters: owner, stage, forecast_category, risk_level, temperature, relationship_health.

Pipeline lists are bounded (`limit` default 50, max 200, `offset`).

Sales manager dashboard adds a `pipeline_forecast` widget from `manager.executive_summary()`. It does not reimplement forecast math.

## Tenant isolation / restart

Tenant B cannot see tenant A pipeline. Restart with the same PostgreSQL facts and `now` returns equivalent probabilities, categories, risk levels, and weighted values.

## Migration

`MIGRATION_REQUIRED=NO`

Alembic head remains `s8n901234567` (count 1).

## Tests

`tests/test_auto_marketplace_crm_manager_forecasting.py` covers empty/single/multiple/open/won/lost snapshots, probability range, deterministic explanations, categories, weighted/zero/missing value, multi-currency safety, deal risk, team/workload, top opportunity/risk ranking and tie-break, action-center dedupe, revenue facts, Sprint 8–11 integration, executive widget, API auth, tenant isolation, idempotent reads, and PostgreSQL restart.

Sprint 7–11 CRM suites remain in the regression gate.

Targeted CRM gate: 120 passed. Broader CRM/BI/portal/manager/API freeze gate: 168 passed.

## Known pre-existing failures

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` → 401 (expected mutation gate)

Frontend was not changed. The user prompt was cut at “27. FRONT”; this sprint ships the backend command center only.

## Architectural decisions

- **Derived manager layer, no forecast table.** PostgreSQL CRM rows remain SoT.
- **Do not call Customer 360 per deal.** Reuse `score_relationship()` and Sprint 10 execution to keep reads bounded.
- **No FX.** CRM has no currency field; mixed-currency helper refuses a canonical total.
- **Limited change intelligence.** Only durable activities; do not invent historical forecast snapshots.
- **Auth on `/crm/manager/*`**, matching intelligence/execution/360 reads.
- **BI forecasting left alone.** It writes `bi_forecasts` and is not CRM revenue truth.

## Files changed

- `applications/auto_marketplace/crm/engine.py`
- `applications/auto_marketplace/crm/customer_360.py`
- `applications/auto_marketplace/api/crm_handlers.py`
- `applications/auto_marketplace/api/register.py`
- `applications/auto_marketplace/executive_dashboard/service.py`

## Files created

- `applications/auto_marketplace/crm/manager_intelligence.py`
- `tests/test_auto_marketplace_crm_manager_forecasting.py`
- `docs/SPRINT_12_CRM_MANAGER_FORECASTING_RESULT.md`

## Final status

Sprint 12 PASS. Safe to commit after explicit acceptance. Do not start Sprint 13 until this work is accepted.
