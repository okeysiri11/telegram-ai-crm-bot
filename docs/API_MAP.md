# API Map — ADOS / BIDEX Enterprise Platform

**Status:** permanent, living document. **Update this file whenever a route, WS message type, MCP
tool, or event class is added, renamed, or removed** — treat a missing entry here as a bug, not a
minor omission, since this is the map people use to find "does this endpoint already exist."

**Method:** direct reads of every route-registration file, the kernel Runtime Server, MCP registries,
and event/handler modules — concrete path strings below, not just directory-level prefixes. Frontend
API-prefix constants are included so a mismatch between what the UI calls and what the backend serves
is visible in one place.

There are **two independent backends** in this repo (see `ARCHITECTURE_MAP.md`/`DEPENDENCY_MAP.md`):
the **Python aiohttp backend** (`api/server.py`, mounted business/admin/public routes) and the **TS
kernel Runtime Server** (`src/kernel/runtime/RuntimeServer.ts`, port 3000, consumed only by
`platform_console` and the TS ecosystem itself). They do not share a route namespace or a process.

---

## 1. REST — Python backend

### 1.1 Mount order (`api/server.py::create_app()`)

System endpoints registered directly (no prefix): `GET /liveness`, `GET /readiness`, `GET /health`,
`GET /system/db-health`, `GET /metrics` (delegates to `ProductionReadinessSuite` via
`api/health_handlers.py`).

Then, in this exact order:

| # | Call | Mounts at | Source |
|---|---|---|---|
| 1 | `register_crm_api_routes(app)` | `/api/*` (legacy, unversioned) | `api/crm_api.py` |
| 2 | `register_api_v1_routes(app)` | `/api/v1/*` (+ legacy `/v1/*` aliases) | `api/v1/public_router.py` |
| 3 | `register_management_routes(app)` | `/management/v1/*` (+ legacy `/management/*`) — cascades to ~10 sub-routers | `platform_management/management_router.py` |
| 4–21 | 17× `register_<app>_routes(app)` | one `/api/<vertical>/v1` prefix family each | `applications/*/api/register.py` + root `ecosystem/api/register.py` |
| 22 | `app.on_startup.append(_init_plugins)` | — | `platform_plugins.plugin_manager` (`auto_enable=False`) |

Version constants (`platform_api/contracts.py`, `platform_api/versioning.py`): `PLATFORM_API_VERSION =
"v1"`, `MANAGEMENT_V1_PREFIX = "/management/v1"`, `PUBLIC_V1_PREFIX = "/api/v1"`,
`LEGACY_PUBLIC_PREFIX = "/v1"`, `LEGACY_MANAGEMENT_PREFIX = "/management"`.

### 1.2 Legacy CRM API — `/api/*` (`api/crm_api.py`, unversioned — see `TECH_DEBT.md` TD-06)

`POST /api/auth/token` · `GET /api/leads` · `GET /api/leads/{request_number}` · `GET /api/clients` ·
`GET /api/managers` · `GET /api/inventory` · `POST /api/inventory` · `GET /api/recommendations` ·
`GET /api/analytics` · `GET /api/openapi.json` · `GET /api/docs` · `GET /swagger`

### 1.3 Frozen public API — `/api/v1/*` (`api/v1/public_router.py`, + `/v1/*` legacy aliases)

`GET /api/v1`, `GET /api/v1/`, `GET /api/v1/openapi.json`, `GET /api/v1/docs` ·
`POST /api/v1/auth/token` · `GET|POST /api/v1/deals` · `GET|PATCH|DELETE /api/v1/deals/{deal_id}` ·
`GET|POST /api/v1/leads` · `GET|PATCH|DELETE /api/v1/leads/{lead_id}` ·
`GET|POST /api/v1/clients` · `GET|PATCH|DELETE /api/v1/clients/{client_id}` ·
`GET|POST /api/v1/crm/deals` · `GET|PATCH|DELETE /api/v1/crm/deals/{deal_id}` ·
`GET /api/v1/reports` · `GET /api/v1/reports/{report_id}` ·
`GET|POST /api/v1/partners` ·
`POST /api/v1/pricing/calculate` · `GET /api/v1/fx/rates` · `GET|POST /api/v1/vehicles` ·
`GET /api/v1/inventory` · `GET|POST /api/v1/orders` · `GET|POST /api/v1/documents` ·
`GET|POST /api/v1/notifications` · `GET /api/v1/dealer-portal` (+`/modules/{module}`) ·
`GET /api/v1/lead-marketplace` (+`/features/{feature}`) ·
`GET /api/v1/ai-procurement-agent`, `ai-advertising-agent`, `ai-sales-agent`,
`recommendation-engine`, `communication-hub`, `ai-conversation-skills`, `deal-pipeline`,
`cross-posting`, `analytics` (each + `/features/{feature}`) ·
Remaining reserved 501 stubs (`api/v1/__init__.py`): `GET|POST /api/v1/managers`,
`/inventory/crm`, `/analytics/crm`.
CRM leads/clients/reports implemented in Sprint 40.2 (`api/v1/crm_foundation.py`).

