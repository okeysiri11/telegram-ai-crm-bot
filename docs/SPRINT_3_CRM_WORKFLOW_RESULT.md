# Sprint 3 — Auto Marketplace CRM Workflow + Tasks + Activities + Pipeline

## Starting HEAD

`901137e72c04d6fd1797125cd2a21b865006d066` on `develop` (Sprint 2 accepted).

The prompt listed `…d0066` (extra trailing `6`); the real Sprint 2 commit is `…d066`.

This sprint did **not** commit or push. HEAD is unchanged.

## Architecture discovered

Production Web Auto CRM already persisted **leads, customers, and deals** in PostgreSQL (`auto_marketplace_crm_*`) via `PostgresCRMPersistence` + `AutoMarketplaceCrmRepository`. Pipeline view/forecast/conversion analytics already derived from durable deals. Lead → deal conversion existed and was idempotent via `lead.metadata["converted_deal_id"]`, but it did **not** provision a customer when `customer_id` was empty.

Tasks, activities, calls, emails, meetings, and reminders lived in `MarketplaceStore` (in-process). HTTP only exposed:

- GET/POST `/api/auto/v1/crm/tasks`
- GET `/customers/{id}/timeline`
- POST `/activities/calls`, `/activities/emails`, `/calendar/meetings`

No tenant-scoped task/activity tables, no complete/reopen/delete HTTP, no automatic lifecycle activities.

Reused: existing CRM models, persistence protocol, `/api/auto/v1/crm` namespace, mutating auth middleware, `Interaction` / `CRMTask` dataclasses. Did **not** duplicate Telegram `ClientRequestCrmEngineV1`, foundation `crm/service.py`, or create a second event bus.

## Tasks implementation

`CRMTask` now carries `created_by`, `priority`, `completed_at`, `updated_at`, and `assigned_to` (alias of `assigned_agent_id`). Durable tables `auto_marketplace_crm_tasks` are tenant-scoped.

Operations: CREATE / READ / LIST / FILTER / UPDATE / COMPLETE / REOPEN / DELETE.

Filters: status, priority, assigned_to/agent_id, lead, customer, deal, overdue, due.

Complete is idempotent. Non-empty `lead_id` / `customer_id` / `deal_id` must exist in the same tenant.

HTTP (additive):

- GET/PATCH/DELETE `/api/auto/v1/crm/tasks/{task_id}`
- POST `/api/auto/v1/crm/tasks/{task_id}/complete`
- POST `/api/auto/v1/crm/tasks/{task_id}/reopen`

## Activities implementation

`Interaction` is the durable activity record (`activity_id` / `activity_type` aliases in `to_dict`). Types reused plus: `message`, `status_change`, `stage_change`, `task_created`, `task_completed`, `lead_created`, `lead_converted`, `customer_created`, `deal_created`.

Table `auto_marketplace_crm_activities` with a **partial unique index** on `(tenant_id, idempotency_key) WHERE idempotency_key <> ''`.

CREATE / READ / LIST / FILTER + chronological `entity_timeline` and customer timeline (`items` additive; `interactions` / `calls` / `emails` / `meetings` kept). Activities are append-oriented; UPDATE/DELETE were not added.

HTTP (additive):

- GET/POST `/api/auto/v1/crm/activities`
- GET `/api/auto/v1/crm/activities/{activity_id}`

Calls, emails, and meetings dual-write a durable activity (store collections remain compatibility overlays).

## Pipeline implementation

No second deal-stage store. `pipeline_view` / forecast / conversion analytics continue to read durable deals. Stage movement uses existing `DealService.update_stage` / win / lose. Totals come from PostgreSQL, not `MarketplaceStore` deal mirrors.

## Conversion implementation

`SalesPipelineEngine.convert_lead_to_deal` now:

1. Ensures a durable customer (`lead.customer_id` or `metadata["converted_customer_id"]`, otherwise creates one tagged `converted-from-lead` with `preferences.source_lead_id`).
2. Ensures a durable deal (`metadata["converted_deal_id"]`).
3. Marks the lead `converted` and keeps both ids on metadata.
4. Records `lead_converted` with idempotency key `lead_converted:{lead_id}`.

