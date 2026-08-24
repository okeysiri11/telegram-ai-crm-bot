# Sprint 7 — CRM End-to-End Lifecycle + Workflow Integrity

## Starting HEAD

`28d1edcfdad81c2c8ec07a6cd2fad0911915fb7d` on `develop` (Sprint 6 accepted, committed, pushed, remotely verified).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovered lifecycle architecture

Production Web CRM remains `/api/auto/v1/crm/...` with PostgreSQL as the source of truth (`PostgresCRMPersistence` when `AUTO_CRM_PERSISTENCE` is unset). Tests keep `AUTO_CRM_PERSISTENCE=memory`. Tenant scoping is `X-Tenant-Id` / `applications/auto_marketplace/crm/tenant.py`.

Mapped production path (no second CRM):

| Step | Real surface |
| --- | --- |
| Incoming request → lead | Authenticated `POST /api/auto/v1/crm/leads` → `LeadService.create` |
| Lead → customer + deal | `POST /leads/{id}/convert` → `SalesPipelineEngine.convert_lead_to_deal` (reuses `lead.metadata["converted_customer_id"]` / `converted_deal_id`) |
| Opportunity | Deal projection (`opportunity_id` or `deal_id`); no opportunities table |
| Pipeline / stage | `DealService.update_stage` / `advance_stage`; stages: prospect → qualification → proposal → negotiation → approval → closed_won; plus closed_lost |
| Tasks | `TaskService` CRUD + complete/reopen |
| Activities | `ActivityService` timeline + idempotency keys (`lead_converted:{lead_id}`, `deal_stage:{id}:{stage}`, `call:{id}`, …) |
| Phone / email / meeting | `CommunicationService` + `CalendarService` |
| Reminders / follow-up | Durable reminders; `GET /crm/follow-up` is a query board (overdue/due tasks + reminders + recent activities), not an external scheduler |
| Won / lost | Domain stages `closed_won` / `closed_lost`. HTTP `/win` and `/lose` require `deals.manage`. Sales-agent write path is `PATCH /deals/{id}` with `stage` |
| Metrics | `CRMEngine.metrics()` / `CRMMetricsService.collect()` against persistence counts |

Foundation `POST /api/auto/v1/crm/requests` (buyer requests/appointments in `crm/service.py`) is a **separate marketplace domain**. It is not Web CRM intake. Unauthenticated POST still returns 401 under the CRM mutation gate.

## Gaps found

1. Lead intake did not persist source attribution (`utm_*`, `channel`, `referrer`) or optional intake identity.
2. Repeated `POST /crm/leads` always created a new lead (no intake idempotency key).
3. Closed deals could be restaged to an open stage, and `mark_won` / `mark_lost` could overwrite each other.
4. `PATCH stage=closed_won|closed_lost` did not set `win` / `closed_at` / terminal probability, so HTTP closure (sales-agent path) was weaker than `mark_won` / `mark_lost`.

Not treated as defects (existing design, left in place):

- Bare lead POST without `intake_key` is a new lead each time.
- Open-stage PATCH may jump (no full FSM); invalid **enum** values are 400.
- Follow-up is a board, not a generated scheduler job.
- `/win` `/lose` remain manager-gated (`deals.manage`); default Bearer test principal is `sales_agent`.
- Foundation `/crm/requests` stays out of Web CRM SoT.

## Changes made

- `LeadService.create` reuses a tenant-scoped lead when `metadata.intake_key` or `metadata.idempotency_key` matches.
- `POST /crm/leads` stores `assigned_agent_id`, source attribution fields, and `metadata`.
- Closed `closed_won` / `closed_lost` deals cannot move to another stage. Same-stage updates and repeated `mark_won` / `mark_lost` are idempotent.
- Terminal stage application sets `win`, `closed_at`, and probability `1.0` / `0.0` on both `update_stage` and `mark_won` / `mark_lost`.
- Focused integration test: `tests/test_auto_marketplace_crm_lifecycle.py`.

No new CRM module, no parallel endpoints, no scheduler, no migration.

## Request → lead

Authenticated `POST /crm/leads` creates a durable lead with tenant ownership, `created_at`, `source`, and source metadata. Invalid source remains 400. Unauthenticated POST remains 401.

`REQUEST_TO_LEAD=PASS`

## Conversion

Convert creates/reuses customer + deal, sets lead status `converted`, preserves tenant, and is idempotent across restart.

`LEAD_CONVERSION=PASS`

`CONVERSION_IDEMPOTENT=PASS`

## Pipeline

