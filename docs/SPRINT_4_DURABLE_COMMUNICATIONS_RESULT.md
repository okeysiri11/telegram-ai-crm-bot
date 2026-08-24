# Sprint 4 — Durable Communications + Reminders + Opportunities

## Starting HEAD

`bb11436e84c5a7f0d053ac7b7a38cfaf0d03ad5f` on `develop` (Sprint 3 accepted).

This sprint did **not** commit or push. HEAD is unchanged.

## Discovery map

| Path | Classification | Notes |
| --- | --- | --- |
| `store.phone_calls` / `CommunicationService.log_call` / `POST .../activities/calls` | **A** production | Was in-memory; now PostgreSQL `auto_marketplace_crm_calls` |
| `store.email_messages` / `log_email` / `POST .../activities/emails` | **A** production | App-level CRM email records only; no SMTP |
| `store.meetings` / `CalendarService.schedule_meeting` / `POST .../calendar/meetings` | **A** production | No Google Calendar integration |
| `store.reminders` / `create_reminder` / `trigger_due_reminders` | **A** production | Distinct from `CRMTask`; own table |
| `store.opportunities` / `SalesOpportunity` | **A→projection** | Older alias of deals, not a separate domain |
| `application.py` `health()` `store.crm_leads` / `store.crm_deals` | **B** overlay | Sync health contract cannot await Postgres |
| `analytics/service.py` `store.leads` / `store.deals` | **B** overlay | Foundation marketplace counts, not Web CRM |
| `analytics/engine.py` workflow counts | **C** derived | Now `count_tasks` / `count_meetings` / `count_reminders` |
| `MarketplaceStore` CRM collections | **B** memory backend | Internals of `MemoryCRMPersistence` (tests) |
| `MemoryCRMPersistence` | **D** test-only | `AUTO_CRM_PERSISTENCE=memory` via `tests/conftest.py` |
| Telegram `ClientRequestCrmEngineV1` | **E** unrelated | Separate domain |
| Foundation `crm/service.py` | **E** unrelated | Separate domain |
| Agro / legal “opportunities” | **E** unrelated | Other verticals |
| Vehicle `maintenance_reminders` | **E** unrelated | Service module, not CRM reminders |

Sprint 3 already dual-wrote call/email/meeting **activities**. Sprint 4 adds typed durable tables **plus** those activities (same pattern as durable tasks), not activity-only reconstruction.

## Persistence model

Production default remains `AUTO_CRM_PERSISTENCE` unset/postgres. Tests keep `memory` via `tests/conftest.py`.

New tables (tenant-scoped, additive):

- `auto_marketplace_crm_calls`
- `auto_marketplace_crm_emails`
- `auto_marketplace_crm_meetings`
- `auto_marketplace_crm_reminders`

CRUD through `PostgresCRMPersistence` + `AutoMarketplaceCrmRepository`. `MemoryCRMPersistence` still uses store collections for unit tests.

Reminders are **not** a task subtype in this domain (`CRMTask` already has its own lifecycle). They remain a separate reminder table.

No SMTP provider. Email persistence is CRM metadata/state only.

No Google Calendar integration.

## Opportunity decision

**Opportunities are an older alias of deals, not a distinct entity.**

- No `auto_marketplace_crm_opportunities` table.
- `convert_lead_to_opportunity` reuses idempotent `convert_lead_to_deal` and sets `deal.opportunity_id = deal.deal_id`.
- `list_opportunities` / `get_opportunity` project `SalesOpportunity` from durable deals.
- `open_deal_from_opportunity` loads the deal by `opportunity_id` or `deal_id`.
- Source of truth: PostgreSQL deals. `store.opportunities` is an unused leftover collection.

Rejected alternative: a second opportunities table (would duplicate deal truth).

## Timeline integration

Idempotent activity keys (existing Activity API unchanged):

| Event | Key |
| --- | --- |
| call logged | `call:{call_id}` |
| email logged | `email:{email_id}` |
| meeting created | `meeting:{meeting_id}` |
| meeting updated | `meeting_updated:{id}:{status}` |
| meeting cancelled | `meeting_cancelled:{meeting_id}` |
| reminder created | `reminder_created:{reminder_id}` |
| reminder completed | `reminder_completed:{reminder_id}` |

