# Enterprise Automation — Trigger System

**Sprint:** CG-7 — Architecture Research + Product Research. Documentation only, `src/` not modified.

**Do not duplicate:** `AUTOMATION_ENGINE.md`/`WORKFLOW_RUNTIME.md` established the engine/runtime
premise — this document covers only what starts a workflow running, per the brief's seven trigger
types (manual, schedule, API, webhook, database, user action, AI action).

## 1. What exists today (verified) — the honest headline

**`platform_workflow/` (the strongest real engine candidate, `AUTOMATION_ENGINE.md` §1) has no trigger
surface of its own at all.** Every workflow starts from a direct, synchronous, programmatic call —
`workflow_engine.create_workflow(...)` followed by `.execute_workflow(...)` — issued by application
code. There is no HTTP endpoint, no webhook receiver, no scheduler binding, and no database-trigger
hook inside `platform_workflow/`, `platform_orchestrator/`, `platform_tools/`, or `events/` themselves.
Every trigger type below is therefore **either a real mechanism that exists elsewhere in the platform
but isn't wired to this engine, or fully SPEC.**

## 2. Per-trigger-type mapping

| Trigger type | Real mechanism elsewhere in the platform | Wired to `platform_workflow` today? | SPEC integration |
|---|---|---|---|
| Manual | Any application code path calling `execute_workflow()` directly — this is the *only* real trigger path today | Yes — trivially, it's the only one | No change needed; this remains the baseline path every other trigger type ultimately calls into |
| Schedule | **Real, but disconnected**: `platform_jobs/` (`cron_manager.py`, `job_scheduler.py`, `job_engine.py`) publishes onto the canonical `events.event_bus.publish`. A second, also real, also disconnected scheduler exists: `services/scheduler_cron.py`/`services/pg_scheduler_engine.py`. A third, narrower one boots at startup scoped to the CRM event bus specifically (`startup.py`, per `ARCHITECTURE_MAP.md` §2.1) | No — none of the three call `workflow_engine.execute_workflow()` | Bind `platform_jobs/`'s scheduler (the best-named, most general-purpose of the three) to call `execute_workflow()` on a matching schedule — the smallest, most additive fix in this entire document: one new call site, zero new infrastructure |
| API | `platform_management/` real, authenticated `/management/v1/*` REST surface exists (`ARCHITECTURE_MAP.md` §2.3) | Not confirmed — this research did not find a `/management/v1/workflows/*` route calling `execute_workflow()` | Add a route under the existing `/management/v1` surface (the real, authenticated, frozen-contract-adjacent admin API), not a new API surface |
| Webhook | **Only outbound found, not inbound**: `applications/enterprise_hub/workflow/actions/webhook.py` is an *outbound* action (a workflow step that calls a webhook), not an inbound receiver that starts a workflow. No inbound webhook route was found anywhere in this research pass that triggers `execute_workflow()` | No | An inbound webhook trigger is a **new, small HTTP route** (under `/management/v1` or a dedicated `/webhooks/*` prefix), whose entire job is: validate the request, call `execute_workflow()`. This is the one trigger type in this table closest to being genuinely net-new, though the route-mounting pattern itself (`api/server.py::create_app()`, real) is not new |
| Database | Not found anywhere in this research pass — no Postgres trigger, no SQLAlchemy event-listener hook into `platform_workflow` | No | Lowest priority of the seven — SQLAlchemy's real `event.listen()` hooks (a standard, already-available mechanism given `database/`'s real SQLAlchemy usage, `ARCHITECTURE_MAP.md` §2.2) are the natural mechanism if ever needed, not a new trigger abstraction |
| User action | The real, canonical `events.PlatformEventBus` (`events/event_bus.py`) already publishes real typed workflow/task lifecycle events (`workflow_events.py`) and a `GenericPlatformEvent` for less-structured cases — a "user did X" event is exactly what this bus already carries | Partially — the bus is real and already carries workflow *lifecycle* events, but this research did not confirm any *inbound* subscription that turns a generic user-action event into a new `execute_workflow()` call | Subscribe a small handler (matching the real pattern in `events/handlers/`, which already has audit/KPI/notification/SLA/configuration handlers) that maps specific `GenericPlatformEvent` types to `execute_workflow()` calls |
| AI action | Same bus, same gap shape as User action — `platform_orchestrator`/`platform_tools` real event publishing (`ToolStartedEvent`/`ToolCompletedEvent`, etc.) could trigger a workflow the same way | No | Same SPEC shape as User action — one new `events/handlers/` subscriber, no new bus |

## 3. The one concrete, already-broken integration this research found

Worth citing precisely because it is the clearest evidence of *why* triggers aren't wired today, not
just *that* they aren't:

`applications/{auto_marketplace,agro_marketplace}/integrations/platform_bridge.py` and
`ecosystem/integrations/platform_bridge.py` construct `TaskRequest(task_type=..., agent_id=...)` when
attempting to hand off to `platform_orchestrator` — but the real `platform_orchestrator.models.TaskRequest`
dataclass has no `task_type` or `agent_id` field (only `capability`/`payload`/`context`/`task_id`/
`timeout_seconds`/`max_retries`/`fallback_capability`/`metadata`). Every such call raises a `TypeError`,
silently swallowed by a blanket `except Exception: logger.debug(...)` in the same file. **This is a
real, present, currently-shipping bug** — not a hypothetical integration risk — and it is exactly the
failure mode any new trigger integration in §2 must guard against: a signature mismatch between a
caller and the real engine's actual dataclass, hidden by overly broad exception handling. Flagged for
`SPRINT_CG_7_RESULT.md`'s risk list as a fix that should happen independently of (and probably before)
any new trigger work, since it demonstrates the exact class of error new triggers would be most likely
to repeat.

## 4. Enterprise event source map (brief §3 — every existing event source)

**Do not duplicate:** City/Notifications/Runtime/Security/Audit event sources were already deeply
researched in `CITY_EVENTS.md` (Sprint CG-4) and `CITY_INTEGRATIONS.md` (Sprint CG-6) — this table
cites those findings rather than re-deriving them, and adds only what those two documents didn't cover
(AI/CRM/ERP/Production Center's backend-side sources, and the canonical Python bus underneath the
frontend one).

| Source | Real event mechanism | Notes |
|---|---|---|
| AI | Python: `platform_orchestrator`'s real `ToolStartedEvent`/`ToolCompletedEvent`/`ToolFailedEvent` (`platform_tools`, this document's own research) and `platform_workflow`'s `TaskCreatedEvent`→`WorkflowCompletedEvent` chain, both via the canonical `events.PlatformEventBus`. Frontend: `CITY_AI_PLATFORM.md`'s already-documented gap — real `/api/ai-os/v1` endpoints exist but the frontend reads a client simulation (`aiAgentRuntime`) instead | Two real, disconnected AI event sources (Python bus, frontend simulation) — `CITY_AI_PLATFORM.md` §4 already specs the migration path |
| CRM | **Thin** — `CITY_CRM.md` §1 already found no live CRM API binding on the frontend side; this document's backend research adds: `events/crm_publisher.py` (real) forwards to a separate DB-backed outbox (`services.crm_event_bus`), distinct from the in-memory `PlatformEventBus` — a real, durable CRM event path exists, just not bound to `platform_workflow` triggers (§2) or to the frontend (`CITY_CRM.md`) | The one domain in this table with a real *durable* event store already (`crm_publisher.py`'s outbox) — worth prioritizing as the first real trigger-binding case in §2 |
| ERP | Same "thin" finding as CRM (`CITY_ERP.md` §1) — no equivalent durable outbox found for ERP specifically in this research pass | Lower priority than CRM for the same reason |
| Desktop | `CITY_DESKTOP.md` §2's already-documented iframe-isolation finding — Desktop-side events do not cross into a Desktop-windowed City's realm except via shared storage or the real Socket.IO layer | Backend triggers reaching a Desktop-windowed frontend inherit this same constraint |
| City | `CITY_EVENTS.md` §1–2 (Sprint CG-4) — the real, 14-value `EnterpriseEventType` union on the frontend `enterpriseEventBus`, not re-described here | |
| Production Center | `CITY_INTEGRATIONS.md` §1 (Sprint CG-6) — real `productionRuntime.monitor()` queue data, blocked on `TD-45`'s generation-backend gap for anything beyond queue plumbing | |
| Notifications | `CITY_INTEGRATIONS.md` §2 (Sprint CG-6) — already covers this fully | |
| Runtime | `CITY_RUNTIME.md` (Sprint CG-4) for the frontend `runtimeEngine`; this document's backend counterpart is the canonical `events.PlatformEventBus` itself, real and confirmed | |
| Security | `CITY_INTEGRATIONS.md` §3 (Sprint CG-6) — real `permissionManager`/`roleManager`/`organizationManager`, not yet consumed by City or by workflow triggers | |
| Audit | `CITY_INTEGRATIONS.md` §3.2's open question (does `telemetry.userActivity` feed `activityCenter`?) remains open; backend-side, `events/handlers/audit` (real, per `ARCHITECTURE_MAP.md`'s handler list) is the canonical audit consumer of the `PlatformEventBus` | |

## 5. Non-goals

- No new event bus for triggers — every trigger type in §2 routes through the real, canonical
  `events.PlatformEventBus` or a real, existing HTTP surface.
- No new scheduler — §2's Schedule row explicitly reuses one of three already-real schedulers rather
  than proposing a fourth.
- Database triggers are explicitly deprioritized (§2) pending an actual product need — not built
  speculatively.

## Related documents

`AUTOMATION_ENGINE.md` §2 (the Schedule row this document expands), `WORKFLOW_RUNTIME.md` (what
happens once a trigger fires), `CITY_EVENTS.md` (the frontend-side event catalog this document's
backend-side "User action"/"AI action" rows are the backend counterpart to — not the same bus, see
`CITY_DESKTOP.md` §2 for why the two are architecturally separate realms).