### 1.4 Authenticated admin API — `/management/v1/*` (`platform_management/management_router.py`)

Each has a `/management/v1/{suffix}` path and a legacy `/management/{suffix}` alias:

`GET system` · `GET health` · `GET configuration` (+`/export`, `/{key}` GET/PUT/POST/DELETE,
`/{key}/history`, `/{key}/rollback`, `POST /validate`, `POST /import`) ·
`GET verticals` (+`/{code}`, `/{code}/enable|disable|reload`) ·
`GET workflows` (+`/reload`, `/validate`, `/statistics`, `/executions`) ·
`GET sla/overdue`, `sla/risk`, `sla/statistics`, `sla/owner-escalated` ·
`GET managers` · `GET requests` · `GET events` ·
`GET audit` (+`/export`, `/history`) · `GET kpi` · `GET config` (+`POST /reload`) ·
`GET legacy/metrics` · `GET migration` (+`/status`, `/coverage`, `/deprecated`,
`/feature-flags`, `/health`) ·
`GET feature-flags` (+`/{key}/enable|disable`, `/validate`) ·
`GET dashboard` (+`/widgets/{widget_id}`, `/metrics`, `/timeline/events`, `/timeline/audit`) ·
`GET realtime` · `GET openapi.json` · `GET docs`.

Cascades registration of the sub-routers in §1.4.1–1.4.8 below (all under the same
`/management/v1` + legacy `/management` dual-prefix convention).

#### 1.4.1 Identity — `platform_identity/identity_router.py` (`/management/v1/identity`)
`GET ""` · `GET users` · `GET roles` · `GET permissions` · `GET sessions`
(+`POST /{session_id}/revoke`) · `GET api-keys` (+`POST`, `POST /{key_id}/rotate`,
`POST /{key_id}/disable`) · `GET policies` (+`POST`, `DELETE /{policy_id}`) ·
**`POST login`** · **`POST refresh`** (the shared login endpoint both `src/web` and
`platform_console` call — see `MODULES.md` §3.3 duplication note).

#### 1.4.2 Integrations — `platform_integrations/integration_router.py` (`/management/v1/integrations`)
`GET ""` · `GET connectors` (+`POST /{connector_id}/enable|disable`) · `GET webhooks`
(+`POST`) · `GET health` · `GET statistics`.
Plus `platform_integrations/webhook_router.py`: **`POST /integrations/inbound/{webhook_id}`**
(inbound webhook receiver, no `/management` prefix).

#### 1.4.3 Jobs — `platform_jobs/jobs_router.py` (`/management/v1/jobs`)
`GET ""` (+`POST`, enqueue) · `GET scheduler` · `GET workers` · `GET history` ·
`GET statistics` · `GET dashboard` · `POST {job_id}/cancel`.

#### 1.4.4 Observability — `platform_observability/telemetry_router.py` (`/management/v1/observability`)
`GET ""` · `GET metrics` · `GET logs` · `GET traces` · `GET alerts`
(+`POST /{alert_id}/resolve`) · `GET health` · `GET dashboard` · `GET|PUT retention`.

#### 1.4.5 Plugins — `platform_plugins/plugins_router.py` (`/management/v1/plugins`)
`GET ""` · `GET schema` · `GET dependencies` · `GET health` · `POST install` ·
`POST reload` · `GET {plugin_id}` (+`POST /install|enable|disable|reload|upgrade|uninstall`,
`GET /{plugin_id}/health`).