Valid enum stages succeed. Invalid enum → 400. Closed deals cannot reopen. Stage survives restart; pipeline queries return the deal; tenant isolation holds.

`PIPELINE_LIFECYCLE=PASS`

`PIPELINE_RESTART_PERSISTENCE=PASS`

## Tasks + activities

Create / read / update / complete / list-filter work. Timeline records lead_created, conversion, stage, task, call/email/meeting, reminder events. Production workflow does not read MarketplaceStore CRM overlays (removed in Sprint 6).

`TASK_LIFECYCLE=PASS`

`ACTIVITY_TIMELINE=PASS`

## Communications

Calls, emails, and meetings persist, associate to customer/lead/deal, appear on customer timeline, survive restart, and stay tenant-scoped.

`COMMUNICATION_LIFECYCLE=PASS`

`COMMUNICATION_TIMELINE=PASS`

## Reminders + follow-up

Reminder create / read / update / complete / dismiss work. Follow-up board lists overdue/due tasks and reminders plus recent activities. No new scheduler.

`REMINDER_LIFECYCLE=PASS`

`FOLLOW_UP_WORKFLOW=PASS`

## Deal closure

Representative outcomes: `closed_won` and `closed_lost` (no cancelled deal status in this domain). Final state is consistent on deal, pipeline grouping, activity timeline, and metrics `deals_by_stage` / conversion won-lost counts.

`DEAL_CLOSURE=PASS`

`FINAL_STATE_CONSISTENCY=PASS`

## Metrics consistency

Service/API metrics match persistence counts for leads, customers, deals, tasks, activities, calls, emails, meetings, reminders, opportunities (= deals), and pipeline stage maps.

`CRM_METRICS_CONSISTENCY=PASS`

## Full restart

A representative graph (lead, customer, deal, pipeline stage, task, activities, call/email/meeting, reminder) reloads from PostgreSQL after `shutdown_db` + `reset_crm_persistence`. Relationships remain intact; conversion stays idempotent.

`FULL_LIFECYCLE_RESTART_PERSISTENCE=PASS`

## Tenant isolation

Two tenants. Tenant B cannot read, update, delete, list, or transition tenant A lifecycle records (API `X-Tenant-Id` and Postgres persistence).

`CROSS_TENANT_LIFECYCLE_ISOLATION=PASS`

## Idempotency

- Intake with the same `intake_key` reuses the lead.
- Conversion reuses customer/deal and a single `lead_converted` activity.
- Repeated `mark_won` / same-stage PATCH does not corrupt amount/stage.
- Activity keys prevent duplicate automatic events.
- Follow-up GET is a query (no extra records).

`CRM_IDEMPOTENCY=PASS`

## API contract

Authenticated GET/POST/PATCH/DELETE on representative CRM routes keep existing schemas (`items`, `to_dict` fields, 201 create). Unauthenticated mutations remain 401, including foundation `POST /crm/requests`.

`CRM_API_CONTRACT=PASS`

`CRM_MUTATION_GATE=PASS`

## Migrations

`MIGRATION_REQUIRED=NO`

Alembic head remains `s8n901234567` (count 1).

## Tests

Targeted (81 passed):

- `tests/test_auto_marketplace_crm_lifecycle.py` (6 new)
- `tests/test_auto_marketplace_crm_postgres.py`
- `tests/test_auto_marketplace_crm_workflow.py`
- `tests/test_auto_marketplace_crm_communications.py`
- `tests/test_auto_marketplace_crm_metrics.py`
- `tests/test_crm_engine.py`
- `tests/test_crm_api_security_40_1.py`

Broader (129 passed, includes targeted): plus `tests/test_bi_engine.py`, `tests/test_portal_engine.py`, `tests/test_api_v1_freeze.py`, `tests/test_manager_dashboard.py`, `tests/test_crm_foundation_40_2.py`.

## Known pre-existing debt

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin
- `tests/test_production_release.py` version mismatch (`2.0.0` vs `4.2.0-enterprise`)
- Frontend Odessa/Agro/node tsc errors
- Unauthenticated `POST /api/auto/v1/crm/requests` → 401 under CRM mutation gate (expected security)

Frontend build was not run: no frontend files changed.

## Architectural decisions

- **No new CRM.** Lifecycle hardening extends existing LeadService / DealService / handlers.
- **Intake identity is optional metadata**, not a schema column.
- **Closed deals are terminal** rather than introducing a full stage FSM.
- **HTTP `/win` `/lose` RBAC left unchanged** (`deals.manage`). Sales-agent closure uses `PATCH stage`.