Retry returns the same customer and deal. No silent duplicates.

## Automatic activity behavior

Lifecycle mutations record activities through `ActivityService.record` / `record_event` with idempotency keys (no new event bus):

| Event | Key |
| --- | --- |
| lead created | `lead_created:{lead_id}` |
| lead status changed | `lead_status:{lead_id}:{status}` |
| lead converted | `lead_converted:{lead_id}` |
| customer created | `customer_created:{customer_id}` |
| deal created | `deal_created:{deal_id}` |
| deal stage changed / won / lost | `deal_stage:{deal_id}:{stage}` |
| task created | `task_created:{task_id}` |
| task completed | `task_completed:{task_id}` |

Retries reuse the existing row.

## Follow-up workflow

`GET /api/auto/v1/crm/follow-up` (and `CRMEngine.follow_up`) returns overdue open tasks, upcoming due tasks, and recent activities from PostgreSQL (or the memory test backend). No UI redesign.

## PostgreSQL source-of-truth status

**YES** for Sprint 3 production workflow: tasks, activities, pipeline stages, conversion customer+deal, and automatic activities persist in PostgreSQL and survive process restart with a new persistence instance.

Production default remains `AUTO_CRM_PERSISTENCE` unset/postgres. Tests keep `memory` via `tests/conftest.py`.

## Remaining memory-backed compatibility paths

Legitimate leftovers (not required for Sprint 3 correctness after restart):

- `MemoryCRMPersistence` (unit tests)
- `MarketplaceStore` collections used as the memory backend and as overlays for phone calls, emails, meetings, reminders, opportunities
- Foundation `crm/service.py` `Lead` (separate domain)
- Telegram `ClientRequestCrmEngineV1` (separate domain; regression-tested)
- `application.py` store CRM counts overlay
- `analytics/engine.py` `store.crm_tasks.count()` dashboard overlay (not the CRM engine metrics path; `CRMEngine.metrics` now uses `count_tasks()`)

## Migrations

`MIGRATION_REQUIRED=YES`

- `migrations/versions/r7m890123456_auto_marketplace_crm_workflow.py`
- revises `q6l789012345`
- single Alembic head: `r7m890123456`
- existing DB upgraded `i8d901234567` → `r7m890123456` cleanly
- historical migrations were not edited

## Tests run / results

Targeted (57 passed):

- `tests/test_auto_marketplace_crm_workflow.py`
- `tests/test_crm_engine.py`
- `tests/test_crm_api_security_40_1.py`
- `tests/test_auto_marketplace_crm_postgres.py`

Broader CRM regression (97 passed, includes targeted):

- plus `tests/test_bi_engine.py`
- `tests/test_portal_engine.py`
- `tests/test_api_v1_freeze.py`
- `tests/test_manager_dashboard.py`

Restart persistence tests construct a **new** `PostgresCRMPersistence` / service instance after `shutdown_db()` + `reset_crm_persistence()`.

## Known pre-existing failures

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin `x7r890123456`
- `tests/test_production_release.py` version `2.0.0` vs existing `4.2.0-enterprise`
- Frontend Odessa/Agro/node TypeScript errors (`npm run build` blocked by tsc)
- Unauthenticated `POST /api/auto/v1/crm/requests` returning 401 under the existing CRM mutation gate

## Changed files

See git status at end of sprint. Documentation file: `docs/SPRINT_3_CRM_WORKFLOW_RESULT.md`.

## Technical debt

- Calls/emails/meetings still have in-memory store copies alongside durable activities.
- Reminders remain in-memory.
- Opportunities remain a compatibility overlay.
- SALES_MANAGER RBAC still lacks exact `tasks.read` / `tasks.write` (pre-existing exact-match permission map; default Bearer principal is `sales_agent`).
- Analytics overlay still counts `store.crm_tasks` rather than persistence.