#### 1.4.6 Realtime — `platform_realtime/websocket_router.py` (`/management/v1`)
`GET realtime/ws` — see §2 (WebSocket).

#### 1.4.7 AI — `platform_ai/{ai,skills,memory,workflows}_router.py` (`/management/v1/ai/*`)
See §4 (AI Runtime) — these are the AI-facing REST endpoints.

### 1.5 Vertical application prefixes (17× `applications/*/api/register.py` + root `ecosystem/`)

| App | Primary prefix | Notable sub-prefixes |
|---|---|---|
| `ecosystem` (root, not under `applications/`) | `/api/ecosystem/v1` | identity, organizations, workspace, navigation, communication, assistant, knowledge, workforce, executive, planning, governance, compliance, risk, learning, simulation, recommendations, strategy sub-paths |
| `auto_marketplace` | `/api/auto/v1` | `/api/auto-marketplace/v1`, `/api/vin-intelligence/v1`, `/api/inspection-ai/v1`, `/api/dealer-crm/v1`, `/api/buyer-ai/v1`, `/api/seller-ai/v1`, `/api/automotive-erp/v1`, `/api/connected-cars/v1`, `/api/mobility-platform/v1`, `/api/enterprise-certification/v1`, `/api/auto/mobile/v1`, `/api/auto/partner/v1` |
| `agro_marketplace` | `/api/agro/v1` | — |
| `agro_enterprise` | `/api/agro-enterprise/v1` | `/api/precision-agriculture/v1`, `/api/smart-irrigation/v1`, `/api/crop-ai/v1`, `/api/controlled-environment/v1`, `/api/agro-supply-chain/v1`, `/api/agro-finance/v1`, `/api/ai-agronomist/v1`, `/api/agro-enterprise-certification/v1` |
| `port_erp` | `/api/port/v1` | — |
| `port_enterprise` | `/api/port-enterprise/v1` | `/api/port-navigation/v1`, `/api/port-containers/v1`, `/api/port-multimodal/v1`, `/api/port-customs/v1`, `/api/port-warehouse/v1`, `/api/port-freight/v1`, `/api/port-ai-director/v1`, `/api/port-enterprise-certification/v1` |
| `drone_platform` | `/api/drone/v1` | — |
| `crypto_enterprise` | `/api/crypto-enterprise/v1` | `/api/crypto-ta/v1`, `/api/crypto-mm/v1`, `/api/crypto-mi/v1`, `/api/crypto-se/v1`, `/api/crypto-rm/v1`, `/api/crypto-oc/v1`, `/api/crypto-at/v1`, `/api/crypto-enterprise-certification/v1` |
| `finance_enterprise` | `/api/finance-enterprise/v1` | `/api/finance-pay/v1`, `/api/finance-bil/v1`, `/api/finance-tr/v1`, `/api/finance-da/v1`, `/api/finance-rpt/v1`, `/api/finance-cfo/v1`, `/api/finance-int/v1`, `/api/finance-enterprise-certification/v1` |
| `legal_enterprise` | `/api/legal-enterprise/v1` | `/api/legal-li/v1`, `/api/legal-ji/v1`, `/api/legal-cm/v1`, `/api/legal-di/v1`, `/api/legal-cp/v1`, `/api/legal-aa/v1`, `/api/legal-ei/v1`, `/api/legal-enterprise-certification/v1` |
| `ai_os` | `/api/ai-os/v1` | **shared with `platform_ai_os` and hub MAOS — TD-07** |
| `platform_builder` | `/api/platform-builder/v1` | — |
| `enterprise` | `/api/enterprise/v1` | — |
| `enterprise_hub` | `/api/enterprise-hub/v1` | ~65 further sub-prefixes (orchestrator, knowledge_graph, ai_agents, communications, workflow, digital_twin, simulation_engine, command_center, release `/api/release/v1`, `enterprise_ai_os` → `/api/ai-os/v1` (again shared, see TD-07), `organization_brain` → `/api/organization-brain/v1`, `vertical_federation` → `/api/verticals/v1` — full list in `applications/enterprise_hub/config.py`) |
| `executive_center` | `/api/executive/v1` | — |
| `marketplace` | `/api/marketplace/v1` | — |
| `workflow_studio` | `/api/workflow-studio/v1` | — |

---

## 2. WebSocket

