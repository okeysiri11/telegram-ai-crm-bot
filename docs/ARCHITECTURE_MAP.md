# Architecture Map — ADOS / BIDEX Enterprise Platform

**Last verified:** 2026-08-02 · Sprint **33.2** Intelligent Navigation · prior **33.1** · **Status:** permanent, living document — part of a four-document set
maintained together and refreshed every sprint (per `CLAUDE.md`'s sprint-closeout rule):

- **`ARCHITECTURE_MAP.md`** (this document) — narrative structure: what exists, how it's organized.
- [`DEPENDENCY_MAP.md`](./DEPENDENCY_MAP.md) — the module dependency graph, direction, and cycles.
- [`MODULES.md`](./MODULES.md) — per-module catalog (owner, public API, status, debt, future plans).
- [`API_MAP.md`](./API_MAP.md) — concrete endpoint-level inventory (REST/WS/MCP/events).
- [`TECH_DEBT.md`](./TECH_DEBT.md) — the living debt registry; this map's §12–16 feed its entries.
- [`TECH_DEBT_REGISTRY.md`](./TECH_DEBT_REGISTRY.md) — categorized debt index (Architecture / Performance / Security / UX / Infrastructure).
- [`INTELLIGENT_NAVIGATION_33_2.md`](./INTELLIGENT_NAVIGATION_33_2.md) · [`ENTERPRISE_UX_33_1.md`](./ENTERPRISE_UX_33_1.md) — UX navigation.

**Method:** direct repository reads + targeted greps across the full tree (Python backend, `src/` TS ecosystem,
`src/web`, `platform_console`, `docs/`), cross-checked against existing generated reports
(`ARCHITECTURE_REPORT.md`, `docs/ARCHITECTURE_INVENTORY.md`, `docs/TECHNICAL_DEBT_REPORT.md`,
`LEGACY_MIGRATION.md`) rather than superseding them — this document is the map that connects those
reports to the actual folder structure, for someone who has never read this repo before.

> This repo actually contains **three largely independent systems** that share one Git history:
> 1. a Python Telegram-bot + enterprise-platform backend (repo root),
> 2. a Python/React set of business-vertical applications and two web consoles built on top of it,
> 3. a standalone Node/TypeScript "ADOS OS" agent-kernel runtime (`src/kernel` + 6 packages) with its
>    own frontend consumer (`platform_console`).
>
> System 3 has **no runtime connection** to systems 1–2 (confirmed by grep — see §8). Keep this in mind
> throughout: many components below have a same-sounding sibling ("orchestrator", "memory", "dashboard")
> that is a *different, disconnected* implementation, not the same thing reused.

---

## 1. Repository tree (top level, annotated)

```
TelegramBotCourse/
├── main.py, bot.py, bootstrap.py, startup.py     # Bot process entrypoint & lifecycle
├── config.py                                     # Legacy config facade → platform_configuration
├── container.py                                  # DI scaffold — defined, NOT wired into startup (§8)
├── handlers.py, keyboards.py                     # Original monolithic bot code (~5,000+ lines, legacy)
├── database_legacy.py                            # 11,205-line legacy DB module (still imported, §5)
├── platform_events_legacy.py                     # Legacy event bus (own `EventBus` class, §5/§7)
├── openrouter.py, fsm_storage.py                 # Legacy support modules
├── *_handlers.py  (21 files)                     # Legacy Telegram feature handlers (§5)
│
├── api/                                          # HTTP app factory — mounts every route family (§4)
├── platform_api/                                 # Frozen contracts/envelope types only (no routes)
├── platform_management/                          # Authenticated admin REST — /management/v1
├── middleware/                                   # entry_point, error_tracking, tenant middleware
├── routers/                                      # 8 Telegram bot routers (registered in startup.py)
│
├── events/                                       # PlatformEventBus — canonical in-process bus
├── services/                                     # Business logic, 232 files (§2)
├── repositories/                                 # Postgres data access, 111 files (§2)
├── database/                                     # Canonical DB package: models/, engine, session, migrations
├── migrations/                                   # Alembic migrations (root) — a SECOND migrations dir (§5)
│
├── platform_architecture/                        # Executable governance + Sprint 32.2 core_inventory / sprint_review
├── platform_legacy/                              # Legacy compatibility/isolation boundary (§5)
├── platform_<capability>/  (~76 packages)         # Enterprise capability layers (§3)
├── platform_enterprise_<capability>/  (30 pkgs)   # Parallel "Enterprise" layer, additive to legacy (§3, §6)
│
├── applications/  (17 verticals)                  # Production apps on "Platform Core" (§9)
├── plugins/                                       # Example vertical plugins — scaffolding only (§8)
│
├── src/                                           # ⚠️ TWO unrelated trees share this path (§6):
│   ├── domains/, platform/, verticals/, events/, web/   #   — Python domain model (parallel, minor)
│   └── kernel/, orchestrator/, providers/, chat_bridge/, voice/, mcp/, execution/  # — Node/TS "ADOS OS"
│
├── platform_console/                             # React "Enterprise Control Center" — UI for ADOS OS (§6)
├── (src/web lives inside src/, see §6.1)          # React "Enterprise Web Platform" — UI for Python backend
│
├── docs/  (~987 files)                            # Sprint-numbered reports, audits, guides
├── tests/                                         # pytest suite (342 subdirs/files)
├── scripts/                                       # Architecture/legacy/certification validation scripts
├── knowledge/, ecosystem/, workflow/, workers/, storage/, models/, states/, audit/, connectors/, lib/
│                                                   # Supporting root packages (not detailed here)
├── docker-compose.yml                             # Defines ONLY postgres + redis (§8 — no app services)
└── package.json                                   # Root npm workspace — orchestrates src/* TS packages
```

---

## 2. Backend architecture (Python, repo root)

### 2.1 Bot lifecycle

`main.py` → `bootstrap.py` (aiogram `Dispatcher`, FSM storage) → `startup.py::run_startup()` (loads
`ConfigurationCenter`, validates IAM JWT secret, starts the aiohttp API server, registers platform
event handlers, starts the CRM event-bus worker and scheduler) → `dp.start_polling(bot)`. `bot.py` is a
backward-compatible re-export shim. Routers are registered via
`platform_legacy.legacy.telegram.register_bot_routers(dp)`, driven by `startup.py::BOT_ROUTER_PATHS`
— currently all 8 files under `routers/` plus `auto_vertical_handlers` and root `handlers`
(`routers/admin/` exists but is empty — no `.py` source, unused).

### 2.2 Core data/service layers

| Layer | Size | Notes |
|---|---|---|
| `services/` | 232 files | Business logic, no direct HTTP exposure. Naming: 101 `pg_*` prefix, 89 `*_engine.py`, 21 `*_v1.py`/`*_service.py`. Some `*_test.py` files live co-located here rather than in `tests/`. |
| `repositories/` | 111 files | All Postgres/SQLAlchemy (`grep sqlite` → 0 hits; 103/111 files use SQLAlchemy). `repositories/base_repository.py` is a 4-line shim re-exporting `src/platform/layers/base_repository.py` — i.e. the real base class lives under the *other* Python tree in `src/` (§6), not in `repositories/` itself. |
| `database/` | models/, engine.py, connection.py, session.py, async_bridge.py, migration_models.py, migrations/versions/ | The canonical, modern DB package; `api/server.py`/`startup.py` import `database.session` directly. |
| `database_legacy.py` | 11,205 lines | Coexists with `database/`; still imported by `database/__init__.py` itself, `platform_architecture/*`, `scripts/check_no_sqlite.py`, `src/platform/layers/architecture_policy.py`, and `platform_legacy/*`. Contains ~85 `# TODO: future implementation` markers. |
| `events/` | event_bus.py (`PlatformEventBus`), crm_publisher.py, base_event.py, handlers/, adapters/ | The canonical event bus; `startup.py` wires `register_platform_event_handlers()` and starts `get_crm_worker()`. **Not the only `EventBus` in the repo** — see §7. |

Two Alembic-relevant migration directories exist: root `./migrations` (pointed to by `alembic.ini`,
`postgresql+asyncpg://` URL) and `./database/migrations` — worth confirming which is authoritative
before adding new migrations.

### 2.3 API surface

`api/server.py::create_app()` mounts, in order: health/metrics endpoints → legacy unversioned
`/api/*` CRM routes (`register_crm_api_routes`, explicitly commented "legacy, unversioned") →
frozen `/api/v1/*` (`register_api_v1_routes`, with `/v1/*` legacy compatibility) →
`platform_management.management_router` (`/management/v1/*`) → **15 separate
`applications/*/api/register.py` registrations** (one per vertical app) → plugin-manager startup hook.

- `platform_api/` — contracts/envelope types only (`ApiEnvelope`, `PaginatedResponse`, `ErrorResponse`,
  `API_CONTRACT_VERSION`); mounts no routes itself.
- `platform_management/` — the actual authenticated admin surface (`/management/v1/*`): configuration,
  verticals, workflows, SLA, managers, identity, plugins.
- Auth today is **header-only** across these surfaces pending full Identity Center token integration
  (per `docs/API_CORE_AUDIT.md`) — see §10.

### 2.4 `platform_*` capability layers

~76 Python `platform_<capability>/` packages plus 30 `platform_enterprise_<capability>/` packages (106
total under this prefix). Each is independently sprint-versioned. Grouped by role:

- **Governance**: `platform_architecture/` (rules, dependency graph, CI validation — the source of
  `ARCHITECTURE_REPORT.md`), `platform_legacy/` (isolation boundary, §5), `platform_certification/`,
  `platform_validation/`, `platform_quality/`, `platform_testing/`.
- **API/identity/integration**: `platform_api/`, `platform_management/`, `platform_identity/`
  ("single authorization source"), `platform_integrations/`, `platform_realtime/`, `platform_jobs/`.
- **Cross-cutting enterprise concerns**: `platform_security/`, `platform_observability/`,
  `platform_reliability/`, `platform_configuration/`, `platform_operations/`, `platform_performance/`.
- **AI agent stack** (the intended chain): `platform_memory/` (context/memory) →
  `platform_orchestrator/` (`AgentRegistry`, `CapabilityRouter`, `AgentMessageBus` — "central execution
  layer for all AI agents") → `platform_agents/` (plugin-based agent registry, near-identical exports
  to `platform_orchestrator`, §7) → `platform_workflow/`/`platform_tools/` (execution) →
  `platform_reasoning/`/`platform_planning/`/`platform_decision/` (cognition) →
  `platform_learning/`/`platform_collaboration/` (feedback/consensus).
- **Plugin/SDK surface**: `platform_plugin_sdk/`, `platform_sdk/`, `platform_plugins/` (dynamic
  discovery/management — see §8 for whether example plugins actually load).
- **Vertical-flavored "Sprint 21–27" packages**: `platform_ai_business_advisor`,
  `platform_ai_marketing_os`, `platform_beauty_*` (3 packages), `platform_cafe_os`,
  `platform_client_portal`, `platform_communications_hub`, `platform_contracts`, `platform_documentation`,
  `platform_migration`, `platform_predictive_intelligence`, `platform_product_intelligence`,
  `platform_release`, `platform_vertical_federation`, `platform_workflow_intelligence`,
  `platform_organization_brain` — each a single `*Library` facade class.
  **Sprint CQ-10 clarification — `platform_contracts` is a name that invites confusion**: it is a real,
  working **API/DTO schema-registry** (`DtoRegistry`/`SchemaRegistry`, schema publish/version/rollback/
  compatibility-check, `platform_contracts/dto/{crm,erp,hr,finance,...}/models.py`) for *internal
  microservice contract compatibility*, not a legal-document/agreement system — not wired into any real
  API route (confirmed by repo-wide grep), with a duplicate copy at `applications/enterprise_hub/
  data_contracts/`. A future "business contract/agreement" feature (`docs/EBN_VERIFIED_DOCUMENTS.md`,
  Sprint CQ-10) should not mistake this package for a foundation — it solves a different problem.
  `platform_communications_hub` is a related naming trap for a different future feature
  (`docs/EBN_COMMUNICATION.md`): it's a real, one-way **outbound notification gateway**
  (`CHANNELS = sms, email, push, telegram, whatsapp, viber, voice_call`), not peer-to-peer chat.
- **`platform_enterprise_*` (30 packages, Sprint 23–27)**: a parallel "Enterprise" layer running
  alongside the above — several explicitly document in their own docstrings that they are *additive*
  to an older sibling (e.g. `platform_enterprise_performance_testing`: "Legacy EPF platform_performance
  remains unchanged"; `platform_enterprise_security_verification`: "Legacy ESH platform_security
  remains unchanged"; `platform_enterprise_digital_twin`: "Distinct from legacy Digital Twin (EDT)").
  This is a deliberate additive-only policy (see `docs/ARCHITECTURE_AUDIT_INDEX.md`: "No new Business
  Ecosystems after Sprint 31.4"), not an accident — but it is also the direct cause of most naming
  duplication in §7.

`container.py` (`AppContainer`/`ServiceRegistry`) is a DI scaffold — see §8, not wired into production.

### 2.5 Middleware & routing

`middleware/` — `entry_point_middleware.py` (rejects cross-flow navigation), `error_tracking_middleware.py`
(captures handler exceptions), `tenant_middleware.py` (injects `ActiveTenantContext` — the multi-tenancy
enforcement point). `routers/` — 8 Telegram router modules (auto client/dealer/hub, client history,
manager crm/dashboard/debug, realty), all referenced by `startup.py`.

### 2.6 Applications (`applications/`, 17 verticals)

Built on "Platform Core"; sizes vary hugely (file counts from direct listing):

| App | Files | Maturity |
|---|---|---|
| `auto_marketplace` | 420 | Largest; GA production marketplace (dealer_network, fleet, telematics, vin_intelligence) |
| `enterprise_hub` | 866 | Largest overall; internally re-implements many `platform_enterprise_*` concepts locally (§7) |
| `port_erp` | 209 | Maritime domain (berths, cranes, vessels, yard) |
| `agro_marketplace` | 185 | "Production Ready" per manifest |
| `drone_platform` | 161 | mavlink/swarm/gcs/firmware |
| `platform_builder` | 113 | No-code builder product — see §9 for internal duplication |
| `legal_enterprise` | 93 | |
| `finance_enterprise` | 91 | Bidex finance platform |
| `agro_enterprise` | 59 | |
| `port_enterprise` | 57 | |
| `crypto_enterprise` | 64 | |
| `ai_os` | 16 | Thin (kernel.py, bus.py, runtime.py, memory.py) — shares `/api/ai-os/v1` with hub MAOS |
| `ecosystem` | 20 | Thin; a *third* "ecosystem" concept alongside root `ecosystem/` and `enterprise_hub` |
| `enterprise` | 17 | Thin |
| `executive_center` | 14 | Thin stub (dashboard.py, monitoring.py, twins.py) |
| `marketplace` | 17 | Thin |
| `workflow_studio` | 14 | Thin |

None of the 17 has its own dedicated test directory (coverage, if any, lives in root `tests/`).

**Sprint 32.2 — Platform Core vs verticals:** "Platform Core" is **composed** (Event Bus, workflow,
permissions, notifications, search, pricing, catalogs) — not a `platform_core/` package. Verticals
must use Core SoR via bridges; Auto local auth/notif/search/pricing are adapters (TD-61). Inventory:
`platform_architecture/core_inventory.py`. Docs: `PLATFORM_CORE.md`, `CORE_SERVICES.md`.

**Sprint CQ-11 cross-reference**: Enterprise City's district hierarchy (`docs/CITY_DISTRICTS.md`, CG-9,
extended CQ-11) was designed from the *frontend* City module without cross-checking this table — doing
so this sprint found that **the single largest real vertical here, `auto_marketplace` (420 files, GA
production), has no corresponding City district**, a bigger gap than any of CG-9's original three
speculative districts. `agro_marketplace`+`agro_enterprise` (244 files) and `port_erp`+`port_enterprise`
(266 files) are similarly real, sizeable, and City-unrepresented. See `docs/CITY_DISTRICTS.md`
D16–D19 and `docs/SPRINT_CQ_11_RESULT.md` for the full reconciliation.

---

## 3. Frontend architecture

Two entirely independent React apps exist, each with its own `package.json`, build tooling, and test
suite, with **no shared code, no npm workspace link, no shared component library** between them.

### 3.1 `src/web` — Enterprise Web Platform (v9.5.0) — the primary UI for the Python backend

React 19 + TypeScript + Vite + Tailwind + TanStack Query + React Router + Zustand + React Hook Form +
Zod + Chart.js + Socket.IO. Not wired into the root `package.json` — run standalone
(`cd src/web && npm install && npm run dev`, port 5180). Vite dev proxy forwards `/api` and
`/management` to `http://localhost:8080` (the Python `api/server.py`), confirming this is that
backend's SPA.

- **Structure**: split across `src/web/src/*` (core shell: `App.tsx`, `dashboard/`, `shell/`) and
  ~11 sibling feature packages at `src/web/<feature>/` stitched in by relative imports: `auth/`
  (Identity Center — users/roles/permissions/sessions/MFA), `command-center/` (Universal Command
  Palette, `/api/enterprise-command/v1`), `design-system/` (tokens, theme engine, component catalog),
  `navigation/` (menu engine, global search, ⌘K), `organization-brain/` (executive dashboard,
  `/api/organization-brain/v1`), `platform-builder/` (largest single area — AI Team, Concierge,
  Mission Control, Rendering/Theme/Digital Twin/Strategy/God Mode engines), `portals/` (customer/
  employee/owner portal shells), `release/` (RC dashboard), `vertical-federation/`, `workspace/`
  ("primary post-login entry point" — dashboard engine, widgets, layout). Plus 30+ single-purpose
  route directories under `src/web/src/*` (`enterprise-city`, `enterprise-control-tower`,
  `enterprise-data-fabric`, `enterprise-governance`, `enterprise-intelligence`, `enterprise-marketplace`,
  `enterprise-okr`, `enterprise-twin`, `enterprise-workflow`, `predictive-intelligence`,
  `self-learning-enterprise`, `autonomous-enterprise`, `ai-builder-studio`, `ai-os-chrome`,
  `ai-runtime`, `ai-team-collaboration`, `audit-vault`, `decision-flow`, `live-ops`, `pilot`, etc.) —
  each is a lazy-loaded route, mostly one directory per "executive surface" feature added sprint by
  sprint.
- **Integration Hub (Sprint 28.0)**: `src/web/src/integration-hub/` — shared app context, enterprise
  event bus (over `workspace/realtime/liveUpdates`), session restore coordinator, universal search
  registration, deep-link helpers. Wired from `shell/Providers.tsx` (`IntegrationHubBridge`). Does
  **not** replace auth/search/notification stores — orchestrates them. See `docs/INTEGRATION_HUB.md`.
  Related OS surfaces: `enterprise-desktop/`, `enterprise-city/`, `ai-production-studio/`,
  `live-dashboard/`, `command-center-runtime/`.
- **Runtime Engine (Sprint 28.1 / 28.2)**: `src/web/src/enterprise-runtime/` — global OS clock: metrics
  (CPU/memory/GPU/workers/jobs/providers/sessions/agents), Health Service singleton (one probe loop;
  `shell/enterprise/useRuntimeHealth` re-exports), Job Manager, AI agent runtime entities, live
  monitors on Desktop/Dashboard/CC/Production/City. **28.2** adds `productionRuntime` (queue lanes,
  workers, retry, analytics, universal pipelines) without a second job engine. **28.3** adds
  Enterprise AI Studio (`/ai-studio`) as a thin composition over Production + Runtime
  (projects, prompt collections, generation history). **28.4** completes Desktop Window Manager.
  **28.5** adds Enterprise Shell (`shell/enterprise` runtime · module registry · prefs · unified
  search/activity · ShellRuntimeBar) as the SPA chrome entry without replacing WM/Runtime.
  **28.6** adds Command Runtime (`src/runtime/commandRuntime`) — Palette/Shell/Desktop execute
  through one registry with history, permissions, and `command.*` Event Bus events.
  **28.7** elevates Command Runtime to the platform execution engine: undo/redo · macros ·
  AI intent routing · remote policy scopes · launcher registry IDs · analytics ·
  `/command-runtime` inspector.
  **28.8** adds Workflow Runtime (`src/runtime/workflowRuntime`) — single workflow engine over
  Command Runtime + Event Bus (`workflow_update`), template seeds, node engine, sessions,
  `/workflow-runtime` inspector. See `docs/WORKFLOW_RUNTIME.md`, `docs/WORKFLOW_ENGINE.md`,
  `docs/SPRINT_28_8_RESULT.md`.
  **28.9** adds Automation Engine (`src/runtime/automation`) on top of Workflow Runtime —
  triggers · queue · policies · scheduler · history · `/automation` Automation Center.
  See `docs/AUTOMATION_ENGINE.md`, `docs/AUTOMATION_QUEUE.md`, `docs/SPRINT_28_9_RESULT.md`.
  **29.0** adds Enterprise Business Network (`src/runtime/businessNetwork` + Hub
  `applications/enterprise_hub/business_network`) — profiles · relationships · graph ·
  communication foundation · verified document links · City facades · permissions ·
  EventBus `business_network_update` · REST `/api/enterprise-ebn/v1` · `/business-network`.
  See `docs/BUSINESS_NETWORK.md`, `docs/BUSINESS_NETWORK_API.md`, `docs/SPRINT_29_0_RESULT.md`.
  **29.1** adds Digital Citizen Runtime (`src/runtime/digitalCitizen` + Hub
  `applications/enterprise_hub/digital_citizen`) — citizen profiles · org membership ·
  workspace · personal AI registry · presence · activity · permissions · City facades ·
  EventBus `digital_citizen_update` · REST `/api/enterprise-edc/v1` · `/digital-citizens`.
  See `docs/DIGITAL_CITIZEN.md`, `docs/DIGITAL_CITIZEN_API.md`, `docs/SPRINT_29_1_RESULT.md`.
  **29.2** adds Life Engine (`src/runtime/lifeEngine`) — living ecosystem over Citizens ·
  EBN · Workflow · Automation: life events · timelines · building occupancy · movement ·
  meetings · vehicles · project participation · City runtime API · EventBus
  `life_engine_update` · `/life-engine`. See `docs/LIFE_ENGINE.md`, `docs/SPRINT_29_2_RESULT.md`.
  **29.3** adds Asset Runtime (`src/runtime/assetRuntime`) — enterprise assets (buildings ·
  fleet · IT · IP · docs · AI) with ownership · location · lifecycle · permissions ·
  City asset queries · EventBus `asset_runtime_update` · `/assets`.
  See `docs/ASSET_RUNTIME.md`, `docs/SPRINT_29_3_RESULT.md`.
  **29.4** adds Spatial Runtime (`src/runtime/spatialRuntime`) — Odessa Digital Twin
  spatial foundation (hierarchy · locations · districts · relationships · routing ·
  City spatial query) · EventBus `spatial_runtime_update` · `/spatial` · no map rendering.
  See `docs/SPATIAL_RUNTIME.md`, `docs/SPATIAL_RUNTIME_API.md`, `docs/SPRINT_29_4_RESULT.md`.
  **29.5** adds City Visualization Runtime (`src/runtime/cityVisualization`) — runtime
  bridge for future 2D/3D Digital Twin clients (building/district/citizen/asset visual
  state · scene cache · LOD · event stream) · EventBus `city_visualization_update` ·
  `/city-visualization` · no graphics engine. See `docs/CITY_VISUALIZATION_RUNTIME.md`,
  `docs/CITY_VISUALIZATION_RUNTIME_API.md`, `docs/SPRINT_29_5_RESULT.md`.
  **29.6** adds Interaction Runtime (`src/runtime/interactionRuntime`) — selection ·
  context actions · search/navigation · sessions/history over living City runtimes ·
  EventBus `interaction_runtime_update` · `/interactions` · reusable by future clients.
  See `docs/INTERACTION_RUNTIME.md`, `docs/INTERACTION_RUNTIME_API.md`, `docs/SPRINT_29_6_RESULT.md`.
  **29.7** adds Intelligence Runtime (`src/runtime/intelligenceRuntime`) — advisory
  insights · recommendations · risks · trends · patterns from live City activity ·
  EventBus `intelligence_runtime_update` · `/intelligence` · **no autonomous execution**.
  See `docs/INTELLIGENCE_RUNTIME.md`, `docs/INTELLIGENCE_RUNTIME_API.md`, `docs/SPRINT_29_7_RESULT.md`.
  **29.8** adds Orchestrator Runtime (`src/runtime/orchestrator`) — registry · dependency
  graph · health · scheduler · event coordinator over existing runtimes (additive only) ·
  EventBus `orchestrator_runtime_update` · `/orchestrator`.
  See `docs/ORCHESTRATOR_RUNTIME.md`, `docs/ORCHESTRATOR_API.md`, `docs/SPRINT_29_8_RESULT.md`.
  **29.9** adds Enterprise Kernel (`src/runtime/kernel`) — platform bootstrap · lifecycle ·
  config/feature flags · health aggregation · diagnostics · isolated recovery ·
  EventBus `kernel_runtime_update` · `/kernel` · wraps Orchestrator startup (no business logic).
  See `docs/KERNEL_RUNTIME.md`, `docs/KERNEL_API.md`, `docs/KERNEL_BOOT_SEQUENCE.md`,
  `docs/KERNEL_DIAGNOSTICS.md`, `docs/SPRINT_29_9_RESULT.md`.
- **Routing**: `src/web/src/App.tsx`, `react-router-dom`, almost all routes behind `ProtectedRoute`.
  ~25 `/platform-builder/*` sub-routes alone; plus `/workspace/*` (including per-vertical live pages:
  auto, beauty, cafe, agro, legal, crypto, drone), `/portals/*`, `/identity/*`, `/pilot*`, `/demo/*`.
- **State**: Zustand stores in 11+ files (auth, workspace, nav, theme, shell layout, preferences,
  notifications, i18n, module catalog). **TanStack Query is installed and `QueryClientProvider` is
  wired in `shell/Providers.tsx`, but zero `useQuery`/`useMutation` calls exist anywhere in `src/web`**
  — the data-fetching library is present but unused; all backend calls go through raw `fetch(`
  (36 files) via `webConfig.ts`'s ~30 named API prefixes.
- **Auth fallback**: `identityApi.ts` soft-probes the backend and falls back to a Demo Auth Provider
  when unreachable, controlled by `VITE_DEMO_AUTH` — **on by default in dev**.
- **Tests**: all `.test.ts` (config/registry/store unit tests — `foundation.test.ts` is 1259 lines).
  **No `.test.tsx` component/route-render tests exist** — nothing renders the actual React tree in a
  test.
- **Dead doc references**: `src/web/README.md` points to `docs/SPRINT_27_1_1_AUTH_RECOVERY.md` and
  `docs/SPRINT_27_1_RESULT.md` inside `src/web/docs/` — that directory does not exist.

### 3.2 `platform_console` — Enterprise Control Center (v2.0.0) — the UI for the *TS kernel*, not the Python backend

React 19 + dnd-kit + Chart.js + Zustand + TanStack Query + Tailwind 4, wired into the root
`package.json` (`install:console`, `build:console`, `test:console`, `console`/`dev` scripts) — this
app, not `src/web`, is the one integrated into the monorepo's top-level build.

- **Talks to two different backends**: (1) `/management/*` REST (same `/management/identity/login`
  endpoint `src/web` also calls — the only concrete coupling point between the two frontends, and
  even that is duplicated code, not shared code); (2) a separate "Runtime" HTTP+WS server at
  `http://localhost:3000` / `ws://localhost:3000/ws` (`services/runtimeApi.ts`,
  `hooks/useRuntimeSocket.ts`) — this is the ADOS TS kernel's own `RuntimeServer` (§6). No demo/mock
  fallback exists; README states "Requires Runtime at http://localhost:3000 (live data only)."
- **Routing gap**: 10 page files exist under `src/pages/` but are never imported into `App.tsx`'s
  route tree (`AiMemoryPage`, `AiPage`, `AiSkillsPage`, `AiWorkflowsPage`, `KnowledgeBasePage`,
  `LoginPage`, `ManagementPage`, `MigrationDashboardPage`, `PluginsPage`, an unrouted `SettingsPage`
  distinct from the routed `OsSettingsPage`). `AdminShell.tsx` and `components/auth/ProtectedRoute.tsx`
  are also defined but never referenced — **no route currently enforces login/role checks** despite
  `authStore` supporting it.
- **State**: unlike `src/web`, TanStack Query is genuinely used for data fetching across ~22 files.
- **Tests**: mix of `.ts` and `.tsx` (`dashboard.test.tsx`, `routing.test.tsx` actually render
  components/routes — more substantive than `src/web`'s test suite).

### 3.3 Cross-app duplication (concrete)

Both apps independently implement: a `DashboardPage.tsx` landing page, a Zustand `authStore.ts`, and a
call to `POST /management/identity/login` — with zero shared code (no common package, no path alias
crossing the trees). This is copy-pasted pattern, not shared library — see also §7 (Dashboards).

---

## 4. Providers

- **`src/providers`** (`@ados/providers`, part of the TS kernel ecosystem, §6): `ProviderGateway.ts`
  (registers/selects providers by capability), `ProviderRegistry.ts`, `BaseProvider.ts`,
  `adapters/builtin.ts` + `adapters/CursorProvider.ts` — explicitly **mock** providers (Cursor/OpenAI/
  Claude/GitHub/Local LLM), commented "no real API keys." No dependents besides `chat_bridge`/`voice`
  within the same TS ecosystem.
- **`platform_integrations/`** (Python) — "single entry point for external systems," exposes
  `IntegrationService` and `register_integration_routes` — this is the actual external-system
  integration point used by the Python backend's `/management/v1` surface; unrelated to `src/providers`.
- **`.cursor/rules/ados-architecture.mdc`**'s "Provider Layer" (Cursor, GitHub, OpenAI, Claude,
  Obsidian, Telegram, WhatsApp) describes the intended role of `src/providers`, not
  `platform_integrations` — two different documents describe two different "provider" concepts under
  the same platform name.
- **Sprint CG-8 addition — the real Python-side LLM provider layer** (a fourth "provider" concept,
  distinct from all three above): root-level `openrouter.py` is a genuine `aiohttp`-based OpenRouter
  integration, actively imported by `handlers.py` and 7+ `services/pg_*` engines — **the only real LLM
  provider call anywhere in this codebase**. `platform_ai/provider_manager.py`/`model_registry.py`
  separately register `openai`/`anthropic`/`google`/`local_llama`/`deepseek` entries, but every one
  resolves to a `MockAIProvider` (`platform_ai/provider_base.py`) — no SDK, no credentials, no network
  call (`requirements.txt` has no `openai`/`anthropic`/`google-generativeai`/`litellm` package).
  `platform_integrations/provider_manager.py`'s `OPENAI` entry is separately bootstrapped
  `enabled=False, description="Future provider"`. Full detail: `docs/AI_PROVIDER_LAYER.md`.

## 5. AI runtime

Two disconnected AI-agent stacks exist:

1. **Python `platform_*` chain** (used by the actual bot/backend): `platform_memory` →
   `platform_orchestrator` (+ `platform_agents`, near-duplicate exports, §7) → `platform_workflow`/
   `platform_tools` → `platform_reasoning`/`platform_planning`/`platform_decision` →
   `platform_learning`/`platform_collaboration`. This is the AI stack described in `CLAUDE.md`'s
   "AI-first development" principle.
2. **TS `src/orchestrator` (`@ados/orchestrator`)** — `AiOrchestrator.ts` (routes tasks to agents via a
   `ProviderGatewayPort`), `BaseAgent.ts`, `AgentRegistry.ts`, `collaboration/CollaborationEngine.ts`
   (own `SharedContext`/`Timeline`), `agents/builtin.ts` (mock Developer/Business/Marketing/Research/
   CRM/Finance/Production agents). Consumed only by `chat_bridge`, `voice`, `execution`, and `kernel`
   within the TS ecosystem — never by Python code.
3. **A third, independent agent/team concept** inside `applications/platform_builder/ai_team/` and
   `ai_builder/` (`team_center.py`, `catalogs.py`, `registry.py`, `wizard.py`) — zero references to
   `platform_orchestrator` from this application.

These three "AI runtimes" do not call each other. See §7 for the full list of overlapping AI-adjacent
naming (memory, orchestrator, learning, knowledge graph).

**Sprint CG-8 addition — a fourth and fifth real system this list didn't yet name:**
`platform_ai_os` (Sprint 27.1, "Multi-Agent OS": real Executive layer, Agent Registry 2.0, a
Communication Bus at `/agent-bus`, a Task Orchestrator at `/tasks` — DAG, parallel/sequential/
conditional, retry/rollback/timeout — a Memory Manager at `/memory-layers`, and a Collaboration
protocol at `/collaborate` — discuss/vote/select_best/critique/merge) and `applications/ai_os`
(Sprint 12.4, thinner: Kernel/Bus/Runtime/Memory, `kernel.py`/`bus.py`/`runtime.py`/`memory.py`) **both
answer requests under the same `/api/ai-os/v1` prefix** — this is the exact collision `TD-07`
already tracks, now attributable to these two specific real packages rather than left as an
abstract "three owners" note. `platform_ai_os`'s Task Orchestrator was not confirmed by this
research to be independent of `platform_workflow` (§13's "Workflow engines" bullet) or the same
code — flagged as the single highest-priority verification item across this whole document's AI
section. Full detail: `docs/AI_OS.md`, `docs/AI_AGENT_LIFECYCLE.md`, `docs/AI_COLLABORATION.md`,
`docs/AI_MEMORY.md`, `docs/AI_PROVIDER_LAYER.md`, `docs/SPRINT_CG_8_RESULT.md` (all Sprint CG-8).

**Sprint CQ-14 confirmation** — item 1's `platform_reasoning`/`platform_planning`/`platform_decision`/
`platform_learning` chain, previously listed only as part of the "intended" AI stack, is now confirmed
**real and cross-package-wired**: `ReasoningEngine.reason()`, `PlanningEngine.plan()`,
`DecisionEngine.decide()`, and `LearningEngine.learn()` are called from real application code
(`applications/auto_marketplace/crm/ai_assistant.py`, `applications/auto_marketplace/
business_intelligence/ai_insights.py`, `platform_collaboration/integrations.py`,
`platform_observability/metrics_manager.py`) — not dead code. **Equally important**: every strategy in
this chain (`RuleBasedStrategy`, `ChainOfThoughtStrategy`, etc., `platform_reasoning/strategies/
builtin.py`) is deterministic keyword/regex matching and fixed-weight arithmetic — not statistical or
LLM-based reasoning — and `platform_predictive_intelligence`'s real `bootstrap()` explicitly sets
`ai_may_act: False`. Also newly confirmed real and tested: `applications/platform_builder/
collaborative_ai/` (Sprint 28.8, `tests/test_collaborative_ai_28_8.py`) — a genuine Decision Engine
(alternatives/pros/cons/risk/recommendation/business impact) — and the real EP-06 Decision Chain UX
(`docs/EP_06_ENTERPRISE_INTELLIGENCE.md`) already threading through Dashboard/Control Tower/Mission
Control/Concierge/Builder/Marketplace/CRM/Knowledge/AI Team/City/Twin. Full detail:
`docs/ENTERPRISE_INTELLIGENCE_CORE.md`, `docs/AUTONOMOUS_AI.md`, `docs/ETHICS_GOVERNANCE.md`,
`docs/SPRINT_CQ_14_RESULT.md` (all Sprint CQ-14).

## 6. MCP (Model Context Protocol)

`src/mcp` (`@ados/mcp`) is a real MCP-shaped implementation: `MCPServer.ts` (JSON-RPC), `MCPGateway.ts`,
`MCPTransport.ts` (stdio/http), `MCPConfig.ts` (loads root `config/mcp.config.json`), auth/permission/
session modules, and built-in tools/resources/prompts (`system.status`, `ados://architecture`,
`explain_module`).

- **It has zero `@ados/*` package dependencies** — it never imports `@ados/orchestrator` or
  `@ados/providers` directly. Instead every tool maps to a generic `RuntimeInvoker` callback
  (`(method, path, body, search) => …`), and the actual wiring happens only in
  `src/kernel/runtime/RuntimeServer.ts`, which points `mcp.setRuntimeInvoker(...)` back at the
  kernel's own in-process HTTP API. MCP is a thin protocol wrapper around the kernel's Runtime Server,
  not an independent integration surface.
- **Config**: `config/mcp.config.json` — host `127.0.0.1`, port `3100`, `runtime.baseUrl:
  http://127.0.0.1:3000`, transport `http+stdio`, dev auth token `ados-mcp-dev-token`.
- **Reachability**: nothing on the Python side, in `src/web`, or in `platform_console` references
  port 3100, `@ados/mcp`, or `mcp.config.json`. It is reachable only via `npm run ados` (kernel boot)
  or the package's own `npm test`/`npm run build`.

## 7. Voice

`src/voice` (`@ados/voice`) implements a genuine speech→intent pipeline: `SpeechPipeline.ts`
(Recorder → Recognizer → IntentDetector → CommandInterpreter → ChatBridge), plus session/history/
settings/wake-word support classes. Depends on `@ados/chat-bridge`, `@ados/orchestrator`,
`@ados/providers`.

- Real, non-trivial code, but `VoiceRecorder` only accepts programmatic PCM/base64 frames — **no OS
  microphone integration** — functions as a mock/simulated pipeline.
- Referenced only within the TS ecosystem (`src/kernel`, `src/chat_bridge`) and two docs
  (`docs/ados_os/voice_module.md`, `docs/ados_os/chatgpt_bridge.md`). `platform_console` has a
  `VoiceCenterPage`/route and a "ChatGPT Bridge" label but **zero `@ados/*` package dependencies** —
  it talks to voice/chat-bridge functionality (if at all) only via the kernel's HTTP Runtime API, never
  by importing the TS package directly.
- No Python file references `@ados/voice` or anything under `src/voice`.

## 8. Memory

Two unrelated "Memory" concepts:

1. **`platform_memory/`** (Python) — "AI context engine for all agents": `MemoryService`,
   `ContextAssembler`, `context_assembler.py`, `summarizer.py`, `providers/`, `repositories/`,
   `search/`. This is the memory layer in the intended AI stack (§5).
2. Also in Python: **`platform_ai/memory/`** — a *second, full parallel memory stack*
   (`memory_manager.py`, `memory_store.py`, `memory_retriever.py`, `memory_ranker.py`,
   `memory_registry.py`, `memory_service.py`) — note `platform_memory` and `platform_ai/memory` both
   independently define a module literally named `memory_service.py`.
3. Further "memory"-named code exists in `ecosystem/assistant/global_memory/service.py`,
   `applications/ecosystem/memory.py`, `platform_enterprise_knowledge_graph/memory/__init__.py`,
   `platform_enterprise_ai_orchestrator/memory/__init__.py`, and `applications/ai_os/memory.py`.
4. Root `memory.db` (577 KB SQLite file at repo root) — likely a leftover artifact from an early
   pre-Postgres-only phase; worth confirming it is not read by anything live given the
   `POSTGRES_ONLY=true` / no-sqlite policy (§10 candidate check).

None of these are cross-wired — each is its own independent implementation under a name that suggests
it's "the" memory system.

**Sprint CG-8 addition:** `platform_enterprise_knowledge_graph/memory/` answers a real, separate API
prefix — `GET/POST /api/enterprise-kg/v1/memory` (per `docs/AI_MEMORY.md`'s preserved implementation
reference) — with its own memory-type taxonomy (Long-Term/Conversation/Business/Project/Decision/
Workflow/Memory Version Control), distinct from `platform_ai_os`'s six-layer Memory Manager (§5) —
a **fourth** independently-real memory surface once that one's counted too. More consequentially:
`platform_ai/memory/`'s `memory_embeddings.py` defines `OpenAIEmbeddingProvider`/
`LocalEmbeddingProvider`, but **both call the same `_hash_embed()` function** — a deterministic
SHA-256 hash, not a real embedding call — meaning the one real-looking knowledge/semantic-search chain
in this survey (`knowledge_base.py`/`document_store.py`/`knowledge_index.py`/`knowledge_search.py`)
cannot actually do semantic similarity search today. No real vector database (pgvector/faiss/
chromadb/pinecone/weaviate/qdrant) exists anywhere in `requirements.txt` or imports — one repository
comment (`platform_memory/repositories/in_memory_semantic_repository.py`) names these as aspirational,
unimplemented swap targets. Full detail: `docs/AI_MEMORY.md`.

## 9. Kernel

`src/kernel` (`@ados/kernel`, v1.4.0) is the root of the standalone TS "ADOS OS" runtime — the only
package in that ecosystem meant to run as a live process.

- **Composition**: `Kernel.ts` (entry point: start/stop/dispose/getHealth) wires `BootLoader.ts`
  (boots event bus → provider/runtime/memory/plugin hosts → extra services), `ServiceRegistry.ts`
  (DI-style register/resolve), `HealthMonitor.ts` (aggregates `.health()` across services),
  `Lifecycle.ts` (Created→Initialized→Started→Paused→Stopped→Disposed state machine).
- **Sub-runtimes inside kernel**: `event_bus/` (a full pub/sub bus — Event, EventBus, EventDispatcher,
  EventFilter, EventHistory, EventPublisher, EventRegistry, EventSubscriber) *plus a second, separate*
  `events/EventBus.ts` (simpler/older, coexists with `event_bus/` — an internal duplicate within the
  same package); `service_mesh/` (ServiceMesh, ServiceDiscovery, ServiceRouter, LoadBalancer,
  ServiceResolver, ServicePolicy — an in-process mesh abstraction); `workflow/` (WorkflowEngine,
  WorkflowScheduler, WorkflowExecutor, WorkflowInstance, WorkflowValidator — yet another,
  fourth/fifth, "workflow engine" concept in the repo, disconnected from Python's `platform_workflow*`
  packages, §7); `runtime/RuntimeServer.ts` (the HTTP+WS server that exposes kernel/orchestrator/
  providers/chat/voice/mcp/execution as REST endpoints — this is what `platform_console` actually
  talks to).
- **Process entry**: `main.ts` constructs Providers→Orchestrator→ChatBridge→Voice→MCP→Execution,
  boots the Kernel, starts `RuntimeServer` on `ADOS_PORT` (default **3000**). Started only via
  `npm run ados` (root `package.json` → `src/kernel`'s own `ados` script: `build && node dist/main.js`).
- **Reachability**: confirmed via repo-wide grep — no Python file, no `docker-compose.yml` service, no
  `src/web` code references `src/kernel`, port 3000, or `dist/main.js`. `platform_console` is the one
  real external consumer (via HTTP/WS to port 3000), but even it holds no `@ados/*` package
  dependency — it calls the kernel over the network, not via import.
- **`@ados/execution` detail** (Sprint CG-7 addition — real mechanics not previously described here):
  `src/execution/` is a genuine, compiled DAG task executor, not a "workflow engine" in the §13 sense
  — its own file header states *"Executes ChatGPT engineering specs; never invents architecture,"*
  i.e. it splits an `EngineeringSpecification` into `ExecutionTask`s per `AgentRole`
  (developer/ui/documentation/qa/review/build/deploy). Real, working parts: `ExecutionQueue`
  (priority-sorted map), `DependencyResolver` (Kahn's-algorithm topological sort + parallel-wave
  computation, with cycle detection), `ExecutionScheduler.runPlan` (runs each ready wave concurrently
  via `Promise.all`, polls every 10ms while anything is still running, no automatic retry on
  failure), and `ExecutionHistory` (bounded in-memory array, max 500 entries — no durable persistence).
  See `docs/AUTOMATION_ENGINE.md`/`docs/WORKFLOW_RUNTIME.md` (Sprint CG-7) for the full comparison
  against the Python-side `platform_workflow/` engine, which independently converged on the same
  topological-sort algorithm for a different domain.

## 10. Web Platform — summary comparison

| | `src/web` | `platform_console` |
|---|---|---|
| Backend | Python `api/server.py` (`/api`, `/management`) | Python `/management/*` **and** TS kernel `RuntimeServer` (port 3000) |
| Wired into root `package.json` | No — standalone | Yes (`install:console`, `console`, `dev`) |
| Primary users | Owners/operators/verticals (business-facing) | ADOS OS operators (kernel/agent/workflow-facing) |
| Data fetching | `fetch()` only; TanStack Query installed but unused | TanStack Query actively used |
| Auth enforcement | `ProtectedRoute` wraps nearly all routes | Auth scaffolding exists but **not wired into the live route tree** |
| Test depth | Unit-only (`.test.ts`), no component render tests | Mix, includes `.tsx` route/component render tests |

Both are legitimate, actively-developed apps — the overlap is in *concept* (dashboard, auth,
"control/command center" branding) and in independently re-implementing the same login call, not in
one being a stale duplicate of the other.

---

## 11. Dependencies between modules

### 11.1 Governed dependency direction (Python backend, as designed)

```
Platform core → Providers → AI services → Business modules → Vertical solutions → Customer applications
```
Enforced by `platform_architecture/` and scored by `scripts/validate_architecture.py`
(→ `ARCHITECTURE_REPORT.md`). Last generated report: **Grade FAIL**, score 95.45/100, 956 modules /
3084 edges / 0 cycles, **4 critical boundary violations** — all `env_access_outside_center`:
`platform_security/config.py:23,24` and `platform_security/secrets.py:30,80` call `os.environ`
directly instead of going through `ConfigurationCenter`. Plus **29 non-critical
`reverse_layer_dependency` violations**, including:
- `database/engine.py` importing services via `platform_configuration.configuration_center`
- several `platform_operations/*` files importing via `platform_management.*`
- `platform_identity/*` (policy_engine, permission_service, role_service, audit_hooks) importing via
  `platform_legacy`
- **9 files under `repositories/`** (`base_repository.py`, `assignment_score_repository.py`,
  `request_repository.py`, `manager_pool_repository.py`, `owner_repository.py`,
  `workflow_execution_repository.py`, `platform_metrics_repository.py`, `manager_repository.py`,
  `kpi_repository.py`) importing from `src/platform/layers/base_repository.py` — the data layer
  reaching into the separate `src/` Python tree.

### 11.2 Cross-tree dependency (the one confirmed real link)

`repositories/base_repository.py` → `src/platform/layers/base_repository.py`. This is the single
confirmed structural dependency of the root Python backend on the `src/domains|platform|verticals|
events` tree. Everything else in that tree (`src/domains/*`, `src/verticals/*`) appears to be an
older/parallel domain model not otherwise wired into `repositories/`/`services/` (not exhaustively
traced beyond this one entry point).

### 11.3 Cross-system dependency (TS kernel ecosystem)

```
@ados/providers ──┐
                   ├──> @ados/chat-bridge ──> @ados/voice
@ados/orchestrator ┘                    └──> (voice contracts)
@ados/orchestrator ──> @ados/execution
(all six) ──> @ados/kernel  (prebuild chains all of them, kernel depends on all)
@ados/mcp  — no @ados/* deps; wired only via kernel's RuntimeInvoker callback at runtime
```
This graph is entirely internal to `src/`'s TS packages and has **no edge** into the Python
dependency graph in §11.1 — confirmed by grep (§6, §8, §9).

### 11.4 Frontend → backend dependency

- `src/web` → Python `api/server.py` (`/api`, `/management`) via Vite proxy to `:8080`.
- `platform_console` → Python `/management/*` (shared login endpoint) **and** TS kernel
  `RuntimeServer` (`:3000`/`:3000/ws`) — the only frontend with a live dependency on the TS ecosystem.

---

## 12. Technical debt

(Cross-referenced with the repo's own `docs/TECHNICAL_DEBT_REPORT.md`, TD-01…TD-16, and
`docs/ARCHITECTURE_INVENTORY.md`'s per-subsystem status codes — this section adds the concrete file
evidence behind those IDs plus items not yet tracked there.)

1. **4 critical + 29 non-critical architecture-governance violations** currently failing CI's
   architecture gate (§11.1) — `platform_security` bypassing `ConfigurationCenter`, and 9
   `repositories/*` files depending on the `src/` tree instead of a root-local base class.
2. **Two migrations directories** (`./migrations` vs `./database/migrations`) — unclear which is
   authoritative for new Alembic revisions.
3. **`database_legacy.py` (11,205 lines) still imported by non-legacy code**, including
   `database/__init__.py` itself, `platform_architecture/*`, and `src/platform/layers/
   architecture_policy.py` — the legacy-isolation policy in `LEGACY_MIGRATION.md` ("direct imports of
   `database_legacy` forbidden outside `platform_legacy/`") is violated by the modern `database/`
   package's own `__init__.py`.
4. **`config.py` (legacy facade) is still directly imported** by `bootstrap.py`, `startup.py`,
   `openrouter.py`, `fsm_storage.py`, `database_legacy.py`, and several `*_handlers.py` files, rather
   than those callers going through `platform_configuration.configuration_center` directly — the
   facade is permanent load-bearing infrastructure, not a transitional shim in practice.
5. **~146 `# TODO: future implementation` markers**, concentrated in `database_legacy.py` (85),
   `handlers.py` (~40), and `keyboards.py` (17) — unfinished CRM/report/AI-context/UI features in the
   legacy monolith that nothing has replaced yet.
6. **`src/web`'s TanStack Query is installed and wired but has zero actual usage** — every network
   call goes through raw `fetch()` instead, meaning none of the caching/retry/invalidation behavior
   the dependency exists for is actually in effect.
7. **`src/web` has no component/route-render tests** (`.test.tsx` count: 0) — all frontend tests are
   unit tests of config objects, registries, and stores; a broken render would not be caught by the
   existing suite.
8. **`src/web/README.md` references two non-existent files** (`docs/SPRINT_27_1_1_AUTH_RECOVERY.md`,
   `docs/SPRINT_27_1_RESULT.md` under `src/web/docs/`, which doesn't exist).
9. **`platform_console` has 10 built page components that are never routed**, plus an unused
   `AdminShell.tsx`/`ProtectedRoute.tsx` — meaning **no route in `platform_console` currently enforces
   authentication**, despite `authStore` supporting it.
10. **Header-only auth** across `/management/*` and vertical APIs pending full Identity Center token
    integration (per `docs/API_CORE_AUDIT.md`, `docs/PRODUCTION_READINESS_AUDIT.md`).
11. **No industry-facing customer web portal exists for any vertical** (Automotive, Agriculture,
    Beauty, Cafe, Crypto, Legal, Drone) per `docs/WEB_READINESS_AUDIT.md` — `src/web/portals/` is a
    thin shell, not vertical-specific.
12. **Root `memory.db`** (SQLite, 577 KB) sitting at repo root despite the repo's `POSTGRES_ONLY=true`
    / `scripts/check_no_sqlite.py` policy — worth confirming it's a dead artifact, not a live path.
13. **`container.py` DI scaffold has never been adopted** — zero production consumers after being
    introduced (§8) — either commit to wiring it in or stop carrying it as aspirational scaffolding.

**Overnight Architecture Audit addition** — a full-repo audit (documentation only) extended
`docs/TECH_DEBT.md` with twelve new items, TD-47–TD-58: the largest is confirming `src/domains` (141
real Python files) has near-zero external usage repo-wide — the largest undocumented architectural
fork found anywhere in this repo, larger by file count than most single `platform_*` package. Also
newly tracked: no real backend `Project` entity exists despite the real Sprint 24.2 knowledge graph
already naming `"project"` as a first-class ontology entity (TD-51); a second, unvalidated JWT-secret
read path in `platform_configuration/configuration_center.py:100` alongside the correctly-validated
one in `platform_identity/jwt_service.py` (TD-57, pending consumer trace, not confirmed exploitable);
and ~100 top-level repo-root directories with two bare namesake-collision risks, `./platform` and
`./workflow`, sitting alongside their prefixed near-namesakes (TD-56). Full detail:
`docs/ENTERPRISE_FULL_AUDIT.md`, `docs/SECURITY_REVIEW.md`, `docs/SCALABILITY_REVIEW.md`,
`docs/ARCHITECTURE_SMELLS.md`, `docs/TOP_20_CRITICAL_FIXES.md`, `docs/TOP_100_RECOMMENDATIONS.md`,
`docs/ENTERPRISE_V1_READINESS.md`, `docs/EXECUTIVE_SUMMARY.md`, `docs/FINAL_AUDIT_RESULT.md`.

**Sprint 29.10 — Master Implementation Roadmap** — documentation-only consolidation of the overnight
audit into a single forward plan. **No production code changed.** Canonical next-step document:
[`docs/MASTER_IMPLEMENTATION_ROADMAP.md`](./MASTER_IMPLEMENTATION_ROADMAP.md) (executive summary,
prioritized backlog, dependency graph, debt-by-category, effort bands, subsystem scores 0–10,
Sprints **30–34** implementation sequence, Enterprise V1 success criteria). Forward Sprints 30–34
are **not** the historical Platform Builder 30.x–34.0 pilot series (see
`docs/ARCHITECTURE_AUDIT_INDEX.md` for that history).

**Sprint 30.0 — Security & Governance Hardening** — JWT secret unification (`platform_security/jwt_secrets.py`),
Platform Builder live identity + gated header auth (`ALLOW_HEADER_AUTH`), tenant filter defaults +
audit script, Permission Engine facade, HTTP security middleware stack, AI likeness consent gate
(TD-46), startup `fail_fast` in production. Docs: `SECURITY_MODEL.md`, `AUTHORIZATION.md`,
`TENANT_ISOLATION.md`, `SPRINT_30_RESULT.md`.

**Sprint 30.1 — Enterprise Authentication & Security Foundation** — ISAM Google Sign-In (preferred Beta,
auto account creation), email/password register + reset, MFA optional + org policy, enterprise roles,
multi-session management, Owner Security Dashboard (RU), audit events. Docs: `AUTHENTICATION.md`,
`GOOGLE_AUTH.md`, `SESSION_MANAGEMENT.md`, `ROLE_MODEL.md`, `SPRINT_30_1_RESULT.md`; updated
`SECURITY_MODEL.md`.

**Sprint 30.2 — Enterprise Navigation & Russian UI** — Russian primary sidebar, Owner Mode dashboard
(`/owner`), top bar (search / company / language / role / notifications / AI), breadcrumbs, global
search RU index, quick actions, role switcher. Docs: `UI_NAVIGATION.md`, `OWNER_DASHBOARD.md`,
`ROLE_SWITCHER.md`, `GLOBAL_SEARCH.md`, `RUSSIAN_UI.md`, `SPRINT_30_2_RESULT.md`.

**Sprint 30.3 — Enterprise Beta Launch & First Visual Interface** — Beta Home on `/dashboard`,
Client/Dealer dashboards, invitation page, Google → first-run → role home, City preview strip,
Production Studio «Скоро будет доступно». Docs: `BETA_HOME.md`, `CLIENT_DASHBOARD.md`,
`DEALER_DASHBOARD.md`, `GOOGLE_LOGIN.md`, `FIRST_RUN.md`, `SPRINT_30_3_RESULT.md`.

**Sprint 30.4 — Enterprise City Visualization Beta** — Interactive City at `/enterprise-city`:
16 districts, building ops cards, pan/zoom/select/hover, Russian inspector, live health legend,
Owner God Mode, camera persistence. Docs: `CITY_ENGINE.md`, `CITY_RENDERER.md`,
`CITY_DISTRICTS.md`, `CITY_BUILDINGS.md`, `CITY_NAVIGATION.md`, `OWNER_CITY_MODE.md`,
`SPRINT_30_4_RESULT.md`.

**Sprint 30.5 — AI Agent Runtime & Production Studio** — AI Agent Center at `/ai-agents`,
10 default agents, task lifecycle (pause/resume/logs), pipeline stages, Production Studio RU CTAs
+ presentation/social studios, Owner AI dashboard, task security/audit. Docs: `AI_RUNTIME.md`,
`AI_AGENT_CENTER.md`, `PRODUCTION_STUDIO.md`, `TASK_PIPELINE.md`, `TASK_EXECUTION.md`,
`OWNER_AI_DASHBOARD.md`, `SPRINT_30_5_RESULT.md`.

**Sprint 30.6 — Enterprise Platform Integration & First Live Demo** — Single boot map, route
aliases (`/ai` `/city` `/production` `/health`), City district→module, Owner subsystems, unified
errors, Platform Health, Beta Live Demo. Docs: `PLATFORM_BOOT.md`, `LIVE_DEMO.md`,
`INTEGRATION_REPORT.md`, `BETA_CHECKLIST.md`, `SPRINT_30_6_RESULT.md`.

**Sprint 30.7 — Enterprise Workspace & Real Module Wiring** — Usable workspace shell: expanded RU
sidebar, Admin/Client/Dealer/Owner dashboards, Calendar/Tasks/Notifications ops pages, RU command
palette (Ctrl/Cmd+K), no dead nav links. Docs: `WORKSPACE.md`, `OWNER_WORKSPACE.md`,
`ENTERPRISE_NAVIGATION.md`, `COMMAND_PALETTE.md`, `SPRINT_30_7_RESULT.md`
(web Workspace track; PB Pilot Hardening remains `PILOT_HARDENING_30_7.md`).

**Sprint 30.8 — Enterprise Business Modules** — Operational CRM/Projects/Knowledge/Calendar/
Notifications/Drive/Marketplace pages in `src/web/src/enterprise-business/`, Auto CRM + EKP +
comms binds, live Owner metrics. Docs: `CRM.md`, `PROJECTS.md`, `KNOWLEDGE.md`, `CALENDAR.md`,
`NOTIFICATIONS.md`, `FILES.md`, `SPRINT_30_8_RESULT.md` (Beauty Pilot 30.8 remains separate).

**Sprint 30.9 — Enterprise Beta Hardening & AI Security** — Prompt firewall (web+APH), demo
auth gate, nginx headers/rate-limit/SPA, compose required secrets, tenant client guards.
Docs: `AI_SECURITY.md`, `API_SECURITY.md`, `BETA_HARDENING.md`, `INFRASTRUCTURE_SECURITY.md`,
`PRODUCTION_CHECKLIST.md`, `SECURITY_TEST_REPORT.md`, `SPRINT_30_9_RESULT.md`
(Beauty Pilot Execution 30.9 remains `BEAUTY_PILOT_EXECUTION_30_9.md`).

**Sprint 31.0 — Closed Beta Release Candidate** — First-run platform roles, Manager/Employee
dashboards, Closed Beta surface catalog, nav honesty (finance/AI Studio). Docs: `CLOSED_BETA.md`,
`FIRST_RUN.md`, `DEPLOYMENT.md`, `INSTALLATION.md`, `OPERATOR_GUIDE.md`, `BETA_RELEASE_NOTES.md`,
`SPRINT_31_0_RESULT.md` (Cafe Pilot 31.0 remains `CAFE_PILOT_EXECUTION_31_0.md`).

**Sprint 31.1 — Visual Polish, Interactive City & Enterprise UX** — City data-flow/online
indicators, Owner God Mode metrics (`deriveGodModeMetrics`), role dashboard polish strip, RU
studio chrome, motion skeletons. Docs: `ENTERPRISE_CITY_UI.md`, `OWNER_GOD_MODE.md`,
`VISUAL_SYSTEM.md`, `UI_GUIDELINES.md`, `SPRINT_31_1_RESULT.md` (Agriculture Pilot 31.1 remains
`AGRICULTURE_PILOT_EXECUTION_31_1.md` / `RELEASE_NOTES_31_1.md`).

**Sprint 31.2 — Integration Hub, n8n & AI Providers** — Extended provider registry, n8n bridge
(`n8n_bridge` + compose profile), APH bootstrap expansion (LiteLLM/OpenRouter/…), Production
Studio provider/cost/n8n launch. Docs: `INTEGRATION_HUB.md` (updated), `N8N_ARCHITECTURE.md`,
`AI_PROVIDERS.md`, `WORKFLOW_LIBRARY.md`, `PROVIDER_REGISTRY.md`, `SPRINT_31_2_RESULT.md`
(Legal Pilot 31.2 remains `LEGAL_PILOT_EXECUTION_31_2.md`).

**Sprint 32.0 — AI Production Studio Enterprise MVP** — Production Home, Brand Kit, Workflow
Builder UI, task queues with cost/tokens, `generateInStudio` → Runtime, Owner production
analytics. Docs: `PRODUCTION_STUDIO_V1.md`, `BRAND_KIT.md`, `AI_PIPELINES.md`,
`SPRINT_32_0_RESULT.md` (Enterprise Web Completion 32.0 remains
`ENTERPRISE_WEB_COMPLETION_32_0.md`).

**Sprint 32.1 — Enterprise Multi-Agent Operating System** — Expanded agent registry, lifecycle
phases, `agentOs` messaging/memory/collab/observe, AgentOsMonitor on Owner + Agent Center,
Production Studio AgentOS hook. Docs: `AGENT_OS.md`, `AGENT_RUNTIME.md`, `AGENT_REGISTRY.md`,
`AGENT_COMMUNICATION.md`, `AGENT_MEMORY.md`, `AGENT_SECURITY.md`, `SPRINT_32_1_RESULT.md`
(External Pilot 32.1 remains `SPRINT_REPORT_32_1.md` / pilot guides).

**Sprint 32.2 — Platform Core Governance** — Composed Core inventory (`core_inventory.py`),
sprint architecture review CI gate, Pricing / USC foundations (no UI), standards + categorized
debt registry. Docs: `PLATFORM_CORE.md`, `CORE_SERVICES.md`, `ARCHITECTURE_GOVERNANCE.md`,
`PLATFORM_STANDARDS.md`, `TECH_DEBT_REGISTRY.md`, `SPRINT_32_2_RESULT.md`
(External Pilot 32.2 remains `SPRINT_REPORT_32_2.md` / `PILOT_OPS_32_2.md`; CQ-32.2 review preserved).

**Sprint 32.3 — Enterprise Consolidation** — Canonical service registry, unified queue lanes
(ai/workflow/background/notification/render) + DLQ, secret policy (no n8n placeholder default),
Event Bus policy, enterprise metrics facade, consolidation scanner. Docs: `CANONICAL_SERVICES.md`,
`QUEUE_ARCHITECTURE.md`, `EVENT_BUS.md`, `SPRINT_32_3_RESULT.md`
(UX track 32.3.1–32.3.7 docs preserved — first entry / City / workspace).

**Sprint 32.4 — Enterprise Security Center (Zero Trust)** — `EnterpriseSecurityCenter` SoR,
continuous Zero Trust, AI/anti-parsing/external-AI/API/knowledge security facades, Incident + Audit
centers. Docs: `SECURITY_CENTER.md`, `ZERO_TRUST.md`, `SPRINT_32_4_RESULT.md`
(AI OS Experience 32.4 docs preserved — `AI_OS_EXPERIENCE_32_4.md`).

**Sprint 32.5 — Closed Beta Launch Preparation** — City destination hygiene, Owner live metrics,
`/security` → Security Center, Closed Beta docs pack. Docs: `CLOSED_BETA_GUIDE.md`,
`FIRST_USER_JOURNEY.md`, `KNOWN_LIMITATIONS.md`, `RELEASE_CHECKLIST.md`, `SPRINT_32_5_RESULT.md`
(Enterprise Intelligence 32.5 docs preserved — `ENTERPRISE_INTELLIGENCE_32_5.md`).

**Sprint 32.6A — First Local Launch Recovery** — `npm run dev:all`, API-only local runner,
Vite proxy hardening, `LOCAL_RUN.md` / `FIRST_LOCAL_RUN_REPORT.md`. Docs: `SPRINT_32_6A_RESULT.md`
(AI Team Collaboration 32.6 docs preserved).

**Sprint 32.6B — Zero-Touch Local Launch** — `events.tenant_id` → `tenants` FK registration,
auto Alembic on startup, Redis-optional health, `FIRST_SUCCESSFUL_LOCAL_RUN.md`. Docs:
`SPRINT_32_6B_RESULT.md`.

**Sprint 33.1 — Enterprise UX Revolution (Foundation)** — Simple/Pro mode, role workspaces,
context nav, AI Ctrl+K intents, Executive Summary dashboard. Docs: `ENTERPRISE_UX_33_1.md`,
`SPRINT_33_1_RESULT.md`. Frontend only.

**Sprint 33.2 — Intelligent Navigation** — Collapsible left-nav accordion (Workspace / Business /
AI / City / Platform / Owner). Docs: `INTELLIGENT_NAVIGATION_33_2.md`, `SPRINT_33_2_RESULT.md`.

## 13. Duplicate modules

Grouped by concept, with the concrete file evidence for each (facts only — the repo's own debt report
explicitly says *not* to merge most of these, given each serves a genuinely separate product; they're
listed here so the scope of the naming overlap is visible in one place):

- **Orchestrator / agents** — three disconnected systems: `platform_orchestrator/` (Python, used by
  the real bot backend) · `src/orchestrator/` (`@ados/orchestrator`, TS kernel ecosystem, used by
  nothing in Python) · `applications/platform_builder/ai_team/` + `ai_builder/` (a third, independent
  agent/team concept). `platform_agents/` additionally exports near-identical symbols to
  `platform_orchestrator` (`BaseAgent`, `BUILTIN_AGENTS`, `register_builtin_agents`).
- **Memory** — `platform_memory/` vs `platform_ai/memory/` (both independently define a
  `memory_service.py`) vs `ecosystem/assistant/global_memory/` vs `applications/ai_os/memory.py` vs
  `applications/ecosystem/memory.py` vs `platform_enterprise_knowledge_graph/memory/` vs
  `platform_enterprise_ai_orchestrator/memory/`.
- **Dashboards / control centers** — `applications/platform_builder/` alone has **four structurally
  near-identical directories**: `command_center/`, `control_center/`, `mission_control/`,
  `operations_center/` (each with a `catalogs.py` + engine file, same shape, different name). Plus
  `src/web` (10+ `dashboard/` subfolders across features) vs `platform_console` (the dedicated
  "Enterprise Dashboard" UI for the TS kernel, per `docs/ados_os/enterprise_dashboard.md`) — different
  products, overlapping name.
- **Workflow engines** — **Sprint CG-7 revision: at least six, not four**, independent implementations
  (deeper file-level research superseding the count below): `platform_workflow/` (singular — found to
  be the most internally coherent real engine: real `WorkflowEngine`, dependency-ordered execution,
  priority queue, retry/backoff, real event publishing, real human-task pause; missing only durable
  persistence, branching/loops, and a trigger surface), `platform_workflows/` (plural — the
  self-described "Unified Workflow Engine — single runtime for all business flows," not confirmed by
  this deeper pass to be more complete than the singular package despite the name), `platform_ai/
  workflows/` (a `WorkflowBuilder` that deserializes JSON/YAML into a `WorkflowDefinition` — a parser,
  not a generator), `platform_workflow_intelligence/`, `src/kernel/workflow/` (TS, `WorkflowEngine.ts` +
  scheduler/executor/instance/validator), and `applications/enterprise_hub/workflow/` +
  `workflow_intelligence/` — plus two disconnected agent registries (`platform_agents.registry` vs.
  `platform_orchestrator.agent_registry`) and two disconnected schedulers (`platform_jobs/` vs.
  `services/scheduler_cron.py`/`pg_scheduler_engine.py`), neither wired to any of the six engines above.
  Full detail, canonical-candidate recommendation, and a six-document implementation Bible:
  `docs/AUTOMATION_ENGINE.md`, `docs/WORKFLOW_RUNTIME.md`, `docs/TRIGGER_SYSTEM.md`,
  `docs/ACTION_LIBRARY.md`, `docs/VISUAL_WORKFLOW.md`, `docs/SPRINT_CG_7_RESULT.md` (all Sprint CG-7).
  Original (now superseded) count for reference — at least four: `platform_workflow/`,
  `platform_workflows/` ("Unified Workflow Engine — single runtime for all business flows"),
  `platform_workflow_intelligence/`, and `src/kernel/workflow/` (TS, `WorkflowEngine.ts` +
  scheduler/executor/instance/validator) — plus `applications/workflow_studio/` and
  `applications/enterprise_hub/workflow/` + `workflow_intelligence/`.
  **Sprint CG-9 addition:** the frontend's `src/web/src/enterprise-workflow/workflowTemplates.ts`
  (real, 9 static templates) gives each template a real `cityPath: CityBuildingId[]` field — a
  ready-made "which buildings does this workflow visit" shape — but it is confirmed to feed only the
  simulated `deriveWorkflowAutomation()` (that module's own header: "no new Workflow / Automation
  Engine / Store"), never a real running workflow from any of the six-plus engines above. One more
  concrete instance of this repo's broader "real-shaped data, simulated execution" pattern. Detail:
  `docs/CITY_DISTRICTS.md`/`docs/SPRINT_CG_9_RESULT.md` (Sprint CG-9).
  **Sprint CQ-19 addition — a seventh, frontend engine:** `src/web/src/runtime/workflowRuntime/` is a
  real, substantial node-graph executor (`WorkflowNodeKind`: sequential/parallel/condition/loop/delay/
  wait_event/ai_action/approval/http/webhook/script; real `WorkflowStatus`: idle/running/paused/
  waiting/completed/failed/cancelled) that composes only `commandRuntime`/`enterpriseEventBus` — no
  call into any of the six backend engines above. Also confirmed: none of the six backend engines has
  a tenant-configurable transition table; that pattern (`DealStage.allowed_next_stages`) is unique to
  the deal-pipeline collision below. Full detail: `docs/ENTITY_RECONCILIATION.md` §3,
  `docs/SPRINT_CQ_19_RESULT.md`.
- **Security / performance / testing "legacy vs enterprise" pairs** — `platform_security/` vs
  `platform_enterprise_security_verification/` (docstring: legacy unchanged); `platform_performance/`
  vs `platform_enterprise_performance_testing/` (docstring: legacy EPF unchanged); `platform_quality/`
  vs `platform_testing/` (docstring: does not duplicate) vs `applications/enterprise_hub/
  quality_assurance/` + `test_infrastructure/`.
- **Digital Twin / Simulation** — `platform_enterprise_digital_twin/` vs legacy "EDT" vs
  `applications/executive_center/twins.py` vs `applications/platform_builder/digital_twin/`;
  `platform_enterprise_simulation_lab/` vs `applications/enterprise_hub/simulation_engine/` +
  `simulation_lab/` vs `applications/platform_builder/simulation/`.
- **Certification** — `platform_certification/`, `platform_enterprise_certification/`, plus
  per-application `enterprise_certification/` subpackages in at least 7 different `applications/*`.
- **"Ecosystem"** — three separate things named ecosystem: root `ecosystem/`,
  `applications/ecosystem/`, and `applications/enterprise_hub/` (branded "Unified AI Ecosystem"/
  "Enterprise Integration Hub" internally re-implementing hub-level concepts).
- **`recommendation_engine`** — appears independently in 6+ locations per
  `docs/TECHNICAL_DEBT_REPORT.md` (TD-05) — not re-traced file-by-file here, see that report.
- **Login pages** — `src/web`'s login flow vs `platform_console/src/pages/LoginPage.tsx` (unrouted,
  §3.2) — duplicate implementations of the same form, per TD-11.
- **`EventBus`-named classes** — at least 6 independent definitions outside the canonical
  `events/event_bus.py::PlatformEventBus`: `platform_events_legacy.py:170`,
  `ecosystem/communication/event_bus/bus.py:14`, `applications/finance_enterprise/integration/
  event_bus.py:22` (`FinancialEventBus`), `applications/enterprise_hub/event_platform/event_bus.py:13`,
  `applications/platform_builder/team_map/engine.py:40` (`VisualEventBus`), plus
  `src/kernel/events/EventBus.ts` existing *alongside* `src/kernel/event_bus/` (an internal duplicate
  within the same TS package).
- **Config** — root `config.py` (legacy facade) vs `platform_configuration/` (real engine, intentional
  layering, not true duplication) vs `applications/platform_builder/config.py` (different concern —
  app metadata) vs `config/mcp.config.json` (different concern — MCP transport). Listed here for
  completeness; not recommended for consolidation since the concerns genuinely differ.
- **Verification-level enums** (Sprint CQ-10 addition) — `database/models/kyc.py`'s `VerificationLevel`
  (`NONE`/`BASIC`/`STANDARD`/`ENHANCED`, four tiers) vs `database/models/compliance.py`'s
  `ComplianceVerificationLevel` (`L0`–`L4`, five tiers), both FK'd to the same
  `partner_engine_partners.id` — two real, independently-defined tier systems for what should be one
  concept. Unlike most entries in this section, this one has a clear, low-cost recommended fix (unify
  before any new consumer, e.g. `docs/ENTERPRISE_BUSINESS_NETWORK.md`'s proposed EBN verification
  ladder, is built against either): see `docs/ENTERPRISE_BUSINESS_NETWORK.md` §3.3 and
  `docs/SPRINT_CQ_10_RESULT.md`.
- **Individual-person identity** (Sprint CQ-12 addition) — three real, independent representations of
  "a person," none reconciled: frontend `src/web/auth/managers/identityManager.ts`'s `IdentityUser`
  (`userId`, demo-seeded), backend `database/models/users.py`'s `User` (`telegram_id` as primary key,
  Telegram-bot-identity-centric — `username`/`full_name`/`role`/`verticals`/`tenant_id`, no HR fields),
  and `database/models/user_role.py`'s `PermissionUserRole` (`user_id`, a third key space, joined to
  `database/models/role.py`'s real `EngineRoleCode` enum — which itself already includes `OWNER`/
  `ADMIN`/`MANAGER`/`ACCOUNTANT`/`LAWYER`/`PARTNER`/`OPERATOR`/`VIEWER`, a genuinely reusable real role
  taxonomy). A fourth, narrower role representation, `platform_workflow/models.py`'s `HumanRole`
  (`MANAGER`/`ADMINISTRATOR`/`OPERATOR`/`OWNER`, workflow-task-assignment-scoped only), was already
  known (CG-7). Also real but currently a **global singleton, not per-user**:
  `src/web/auth/managers/profileCenter.ts`'s `ProfileSettings` — a concrete, low-cost fix (make it
  per-user) flagged alongside the larger ID-reconciliation question. Full detail:
  `docs/DIGITAL_CITIZEN.md`, `docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md`, `docs/SPRINT_CQ_12_RESULT.md`.
- **Marketplace systems** (Sprint CQ-13 addition) — at least four independent real marketplace
  implementations, none consolidated: `docs/MARKETPLACE.md` (Sprint 12.1 — AI agents/plugins/
  connectors/workflows/applications), `docs/EES_MARKETPLACE_API.md` (Sprint 25.0 — industry_solutions/
  ai_skills/templates/integrations/ui_packs/workflow_packs/dashboard_packs), `docs/
  ENTERPRISE_MARKETPLACE_32_9.md` (Sprint 32.9 — explicitly states "No new Marketplace Engine," reuses
  AI Builder Studio/AI Team/Workflow Automation catalogs — the correct instinct, not yet applied to the
  other three), plus the real City `marketplace` district (Sprint 27.8). Also newly reconciled this
  sprint: `docs/DIGITAL_ASSET_TREASURY.md`/`docs/DIGITAL_ASSET_RISK.md` (real, Sprint 18.4, a genuine
  fiat/crypto treasury — confirmed scoped to financial instruments, **not** the general
  building/equipment/brand/license "digital assets" concept a new Enterprise City feature might
  otherwise assume it already covers) and `docs/FREIGHT_EXCHANGE.md`/`docs/AUCTION_PLATFORM.md` (real,
  vertical-scoped tender/bid/auction systems). Full detail: `docs/BUSINESS_MARKETPLACE.md`,
  `docs/DIGITAL_ASSETS.md`, `docs/TENDERS_PROCUREMENT.md`, `docs/SPRINT_CQ_13_RESULT.md`.
- **Command Center systems** (Sprint CQ-15 addition) — the largest naming-collision found in this
  document's whole history: **four** independent real "Command Center" implementations, none
  consolidated — `docs/ENTERPRISE_COMMAND_CENTER.md` (Sprint 26.6 — productivity platform, search/
  actions/AI/analytics, `platform_enterprise_command_center`), `docs/COMMAND_CENTER.md` (Sprint 27.5 —
  `CommandCenterProvider`/`UniversalCommandPalette`, confirmed the actually-mounted/live one per this
  document's own §3.1/§7 research), `docs/COMMAND_CENTER_OS.md` (Sprint 29.13 — Platform Builder,
  explicitly "no business logic, only orchestrates"), and `docs/ENTERPRISE_COMMAND_CENTER_32_3_2.md`
  (Sprint 32.3.2 — the real `/dashboard` first-entry landing answer). Also newly reconciled:
  `docs/EXECUTIVE_DECISION_INTELLIGENCE.md` (real, Sprint 29.18 — decision support, "analytical and
  advisory only," directly relevant to §5's AI runtime discussion above). Full detail:
  `docs/EXECUTIVE_OPERATING_SYSTEM.md`, `docs/EXECUTIVE_DECISION_CENTER.md`,
  `docs/SPRINT_CQ_15_RESULT.md`.
- **Digital Twin — fifth collision entry** (Sprint CQ-16 addition) — the real "Digital Twin /
  Simulation" collision above (`platform_enterprise_digital_twin/` vs legacy EDT vs `applications/
  executive_center/twins.py` vs `applications/platform_builder/digital_twin/`) is confirmed this
  sprint to be **entirely organizational/process-scoped** (`platform_enterprise_digital_twin/models.py:
  39`'s own `"one_twin_per_company"` principle) — none of the four model geography. The real
  geo-relevant "Digital Twin" usage is a structurally separate fifth lineage: `docs/SPATIAL_RUNTIME.md`
  (real, Sprint 29.4, self-branded "Odessa Digital Twin"). Recommendation to prevent a sixth collision:
  use "Digital Twin" only in the narrative/brand sense Sprint 29.4 already established, and
  "Territory"/"Regional Spatial Twin" as the technical term for geospatial work going forward. Also
  newly reconciled: a real three-way permission-scope near-collision (`SpatialPermissionScope` vs
  `AssetPermissionScope` vs business `Visibility`), none identical, none yet unified. Full detail:
  `docs/REGIONAL_DIGITAL_TWIN.md` §3, `docs/DIGITAL_TWIN_STANDARDS.md` §2, `docs/SPRINT_CQ_16_RESULT.md`.
- **Notification vocabularies** (Sprint CQ-17 addition) — three real, independently-authored
  notification systems, none identical: legacy per-vertical `NOTIFICATION_CATEGORIES` (`crypto_otc/
  agro_trading/law/drone/cafe_beauty/calendar/ai_assistant`, `database_legacy.py:5904-5914`) vs. the
  unified `docs/NOTIFICATION_CENTER.md`/`docs/NOTIFICATION_CHANNELS.md` (real, `/api/enterprise-comms/
  v1/center`, `services/notification_center.py`) vs. frontend `NotificationKind`/`NotificationBucket`
  (`src/web/src/notifications/notificationStore.ts:3-38`). None of these three map cleanly onto each
  other, and none carry business-domain categories (e.g. "Business Opportunities," "Partner Requests")
  — recommended fix is a thin composing tag layered over all three, not a fourth taxonomy. Also newly
  confirmed real this sprint: a genuine unified per-organization Business Calendar
  (`database/models/calendar.py`'s `CalendarEvent`, `services/calendar_service.py`) — correcting any
  assumption that no real business calendar exists; the real gap is narrower (cross-*organization*
  calendar sharing only). Full detail: `docs/OPERATIONAL_NOTIFICATIONS.md`, `docs/BUSINESS_CALENDAR.md`,
  `docs/SPRINT_CQ_17_RESULT.md`.
- **Deal/pipeline systems — the largest collision found in this document's history** (Sprint CQ-18
  addition) — at least **six** independent real staged-pipeline implementations, exceeding both the
  four-way Command Center collision (CQ-15) and the four-way Digital Twin collision (CQ-16):
  `deals.py`'s generic `Deal` (module + per-vertical `Deal*Ext` tables), `deal.py`'s `DealEngineDeal`
  (`DealStatus`, exchange/OTC-flavored), `deal_engine_v1.py`'s `DealEngineV1Deal` (superseded v1),
  `deal_pipeline_engine.py`'s `PipelineDeal`/`DealPipelineStageCode` (**recommended canonical** —
  tenant-configurable `DealStage.allowed_next_stages`, real SLA, real `DealStageHistory` audit trail
  with `validation_passed`), `lead_engine.py`'s `LeadEngineLead` (closest to a textbook
  new/qualified/negotiation/won/lost funnel), and `automotive_sales.py`'s `Lead`/`SalesPipelineStage`
  (automotive-only). No dedicated Opportunity/Proposal/Contract entity exists in any of them. Also
  newly reconciled: real vertical-scoped Support/Maintenance/Renewal precedents
  (`automotive_service.py`'s `ServiceOrder`/`WarrantyRecord`, `docs/CPL_LOYALTY_CALENDAR.md`'s real
  Loyalty/Membership Center) confirm the post-sale value chain is real but not generalized past a
  single vertical each — same shape as the sales-side collision, smaller scale. Full detail:
  `docs/ENTERPRISE_VALUE_CHAIN.md`, `docs/PROJECT_LIFECYCLE.md`, `docs/SPRINT_CQ_18_RESULT.md`.
- **Canonical process model** (Sprint CQ-19 addition) — rather than adding an eighth deal system or a
  ninth workflow engine, this sprint defines one canonical stage/state/event vocabulary
  (`CanonicalStage`/`ProcessState`/`CanonicalProcessEvent`) that every real system above maps onto via
  additive lookup tables — no real column is renamed, no real engine is replaced. Two further
  collisions found in the process of building this mapping: (1) **Tasks** — at least three independent
  real task concepts (`database/models/tasks.py`'s generic `Task`, itself disconnected from `Deal` and
  only weakly linked to a project via a non-FK `project_id` column; `deal_pipeline_engine.py`'s
  `DealTask`; and the frontend `ProjectParticipant.assignments`, plain strings with no task entity at
  all); (2) **History/Versioning** — confirmed via a full read of `database/models/mixins.py` (only
  `UUIDPrimaryKeyMixin`/`TimestampMixin`/`CreatedAtMixin`/`SoftDeleteMixin` exist) that no generic
  history or versioning mixin exists anywhere — every entity that tracks history reinvents its own
  table. Full detail: `docs/CANONICAL_PROCESS_MODEL.md`, `docs/ENTITY_RECONCILIATION.md`,
  `docs/SPRINT_CQ_19_RESULT.md`.
- **Knowledge graph / ontology — four real, sequential, self-aware "unify the vocabulary" systems**
  (Sprint CQ-20 addition) — the most on-the-nose collision this document has catalogued, since
  unifying vocabulary is the exact mission of the sprint that found it: `docs/KNOWLEDGE_GRAPH.md`
  (Sprint 12.0, `/api/ai-ecosystem/v1/knowledge`, "merges application knowledge registries into one
  global graph"), `docs/UNIFIED_KNOWLEDGE_GRAPH.md` + `docs/ENTERPRISE_ONTOLOGY.md` (Sprint 19.2,
  `/api/enterprise-kg/v1`, package `applications/enterprise_hub/knowledge/`), `docs/ENTERPRISE_
  KNOWLEDGE_PLATFORM.md` (Sprint 20.3, `/api/enterprise-ekp/v1`, package `knowledge_platform/` —
  explicitly renamed because `knowledge/` was "reserved" by Sprint 19.2), and `docs/ENTERPRISE_
  KNOWLEDGE_GRAPH.md` (Sprint 24.2, `/api/enterprise-ekg/v1`, package `platform_enterprise_knowledge_
  graph/` — explicitly self-described as "Additive to legacy `/api/enterprise-kg/v1` and
  `/api/enterprise-ekp/v1`"). Each of the last three announced itself as the unifying layer and chose
  addition over consolidation of the one before it — the real precedent this sprint's own canonical
  vocabulary work deliberately follows (a fifth *documentation* layer, never a fifth *system*). Real
  `platform_enterprise_knowledge_graph.ENTITY_TYPES`/`RELATION_TYPES` (Sprint 24.2, 21 and 14 values
  respectively) is recommended as the canonical entity/relation vocabulary going forward — the most
  complete of the four, and already covers 8 of the brief's 19 requested entity kinds verbatim. Full
  detail: `docs/ENTERPRISE_ONTOLOGY.md`, `docs/RELATIONSHIP_MODEL.md`, `docs/SPRINT_CQ_20_RESULT.md`.

## 14. Legacy modules

- **`platform_legacy/`** (21 files) — the sanctioned isolation boundary: `facade.py`, `adapter.py`,
  `compatibility_layer.py`, `migration_manager.py`, `legacy_import_policy.py`,
  `deprecation_manager.py`, `runtime_monitor.py`, `docs_generator.py`, `ci_validation.py`,
  `coverage.py`. Wraps `handlers.py`, `database_legacy.py`, `openrouter.py`, `services/pg_*` per
  `LEGACY_MIGRATION.md`'s 10-subsystem migration matrix (ai, configuration, managers, notifications,
  repositories, requests, scheduler, telegram, users, workflow) — every subsystem's feature flag
  currently defaults to `False` (still legacy), and every "deprecated API removal date" in that matrix
  is listed as "None."
- **`database_legacy.py`** (11,205 lines) — imported by 6+ non-`platform_legacy` locations (§12 item 3).
- **`platform_events_legacy.py`** (345 lines, own `EventBus` class) — imported by
  `platform_architecture/*` and `tests/test_unified_event_bus.py` in addition to `platform_legacy/*`.
- **21 root `*_handlers.py` files** (ai_sales, anti_loss_layer, auto_vertical, automotive_partner,
  automotive_revenue, bidex_quote, cart_engine, crm_pipeline_boards, deal_engine, deal_workflow,
  dealer_onboarding, dealer_quote_authority, lead_engine, owner_dashboard, owner_panel,
  owner_payment_profile, partner_cabinet, payment_engine, revenue_engine, start_routing,
  tenant_guard, vertical_onboarding) plus core `handlers.py` (~5,000+ lines) and `keyboards.py`
  (65KB) — the original monolithic bot, still the fallback router chain in `startup.py::BOT_ROUTER_PATHS`.
- **Legacy-aware code elsewhere**: `platform_workflows/adapters/legacy_rules.py`,
  `events/adapters/legacy_adapter.py`, `tests/test_legacy_isolation.py`,
  `tests/test_legacy_migration.py`, `tests/test_legacy_migration_framework.py`,
  `scripts/validate_legacy_migration.py` — a legacy-boundary test suite exists and runs in CI
  (`.github/workflows/architecture.yml`), which is the main safeguard keeping the isolation boundary
  from silently eroding further.

## 15. Missing integrations

1. **`container.py` DI container** — defined, documented as a scaffold in its own docstring ("does NOT
   replace legacy wiring... not wired into bot startup"), and consumed only by its own scaffold tests
   (`tests/unit/test_container_scaffold.py`, `tests/run_scaffold_tests.py`). No production service or
   handler resolves dependencies through it.
2. **The entire `src/` TS "ADOS OS" ecosystem (kernel/orchestrator/providers/chat_bridge/voice/mcp/
   execution) has no runtime connection to the Python backend or to `src/web`.** Confirmed by:
   `docker-compose.yml` defining only `postgres`+`redis` (no kernel/API/bot services); zero grep hits
   for `src/kernel`, `ados`, ports 3000/3100 in any `.py` file; zero grep hits for the Python API's
   host/port in any TS file. The only real bridge is `platform_console` calling the kernel's
   `RuntimeServer` over HTTP/WS — one frontend, one direction, no package-level import.
3. **MCP gateway (`src/mcp`) is unreachable from outside the TS kernel process** — not started
   independently, not referenced by Python, `src/web`, or `platform_console`; only invoked in-process
   via `RuntimeServer`'s `setRuntimeInvoker`.
4. **Voice pipeline (`src/voice`) has no real audio I/O integration** (PCM/base64 frames only) and no
   consumer outside the TS ecosystem.
5. **Example vertical plugins (`plugins/agro`, `auto`, `construction`, `insurance`, `legal`, `medical`,
   `realty`) are never imported by any application, handler, or router** — `platform_plugins/
   plugin_manager.py`'s dynamic `discover()` mechanism is real and is exercised by
   `tests/test_plugins.py`, but that test writes **synthetic fixture plugins to a temp directory**
   rather than loading the real files under root `plugins/` — the example plugins are protocol-shaped
   scaffolding, not something the platform actually installs today.
6. **No unified deployment path** for the dual runtime (Telegram bot + aiohttp API in one process, per
   `docs/PRODUCTION_READINESS_AUDIT.md`'s "Ops gap" note) — `docker-compose.yml` doesn't define an app
   service at all (only `postgres`/`redis`), and `docker-compose.prod.yml` would need to be checked
   against current `startup.py` behavior before relying on it.
7. **No industry-specific customer-facing web portal** for any of the 7+ verticals with a backend
   (`docs/WEB_READINESS_AUDIT.md`) — `src/web/portals/` is generic (customer/employee/owner), not
   wired to e.g. `applications/auto_marketplace`'s specific customer journeys.
8. **Identity/RBAC token flow is partial** — `/management/*` and vertical APIs are header-only
   (§12 item 10); `src/web`'s Identity Center UI exists but the full authenticated round-trip to a
   live token issuer isn't confirmed end-to-end here.

## 16. High-priority improvements

Ordered by (blast radius if left alone) × (cost to fix now vs. later). These are **candidates to
evaluate**, not directives — several conflict with the repo's own stated "additive-only, don't merge"
policy (`docs/TECHNICAL_DEBT_REPORT.md`), so treat consolidation items as "worth a deliberate decision"
rather than "do this."

1. **Fix the 4 critical CI-failing violations now** — `platform_security/config.py:23-24` and
   `platform_security/secrets.py:30,80` reading `os.environ` directly. This is the one item in this
   whole document that is an outright policy violation with an existing enforced gate
   (`ARCHITECTURE_REPORT.md` grade FAIL) rather than a judgment call — lowest-risk, highest-value fix.
2. **Resolve the `database_legacy.py` re-import from `database/__init__.py` and
   `src/platform/layers/architecture_policy.py`.** These two are *supposed* to be on the modern side of
   the legacy boundary; their dependency on the legacy module undermines the isolation guarantee
   `platform_legacy/` exists to provide.
3. **Decide the fate of `container.py`.** Either invest in wiring it into `startup.py`/`api/server.py`
   for new services (matching the DI principle in `CLAUDE.md`), or remove it as unadopted scaffolding
   — carrying it unresolved invites new code to ignore it by precedent.
4. **Clarify the two migrations directories** (`./migrations` vs `./database/migrations`) before the
   next schema change — a wrong choice here risks a split migration history.
5. **Decide whether the TS "ADOS OS" ecosystem (`src/kernel` + 6 packages) is an active product or a
   parked experiment.** Right now it has real, non-trivial code (kernel, orchestrator, mcp, voice) and
   one real consumer (`platform_console`), but zero connection to the production Python
   bot/platform — that's a large amount of maintained surface area with an unclear relationship to the
   rest of the repo. If it's meant to eventually replace or front the Python `platform_orchestrator`
   chain, that's a major architectural decision that should be written down (per `CLAUDE.md`'s
   "every architectural decision must be documented"); if it's a separate product, it may belong in
   its own repository.
6. **Give `src/web` component/route-render tests.** Zero `.test.tsx` files means a broken render in
   the primary enterprise UI would not be caught by CI today.
7. **Either use or remove `src/web`'s TanStack Query wiring** — an unused data-fetching library adds
   confusion for anyone reading the codebase expecting cached/deduped requests.
8. **Wire or delete `platform_console`'s 10 unrouted pages and its unused `ProtectedRoute`/
   `AdminShell`** — an app with built auth scaffolding but no enforced auth route is a easy-to-miss gap
   if this console is ever exposed beyond trusted operators.
9. **Confirm root `memory.db` is dead** and remove it if so — its mere presence contradicts the
   documented `POSTGRES_ONLY=true` policy and could confuse a future contributor into thinking SQLite
   is a supported path.
10. **Fix the two dead doc links in `src/web/README.md`** (trivial, but a new contributor's first
    "quick start" experience currently hits two 404s).
11. **Address the header-only auth gap** on `/management/*` before any pilot/production exposure
    beyond trusted internal operators, per the existing `docs/PRODUCTION_READINESS_AUDIT.md` finding.
12. **Revisit the `applications/platform_builder` four-way command_center/control_center/
    mission_control/operations_center split** specifically (as opposed to the broader "additive
    enterprise layer" pattern) — these four are structurally identical (same file shape, same pattern)
    within a *single* application, which reads less like deliberate additive versioning and more like
    incremental copy-paste within one codebase; worth a targeted look even under an otherwise
    additive-only policy.

---

## Sources consulted

Primary reads: `README.md`, `ARCHITECTURE_REPORT.md`, `LEGACY_MIGRATION.md`, `CLAUDE.md`,
`docs/ARCHITECTURE_AUDIT_INDEX.md`, `docs/ARCHITECTURE_INVENTORY.md`, `docs/TECHNICAL_DEBT_REPORT.md`,
`docs/API_CORE_AUDIT.md`, `docs/PRODUCTION_READINESS_AUDIT.md`, `docs/WEB_READINESS_AUDIT.md`,
`container.py`, `startup.py`, `main.py`, `bot.py`, `api/server.py`, `config.py`, all `platform_*/
__init__.py` files, `src/kernel/**`, `src/orchestrator/**`, `src/providers/**`, `src/chat_bridge/**`,
`src/voice/**`, `src/mcp/**`, `src/execution/**` package.json/README/source files, `src/web/**` and
`platform_console/**` source trees, plus targeted repo-wide greps for `EventBus`, `get_container`,
`AppContainer`, `@ados/*`, `database_legacy`, `legacy`/`deprecated`, and TODO/FIXME markers. No source
file was modified in the production of this document.