Opportunity lifecycle reuses existing `lead_converted` / `deal_created` keys. Customer timeline reads durable calls/emails/meetings plus activities.

## HTTP (additive)

Namespace `/api/auto/v1/crm/...`. Existing POSTs kept.

- GET/PATCH/DELETE `/calls/{id}`, GET `/calls`
- GET/PATCH/DELETE `/emails/{id}`, GET `/emails`
- GET `/calendar/meetings`, GET/PATCH/DELETE `/calendar/meetings/{id}`, POST `.../cancel`
- GET/POST `/reminders`, GET/PATCH/DELETE `/reminders/{id}`, POST `.../complete`, `.../dismiss`
- GET `/opportunities`, GET `/opportunities/{opportunity_id}`

Unauthenticated mutations remain 401. Tenant isolation via existing CRM tenant middleware.

## Overlays reviewed

- `CRMEngine.metrics` / follow-up: durable counts and reminder filters.
- `analytics/engine.py` workflow: durable repository metrics (safe).
- `application.py` `health()`: **left as compatibility overlay**. Method is synchronous; switching to Postgres would require making health async and breaking the existing contract.
- `analytics/service.py`: **left as compatibility overlay**. Counts foundation `store.leads` / `store.deals`, not Web Auto CRM.

## Remaining memory-backed paths

Legitimate leftovers (not required for Sprint 4 production workflow after restart):

- `MemoryCRMPersistence` / store collections (unit tests)
- `application.py` sync `health()` CRM counts
- `analytics/service.py` foundation marketplace counts
- unused `store.opportunities` collection
- Telegram `ClientRequestCrmEngineV1`, foundation CRM, agro/legal, vehicle maintenance reminders

No active Sprint 4 production workflow requires process-local state for correctness after restart.

## Migrations

`MIGRATION_REQUIRED=YES`

- `migrations/versions/s8n901234567_auto_marketplace_crm_communications.py`
- revises `r7m890123456`
- single Alembic head: `s8n901234567`
- existing DB upgraded `r7m890123456` → `s8n901234567` cleanly
- historical migrations were not edited
- no opportunities table
- indexes on tenant + relation/status/trigger columns; no extra FKs (matches Sprint 1–3 CRM tables)

## Tests run / results

Targeted (68 passed):

- `tests/test_auto_marketplace_crm_communications.py`
- `tests/test_auto_marketplace_crm_postgres.py`
- `tests/test_crm_engine.py`
- `tests/test_crm_api_security_40_1.py`
- `tests/test_auto_marketplace_crm_workflow.py`

Broader CRM regression (116 passed, includes targeted):

- plus `tests/test_bi_engine.py`
- `tests/test_portal_engine.py`
- `tests/test_api_v1_freeze.py`
- `tests/test_manager_dashboard.py`
- `tests/test_crm_foundation_40_2.py`

Restart persistence tests construct a **new** `PostgresCRMPersistence` / service instance after `shutdown_db()` + `reset_crm_persistence()`.

## Known pre-existing failures

- `tests/test_database_stabilization_37_1.py` stale Alembic head pin `x7r890123456`
- `tests/test_production_release.py` version `2.0.0` vs existing `4.2.0-enterprise`
- Frontend Odessa/Agro/node TypeScript errors (`npm run build` blocked by tsc)
- Unauthenticated `POST /api/auto/v1/crm/requests` returning 401 under the existing CRM mutation gate (`tests/test_auto_marketplace.py::test_rest_foundation_endpoints`)

Frontend build was not run: no frontend files and no incompatible response-contract changes (additive JSON only).

## Technical debt

- `store.opportunities` collection is unused leftover compatibility surface.
- Sync `health()` still cannot report durable CRM counts.
- Foundation `analytics/service.py` still counts non-CRM store collections.
- SALES_MANAGER RBAC still lacks exact `tasks.read` / `tasks.write` (pre-existing exact-match permission map; default Bearer principal is `sales_agent`).
- Email delivery remains external/absent (CRM records only).