### 2.1 Python backend — `platform_realtime/websocket_router.py`

Single endpoint: **`GET /management/v1/realtime/ws`** (+ legacy `GET /management/realtime/ws`),
authenticated via `identity_service.authenticate_request(request)` before upgrade.

- On connect: `{"type": "connected", "event": "Connected", connection_id, principal_id, roles,
  channels_available, heartbeat_interval}`.
- Inbound message `"type"`: `"ping"` → server `"pong"`; `"subscribe"`/`"unsubscribe"` → server
  `"subscribed"`/`"unsubscribed"` (`event: "Subscribed"`/`"Unsubscribed"`); unknown → `"error"`.
- Channels (`platform_realtime/models.py::RealtimeChannel`): `system`, `dashboard`, `requests`,
  `workflows`, `managers`, `audit`, `configuration`, `notifications`, `plugins`, `ai`, `health`.
- Broadcaster: `platform_realtime/realtime_hub.py::RealtimeHub` (`broadcast`, `broadcast_channel`,
  `broadcast_user`, `send_raw`). Domain-event fan-out via
  `platform_realtime/event_dispatcher.py::RealtimeEventDispatcher` — forwards internal `BaseEvent`
  subclasses as `{"type": "event", "event": "<EventClassName>"}` (e.g. `RequestCreatedEvent`), plus
  synthetic `HealthChanged`, `PluginLoaded`, `KPIUpdated`, and duplicates onto the `audit` channel as
  `AuditEntry`.

### 2.2 TS kernel Runtime Server — `src/kernel/runtime/RuntimeServer.ts`

Bound at **`/ws`** on the same port as the REST API (3000).

- On connect: `{ type: "welcome", platform: "ADOS", version, status: "READY" }`.
- Client `"ping"` (text) → server `{ type: "pong", at }`.
- Every 2s: `{ type: "status", payload: buildStatus() }`.
- Internal kernel event-bus events → `{ type: "event", payload: entry }` (`entry = {id, type, at,
  payload}`).
- Each module (`orchestrator`, `providers`, `chat`, `voice`, `mcp`, `execution`) is given a
  `setStatusBroadcaster` callback and can push its own typed messages onto the same socket — the
  orchestrator README documents `agent.status` and `agent.task` as messages emitted this way.

`platform_console/src/hooks/useRuntimeSocket.ts` is the one real consumer of this WS endpoint
(`RUNTIME_WS`, default `ws://localhost:3000/ws`).

---

## 3. MCP (`src/mcp`, TS)

Not reachable over the network independently — wired in-process to the kernel's `RuntimeServer` via
`setRuntimeInvoker` (see `DEPENDENCY_MAP.md` §5). Listed here as the protocol surface it exposes.

### 3.1 Built-in tools (`MCPToolRegistry.ts::createBuiltinTools`) — name → permission → Runtime call

| Tool | Permission | Runtime API call |
|---|---|---|
| `system.status` | read | `GET /status` |
| `system.health` | read | `GET /health` |
| `system.version` | read | `GET /status` |
| `runtime.status` | read | `GET /status` |
| `runtime.metrics` | read | `GET /metrics` |
| `agent.list` | read | `GET /agents` |
| `agent.info` | read | `GET /agents/status` |
| `agent.execute` | execute | `POST /agents/run` |
| `workflow.list` | read | `GET /workflow` |
| `workflow.execute` | execute | `POST /workflow/start` |
| `provider.list` | read | `GET /providers` |
| `provider.status` | read | `GET /providers/status` |
| `project.list` | read | `GET /services` |
| `project.info` | read | `GET /kernel` |
| `knowledge.search` | read | `GET /events` |
| `document.search` | read | `GET /logs` |
| `dashboard.status` | read | `GET /status` |
| `voice.status` | read | `GET /voice/status` |

### 3.2 Built-in resources (`MCPResources.ts::createBuiltinResources`) — URI → Runtime path

`ados://architecture` → `/kernel` · `ados://sprint` → `/status` · `ados://documentation` → `/` ·
`ados://knowledge` → `/events` · `ados://modules` → `/services` · `ados://providers` → `/providers` ·
`ados://agents` → `/agents` · `ados://configuration` → `/kernel` (permission: `admin`).

