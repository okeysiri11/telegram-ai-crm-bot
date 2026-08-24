# Sprint 9 — CRM Sales Intelligence + Lead Scoring + Next Best Action

## Baseline

`16fd4aec7123596427440806d13e1632376c8d5b` on `develop` (Sprint 8 accepted, committed, pushed). Local HEAD matched `origin/develop`. Worktree was clean. Alembic head `s8n901234567` (count 1).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery

Durable Web CRM already persisted leads, deals, activities, calls, emails, meetings, tasks, and Sprint 8 follow-up reminders in PostgreSQL. Opportunities remain a deal projection.

Existing intelligence surfaces that were **not** replaced:

- `LeadIntelligenceService` (`applications/auto_marketplace/lead_intelligence/`) mutates `lead.score` / metadata and can qualify leads. AI sales route `/api/auto/v1/ai/leads/{id}/intelligence`.
- `AISalesAssistant.next_best_action` is a heuristic used at lead create and `GET /crm/leads/{id}/next-action`.
- Customer intelligence profiles and VIN/AI recommendation engines are separate products.

Sprint 8 `CRMAutomationEngine` already exposes overdue follow-ups, next due action, tasks, and the manager action queue. Sprint 9 consumes that state.

**Decision:** one canonical derived scorer at `applications/auto_marketplace/crm/intelligence.py`. No second CRM store. No LLM API. No new table.

## Architecture chosen

`CRMIntelligenceService` is constructed by `CRMEngine` with the same tenant-scoped lead/deal/task/calendar/activity/communication/automation/customer services as Sprint 8.

Reads only. Scoring, temperature, NBA, and stale detection never restage deals, never qualify/lose leads, and never create follow-ups, tasks, or activities.

Temperature names `hot` / `warm` / `cold` match existing CRM/AI-sales terminology. Thresholds are module constants (`HOT_THRESHOLD=75`, `WARM_THRESHOLD=45`), not imported from the AI sales layer.

## Scoring model

Normalized integer score `0..100`.

`score = clamp(40 + sum(factor.impact))`

Same durable CRM facts plus the same `now` produce the same score, factors, temperature, and NBA.

### Positive factors (when the durable fact exists)

| code | impact | fact |
| --- | --- | --- |
| quality_source | +8 | lead source referral or dealer |
| vehicle_interest | +5 | vehicle_id set |
| converted | +8 | lead status converted |
| customer_intent | +10 | customer.intent_score > 50 |
| deal_value | +1..10 | deal.amount / 5000, capped |
| deal_progress | +6..20 | qualification / proposal / negotiation / approval |
| recent_activity | +12 | interaction within 3 days |
| completed_meeting | +15 | meeting status completed |
| completed_call | +12 | call status completed |
| recent_email | +8 | email sent or logged |
| active_follow_up | +10 | Sprint 8 follow-up upcoming or due |
| open_task | +6 | open task that is not overdue |

### Negative factors

| code | impact | fact |
| --- | --- | --- |
| inactivity | -12 or -20 | no activity, 7+ days, or 14+ days |
| overdue_follow_up | -15 | Sprint 8 follow-up overdue |
| overdue_task | -12 | open task past due_at |
| stale_pipeline | -15 | open deal with 14+ days inactivity |
| missing_follow_up | -8 | no next action and no follow-ups |
| unanswered_attempts | -6 each, max 3 | missed calls |
| closed_lost | -20 | deal stage closed_lost |

Closed entities are classified COLD and are not active sales work.

## Temperature thresholds

Centralized in `applications/auto_marketplace/crm/intelligence.py`:

- HOT: active and score >= 75
- WARM: active and score >= 45
- COLD: inactive, or score < 45

## NBA rules

Recommendation only. Never executed.

Priority order:

1. Closed entity → `NO_ACTION`
2. Overdue task → `COMPLETE_OVERDUE_TASK`
3. Overdue follow-up → `CALL_CUSTOMER` / `SEND_EMAIL` / `SCHEDULE_MEETING` from Sprint 8 `action_type`
4. New lead with no calls → `CALL_CUSTOMER`
5. No next action → `CREATE_FOLLOW_UP`
6. Deal negotiation/approval → `ADVANCE_PIPELINE`
7. Deal proposal/qualification → `REVIEW_DEAL`
8. No meeting → `SCHEDULE_MEETING`
9. Else → `SEND_EMAIL`

Each result includes `action`, `priority`, `reason`, `entity_type`, `entity_id`.

## Stale detection rules

Open entities only. Closed won/lost and lost leads are excluded.

Flags when present:

- no recent activity (none, or 14+ days)
- overdue follow-up
- overdue task
- missing next action
- pipeline stage inactivity on an open deal

## Persistence decision

`MIGRATION_REQUIRED=NO`

Intelligence is derived from PostgreSQL CRM rows on each read. Restart returns the same result for unchanged durable state. No snapshot table, no in-memory production cache.

Alembic head remains `s8n901234567` (count 1).

## Manager integration

`GET /api/auto/v1/crm/intelligence` returns hottest active work, neglected open deals, overdue follow-ups, recommended actions, and temperature counts.

Sales manager executive dashboard adds a `sales_intelligence` widget that reuses the same read model. No second dashboard architecture. Telegram `test_manager_dashboard.py` is a different product and was not redesigned.

`GET /crm/leads/{id}/next-action` additively includes `recommended_action` beside the existing heuristic and durable follow-up.

## API surface

Additive, authenticated, tenant-scoped, read-only:

- `GET /api/auto/v1/crm/intelligence`
- `GET /api/auto/v1/crm/leads/{id}/intelligence`
- `GET /api/auto/v1/crm/deals/{id}/intelligence`

Unauthenticated intelligence reads return 401. Mutation gates are unchanged.

## Security

- Tenant scoping remains `bind_crm_tenant` / `X-Tenant-Id`.
- Tenant B cannot read tenant A scores, factors, NBA, stale deals, or manager intelligence (404 / empty lists).
- Intelligence GET requires Bearer auth in handler and CRM middleware.
- Reads do not create activities, communications, reminders, tasks, or deals.

## Tests

`tests/test_auto_marketplace_crm_intelligence.py` covers score bounds, determinism, explanation, activity/overdue effects, HOT/WARM/COLD, NBA + explanation, stale detection, closed-deal safety, manager ordering, PostgreSQL restart, tenant isolation, API auth, API tenant isolation, and read side-effect absence.

Sprint 7 lifecycle and Sprint 8 automation suites remain green. CRM metrics tests remain green.

## Migration status

No migration. `alembic heads` → `s8n901234567` (1 head).

## Known pre-existing debt

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` → 401 (expected mutation gate)

Frontend build was not run: no frontend files changed.

## Architectural decisions

- **Derived, not snapshotted.** PostgreSQL CRM rows are already the source of truth; a score table would duplicate state and risk drift.
- **New CRM intelligence module, not LeadIntelligenceService.** That service mutates leads and sits on the AI sales path. Sprint 9 must not mutate lifecycle and must not add LLM dependencies.
- **Reuse 75/45 temperature cutovers** already used by lead intelligence, as constants inside CRM, to avoid an AI-layer import.
- **Auth on intelligence reads only.** Existing unauthenticated CRM GET list/detail contracts stay intact; mutation gates stay intact.

## Files changed

- `applications/auto_marketplace/crm/engine.py`
- `applications/auto_marketplace/api/crm_handlers.py`
- `applications/auto_marketplace/api/register.py`
- `applications/auto_marketplace/executive_dashboard/service.py`

## Files created

- `applications/auto_marketplace/crm/intelligence.py`
- `tests/test_auto_marketplace_crm_intelligence.py`
- `docs/SPRINT_9_CRM_SALES_INTELLIGENCE_RESULT.md`

## Final status

Sprint 9 PASS. Safe to commit. Do not start Sprint 10 until this work is accepted.