### 3.3 Built-in prompts (`MCPPrompts.ts::createBuiltinPrompts`) — template-based, no Runtime call

`explain_module`, `review_code`, `create_workflow`, `generate_ui`, `generate_documentation`,
`architecture_review`, `bug_investigation`.

### 3.4 Config

`config/mcp.config.json` — host `127.0.0.1`, port `3100`, `runtime.baseUrl: http://127.0.0.1:3000`,
transport `http+stdio`, dev auth token `ados-mcp-dev-token`. Not referenced by anything outside
`src/mcp`/`src/kernel` (confirmed in `ARCHITECTURE_MAP.md` §8).

---

## 4. AI Runtime

### 4.1 Python — `/management/v1/ai/*` (the production AI-facing REST surface)

- **`platform_ai/ai_router.py`** (`/management/v1/ai`): `GET ""` · `GET providers` · `GET models` ·
  `GET prompts` · `GET statistics` · `GET costs` · `GET cache` · `POST cache/invalidate` ·
  `POST complete`.
- **`platform_ai/skills_router.py`** (`/management/v1/ai/skills`): `GET ""` · `GET list` ·
  `GET metrics` (+`/{skill_id}`) · `GET health` (+`/{skill_id}`) · `POST execute` (+`/{skill_id}`) ·
  `POST {skill_id}/disable|enable`.
- **`platform_ai/memory_router.py`** (`/management/v1/ai/memory`): `GET ""` · `GET statistics` ·
  `GET recall` (+`/{memory_id}`) · `POST remember` · `DELETE {memory_id}` · `GET|POST search` ·
  `GET knowledge` (+`POST /index`, `POST /rebuild`, `DELETE /{document_id}`, `GET|POST /search`).
- **`platform_ai/workflows_router.py`** (`/management/v1/ai/workflows`): `GET ""` · `GET list` ·
  `GET templates` · `GET history` · `GET metrics` (+`/{workflow_id}`) · `POST execute`
  (+`/{workflow_id}`) · `POST {execution_id}/cancel|resume`.

These routers depend on `platform_management.*` + `platform_api.versioning` for auth/envelope
consistency (see `DEPENDENCY_MAP.md` §5) — they are the governed, API-facing edge of the much larger
internal `platform_ai.*` service graph (`DEPENDENCY_MAP.md` §3.2), which also contains its own
parallel memory/workflow subsystems not exposed here directly.

### 4.2 TS kernel Runtime Server (`RuntimeServer.ts`) — agent/orchestrator/execution endpoints

`GET /agents`, `/agents/status`, `/agents/logs`, `/agents/metrics` · `POST /agents/run` ·
`POST /orchestrator/task` · `GET /collaboration/overview` ·
`POST /execution/plan` · `GET /execution/status`, `/execution/history`, `/execution/report`.

Documented again (subset) in `src/orchestrator/README.md`'s own REST table — same paths, consistent
with `RuntimeServer.ts`.

### 4.3 Chat Bridge (TS, part of the same Runtime Server)

`POST /chat/task` · `POST /chat/run` · `GET /chat/history` · `GET /chat/tasks` · `GET /chat/session` ·
`GET /chat/status` · `POST /chat/cancel` · `POST /chat/rollback` (per `src/chat_bridge/README.md`
and confirmed in `RuntimeServer.ts`).

### 4.4 Voice (TS, part of the same Runtime Server)

`POST /voice/start`, `/voice/stop`, `/voice/process` · `GET /voice/history`, `/voice/settings`
(+`POST`) · `GET /voice/status` · `POST /voice/pause`, `/voice/resume`.

---

## 5. Providers

### 5.1 Python — `platform_integrations/`

Exposed via `/management/v1/integrations` (§1.4.2) — `GET connectors`, enable/disable, `GET webhooks`,
`GET health`/`statistics`, plus the inbound webhook receiver `POST /integrations/inbound/{webhook_id}`.
No further sub-endpoint per named provider found — providers/connectors are data records behind this
one router, not individually-routed.

### 5.2 TS — `@ados/providers`, exposed via the kernel Runtime Server

`GET /providers`, `/providers/status`, `/providers/capabilities` · `POST /providers/connect`,
`/providers/disconnect`, `/providers/execute`. Backing implementation is mock-only (Cursor/OpenAI/
Claude/GitHub/Local-LLM adapters, "no real API keys" per `ProviderGateway`'s own comments —
`ARCHITECTURE_MAP.md` §4).

---

## 6. Events (internal — no HTTP surface, in-process pub/sub only)

### 6.1 Event classes (`events/*.py`)

| File | Classes |
|---|---|
| `base_event.py` | `BaseEvent` (base) |
| `generic_events.py` | `GenericPlatformEvent` |
| `configuration_events.py` | `ConfigurationChangedEvent` |
| `request_events.py` | `RequestCreatedEvent`, `RequestAssignedEvent`, `ManagerFirstResponseEvent`, `RequestCompletedEvent`, `RequestOverdueEvent`, `ManagerEscalationEvent`, `ManagerReassignedEvent` |
| `workflow_events.py` | `WorkflowStartedEvent`, `WorkflowStepCompletedEvent`, `WorkflowCompletedEvent`, `WorkflowCancelledEvent` |
| `manager_pool_events.py` | `ManagerAssignedEvent`, `ManagerReleasedEvent`, `ManagerUnavailableEvent` |
| `owner_events.py` | `OwnerEscalationEvent` |
| `smart_assignment_events.py` | `SmartAssignmentCalculatedEvent`, `SmartAssignmentCompletedEvent` |

### 6.2 Subscription table (wired in `events/handlers/__init__.py::register_platform_event_handlers()`)

| Event | Handlers |
|---|---|
| `RequestCreatedEvent` | notification, metrics, sla |
| `RequestAssignedEvent` | metrics, sla |
| `RequestCompletedEvent` | metrics, sla |
| `RequestOverdueEvent` | sla, notification |
| `ManagerReassignedEvent` | metrics |
| `ManagerEscalationEvent` | notification |
| `OwnerEscalationEvent` | owner_notification, metrics |
| `ConfigurationChangedEvent` | `configuration_hot_reload` |

Plus broad (all-event) subscribers: `audit_service`, `kpi_service` (via
`events/handlers/{audit,kpi}_handler.py`'s generic `BaseEvent` passthrough), `sla_timer_service`,
`manager_pool_service`, `smart_assignment_service`, `workflow_kpi_service`,
`platform_realtime.event_dispatcher.register_realtime_event_handlers()` (→ WS fan-out, §2.1), and
`events/adapters/legacy_adapter.register_legacy_handlers_on_platform_bus()` (→ legacy bridge).

### 6.3 Other event buses (not the canonical one — see `TECH_DEBT.md` TD-20)

`platform_events_legacy.py`'s own `EventBus`, `ecosystem/communication/event_bus/bus.py`,
`applications/finance_enterprise/integration/event_bus.py` (`FinancialEventBus`),
`applications/enterprise_hub/event_platform/event_bus.py`,
`applications/platform_builder/team_map/engine.py` (`VisualEventBus`), and TS
`src/kernel/events/EventBus.ts` — none of these publish onto `events.event_bus.PlatformEventBus`,
so an event raised on one does not reach subscribers on another.

---

## 7. Internal services (non-HTTP, package-to-package calls)

Not "endpoints" in the network sense — listed here because they are the internal equivalent of an
API contract other packages depend on. Full edge list: `DEPENDENCY_MAP.md` §3.

- `platform_management.management_service` — the de facto internal API most other `platform_*`
  packages call into for admin operations (see `DEPENDENCY_MAP.md` §3.1 for its own fan-out).
- `platform_configuration.configuration_center` — the sanctioned way to read config/secrets; anything
  bypassing it directly (`os.environ`) is a tracked violation (`TECH_DEBT.md` TD-17).
- `events.event_bus.PlatformEventBus` — the canonical internal pub/sub contract (§6).
- `platform_ai.ai_service` — the internal entrypoint other packages use for LLM completions (wrapped
  externally by `ai_router.py`, §4.1).
- `repositories/*Repository` classes — the internal data-access contract fronting `database/models/*`.

---

## Related documents

- `ARCHITECTURE_MAP.md` — narrative context for each subsystem above.
- `DEPENDENCY_MAP.md` — package-level dependency edges behind these endpoints.
- `MODULES.md` — per-module catalog; "Public API" columns point back here.
- `TECH_DEBT.md` — TD-06, TD-07, TD-08, TD-13 are about the API surfaces documented above.
