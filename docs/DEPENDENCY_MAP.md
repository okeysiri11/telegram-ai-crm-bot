# Dependency Map — ADOS / BIDEX Enterprise Platform

**Status:** permanent, living document — maintained alongside `ARCHITECTURE_MAP.md`, `MODULES.md`,
`API_MAP.md`, `TECH_DEBT.md`. **Update after every sprint** that adds a cross-package import, a new
`platform_*`/`applications/*` package, or a new external service call.

**Sources:** this document is built from the repo's own generated baseline
(`docs/architecture_baseline/{DEPENDENCY_GRAPH,MODULE_GRAPH,SERVICE_GRAPH,IMPORT_GRAPH}.md`, generated
2026-07-19 via `scripts/generate_architecture_baseline.py`) plus the CI governance output
(`ARCHITECTURE_REPORT.md`, generated 2026-07-20 via `scripts/validate_architecture.py`), cross-checked
against direct package reads for the parts those tools don't cover (the TS kernel ecosystem, the two
frontends). **Re-run `scripts/generate_architecture_baseline.py` and `scripts/validate_architecture.py`
each sprint and refresh the numbers below from their output** rather than hand-editing counts.

---

## 1. How to regenerate this map

```bash
python scripts/generate_architecture_baseline.py   # refreshes docs/architecture_baseline/*.md
python scripts/validate_architecture.py             # refreshes ARCHITECTURE_REPORT.md, scores the graph
```

The Python-side numbers in this document (node/edge counts, violation list) are only as fresh as the
last run of these two scripts — check the "Generated" timestamp at the top of
`docs/architecture_baseline/DEPENDENCY_GRAPH.md` before trusting an exact count. The TS kernel ecosystem
and the two frontends have **no automated dependency-graph generator** — their sections below were
built by direct `package.json`/import reads and must be updated by hand when those packages change.

---

## 2. System-level map (the four graphs that matter)

There are four dependency graphs in this repo, and **they do not connect to each other** except at one
confirmed point (§6):

```
┌─────────────────────────────┐      ┌──────────────────────────────┐
│  Python backend graph        │      │  TS "ADOS OS" kernel graph     │
│  (platform_*, services,      │      │  (@ados/providers, orchestrator,│
│   repositories, database,    │      │   chat-bridge, voice, mcp,      │
│   events, applications/*)    │      │   execution, kernel)            │
│  804 nodes / 2620 edges       │      │  7 packages, kernel depends on  │
│  0 strict cycles              │      │  all 6 others                  │
└──────────────┬───────────────┘      └───────────────┬────────────────┘
               │                                        │
               │ Vite proxy → :8080                     │ HTTP/WS → :3000
               ▼                                        ▼
      ┌─────────────────┐                      ┌────────────────────┐
      │   src/web (SPA)  │                      │  platform_console   │
      │  Enterprise Web   │                      │  Enterprise Control │
      │  Platform         │                      │  Center             │
      └─────────────────┘                      └────────────────────┘
```

The only edge crossing the left/right split is `repositories/base_repository.py` re-exporting from
`src/platform/layers/base_repository.py` (a *Python* file living under the `src/` directory, unrelated
to the TS packages that also live under `src/`) — see §6.1. There is no HTTP, message-queue, or
shared-config link between the Python backend and the TS kernel ecosystem.

---

## 3. Internal packages (Python backend dependency graph)

Per the last baseline run: **804 nodes, 2620 edges, 0 strict cycles** (`docs/architecture_baseline/DEPENDENCY_GRAPH.md`).
Nodes are grouped into layers by `platform_architecture`'s own classifier
(`docs/architecture_baseline/MODULE_GRAPH.md`):

| Layer | Modules | Contents |
|---|---|---|
| `api` | 9 | Route-registration modules: `platform_identity/identity_router.py`, `platform_integrations/{integration,webhook}_router.py`, `platform_jobs/jobs_router.py`, `platform_management/management_router.py`, `platform_observability/telemetry_router.py`, `platform_plugins/plugins_router.py`, `platform_realtime/websocket_router.py`, `services/ai_router.py` |
| `database` | 127 | `database/` package + all `database/models/*.py` |
| `legacy` | 102 | `platform_events_legacy.py` + all `services/pg_*.py` engine modules |
| `plugins` | 9 | `plugins/_scaffold.py` + 7 example vertical plugins + `plugins/realty` |
| `repositories` | 109 | `repositories/*.py` |
| `services` | 257 | `events/*`, `platform_ai/*` (largest single subtree here), `platform_certification/*`, `platform_configuration/*`, and more |
| `shared` | 52 | Package `__init__.py` files and cross-cutting shared modules (`platform_api/*`, `platform_management/{auth,exceptions,health,...}.py`, `src/platform/*` shims) |
| `workflow` | 12 | `platform_workflows/*.py` |
| `unknown` | 127 | Root `services/*.py` files not matching a naming convention the classifier recognizes (mostly domain services and `*_test.py` files co-located in `services/`) |

### 3.1 Representative real edges (not exhaustive — see `docs/architecture_baseline/DEPENDENCY_GRAPH.md` for the full 2620)

**`platform_management` is the most-depended-on hub** — `management_router.py` alone imports from
9 other `platform_*` packages to assemble the `/management/v1` surface:

```
platform_management.management_router
  → platform_management.{permissions, management_service, exceptions, response_models, management_context}
  → platform_api.{versioning, contracts, pagination}
  → platform_observability.telemetry_router
  → platform_ai.{ai_router, workflows_router, skills_router, memory_router}
  → platform_integrations.integration_router
  → platform_realtime.{websocket_router, realtime_hub}
  → platform_jobs.jobs_router
  → platform_identity.identity_router
  → platform_operations.operations_service
  → platform_plugins.plugins_router
```

```
platform_management.management_service
  → services.{smart_assignment_service, sla_dashboard_service, manager_pool_service}
  → platform_legacy.{migration_report, deprecation_manager, health, feature_flags, deprecation, "(package)"}
  → platform_ai.ai_service
  → platform_configuration.{config_provider, configuration_center, config_service, config_schema}
  → platform_plugins.plugin_manager
  → platform_sdk.{base_vertical, vertical_registry, workflow_loader, bootstrap}
```

```
platform_workflows.workflow_engine
  → events.{workflow_events, publisher}
  → platform_workflows.{workflow_loader, models, context, workflow_registry, workflow_executor,
      workflow_validator, exceptions, adapters.python_definitions}
  → repositories.workflow_execution_repository
  → database.session
  → platform_ai.skills.skill_manager
```

```
platform_operations.dashboard_service
  → platform_operations.{summary_service, jobs_widgets, exceptions, models, widgets,
      status_service, observability_widgets, activity_service, metrics_service}
platform_operations.jobs_widgets → platform_jobs.job_engine
platform_operations.observability_widgets → platform_observability.dashboard_metrics
```

```
platform_plugin_sdk.plugin_api
  → platform_ai.{workflows.models, memory.models, skills.models, workflows.workflow_engine,
      memory.memory_service, skills.skill_manager}
  → events.{event_bus, publisher}
  → platform_configuration.config_provider
  → platform_sdk.{vertical_builder, workflow_loader}
  → platform_integrations.integration_service
  → platform_observability.metrics_service
  → platform_jobs.job_engine
  → platform_identity.identity_service
```

```
database.engine → platform_configuration.configuration_center
database → services.{user_service, audit_service, request_service, role_service}, database.async_bridge
database.session → database.{engine, base}
```

### 3.2 The AI-stack internal graph (`platform_ai`, 487 service modules total per `SERVICE_GRAPH.md`)

`platform_ai` is internally the densest single package — it contains its **own** memory stack
(`platform_ai/memory/*`, 13 modules: `memory_manager`, `memory_store`, `memory_retriever`,
`memory_ranker`, `memory_registry`, `memory_service`, `knowledge_base`, `knowledge_index`,
`knowledge_loader`, `knowledge_search`, `chunking`, `document_store`, `memory_context`,
`memory_embeddings`) and its own skills/workflow subsystems (`platform_ai/skills/*`,
`platform_ai/workflows/*`), which is architecturally separate from `platform_memory/` and
`platform_workflows/` at the top level (see §7 — this is the confirmed "two memory stacks" and
"multiple workflow engines" duplication also flagged in `TECH_DEBT.md`).

Concretely: `platform_ai.workflows.workflow_engine` **wraps** `platform_workflows.workflow_engine` and
`platform_workflows.workflow_executor` (a real dependency, not just a naming coincidence — `platform_ai`
depends on `platform_workflows`, not the reverse). But `platform_ai.memory.memory_service` has **no
dependency on `platform_memory`** — the two memory stacks do not share code at all.

---

## 4. Providers

Two disconnected "provider" concepts:

- **`platform_integrations/`** (Python) — `integration_service.py`, `integration_router.py`,
  `webhook_router.py`, `webhook_manager.py`. This is the real external-system integration point used
  by the Python backend; `webhook_manager.py` imports `platform_legacy` (flagged as a
  `reverse_layer_dependency` warning in `ARCHITECTURE_REPORT.md`, §7).
- **`src/providers/` (`@ados/providers`)** (TS) — `ProviderGateway.ts`, `ProviderRegistry.ts`,
  `BaseProvider.ts`, `adapters/builtin.ts` + `adapters/CursorProvider.ts` (mock Cursor/OpenAI/Claude/
  GitHub/Local-LLM adapters — "no real API keys"). Depended on by `@ados/chat-bridge` and
  `@ados/voice`; has no dependents outside the TS kernel ecosystem and no dependency of its own.

No dependency edge connects these two — a Python service cannot reach `@ados/providers` and vice versa.

---

## 5. AI runtime

Three independent agent/orchestration graphs, confirmed to not import each other:

```
Python:  platform_memory → platform_orchestrator (+ platform_agents, near-duplicate exports)
           → platform_workflow / platform_tools
           → platform_reasoning / platform_planning / platform_decision
           → platform_learning / platform_collaboration

TS:      @ados/providers → @ados/orchestrator (AiOrchestrator, AgentRegistry, CollaborationEngine)
           → @ados/chat-bridge → @ados/voice
           → @ados/execution
         (all six) → @ados/kernel (RuntimeServer exposes them as REST/WS)

App:     applications/platform_builder/ai_team/ (team_center.py)
         applications/platform_builder/ai_builder/ (catalogs.py, registry.py, wizard.py)
         — zero references to platform_orchestrator from this application
```

`platform_ai.ai_router` / `skills_router` / `memory_router` / `workflows_router` (the actual
`/management/v1/ai/*`-family endpoints — see `API_MAP.md`) all depend on `platform_management.*`
(management_context, permissions, response_models) and `platform_api.versioning` — these are the
*governed* API-facing edges, distinct from the internal `platform_ai.*` service graph in §3.2.

---

## 6. Frontend

### 6.1 `src/web` → Python backend

```
src/web (Vite proxy) → http://localhost:8080  (api/server.py: /api, /management)
```
No package-level dependency — this is a network dependency only, configured in `src/web/vite.config.ts`
and `src/web/src/config/webConfig.ts` (~30 named API-prefix constants). `src/web` shares **zero** code
with `platform_console` (no workspace link, no common package).

### 6.2 `platform_console` → two backends

```
platform_console → /management/*                      (Python, api/server.py mount)
platform_console → http://localhost:3000 (+ /ws)        (TS kernel's RuntimeServer)
```
`platform_console`'s `package.json` has **zero `@ados/*` dependencies** — its link to the TS kernel is
a pure network dependency (HTTP/WS), same as its link to the Python backend. It is the only frontend
with a live dependency on the TS ecosystem.

### 6.3 The one real Python ↔ `src/` cross-tree edge

```
repositories/base_repository.py  →  src/platform/layers/base_repository.py   (Python, NOT the TS tree)
```
Plus 8 more `repositories/*.py` files depending on the same module transitively
(`assignment_score_repository.py`, `request_repository.py`, `manager_pool_repository.py`,
`owner_repository.py`, `workflow_execution_repository.py`, `platform_metrics_repository.py`,
`manager_repository.py`, `kpi_repository.py` — per `docs/architecture_baseline/IMPORT_GRAPH.md`). This
is the *only* dependency of the root `repositories/` package on anything under `src/`, and it is flagged
by `scripts/validate_architecture.py` as a non-critical `reverse_layer_dependency` warning (§7).

---

## 7. Dependency directions (governed vs. observed)

**Intended direction** (per `.cursor/rules/ados-architecture.mdc` and `platform_architecture/`):

```
Platform core → Providers → AI services → Business modules → Vertical solutions → Customer applications
```

**Observed violations** at the last CI run (`ARCHITECTURE_REPORT.md`, Grade **FAIL**, score 95.45/100):

### 7.1 Critical (blocks CI — 4 total, all `env_access_outside_center`)

| File | Lines | Violation |
|---|---|---|
| `platform_security/config.py` | 23, 24 | Direct `os.environ` access, bypassing `ConfigurationCenter` |
| `platform_security/secrets.py` | 30, 80 | Direct `os.environ` access, bypassing `ConfigurationCenter` |

### 7.2 Non-critical (`reverse_layer_dependency` — 29 total, full list from `docs/architecture_baseline/IMPORT_GRAPH.md`)

A lower/shared-layer module importing from a nominally-higher layer:

- `database/engine.py` → `platform_configuration.configuration_center`
- `platform_operations/timeline_service.py` → `platform_management.management_service`
- `platform_operations/status_service.py` → `platform_management.{system_info, health}`
- `platform_operations/activity_service.py` → `platform_management.{statistics, management_service}`
- `platform_integrations/webhook_manager.py` → `platform_legacy`
- `platform_identity/{policy_engine, permission_service, role_service, audit_hooks}.py` → `platform_legacy`
- `platform_identity/identity_service.py` → `platform_management.{permissions, exceptions}`
- `platform_sdk/bootstrap.py` → `platform_sdk.verticals`
- `platform_sdk/{notification_provider, validation_provider}.py` → `platform_legacy`
- `platform_ai/{workflows_router, ai_router, skills_router, memory_router}.py` → `platform_management.{response_models, permissions, management_context}`, `platform_api.versioning`
- `platform_ai/context_builder.py` → `platform_management.statistics`
- `platform_configuration/config_service.py` → `platform_legacy`
- `platform_observability/metrics_service.py` → `platform_management.management_service`
- `platform_legacy/adapter.py` → `database`
- `src/verticals/{realty,auto,legal,logistics,agro}/service.py` → `src.verticals`, `platform_legacy`
- `events/adapters/legacy_adapter.py` → `platform_legacy`
- `events/handlers/sla_handler.py` → `platform_legacy`
- `platform_sdk/verticals/auto_vertical.py` → `platform_legacy`
- `platform_workflows/adapters/legacy_rules.py` → `platform_legacy`
- **9× `repositories/*.py`** → `src.platform.layers.base_repository` (§6.3)
- `repositories/owner_repository.py`, `repositories/sla_repository.py` → `platform_configuration.config_provider`
- `repositories/{partner,calendar,finance,task}_repository.py` → `database` (shared-layer import, flagged but expected for a data-access layer)
- `repositories/event_repository.py` → `events`
- `repositories/event_bus_repository.py` → `platform_configuration.event_bus_policy`

None of these 29 are currently blocking CI (only the 4 critical ones are), but they represent the gap
between the documented layering and the actual import graph — see `TECH_DEBT.md` for remediation
priority.

---

## 8. Cyclic dependencies

**Confirmed: 0 strict cycles** in the governed Python dependency graph, per
`docs/architecture_baseline/DEPENDENCY_GRAPH.md` ("Strict cycles: 0 — None in governed layers") and
`ARCHITECTURE_REPORT.md` ("Cycles: 0" across 956 modules / 3084 edges in that report's own count —
the two tools' node/edge counts differ slightly by run date, but both agree on zero cycles).

No cycle-detection tooling exists for the TS kernel ecosystem or either frontend. Manually inspecting
the six `@ados/*` package dependency declarations (§5) shows a clean DAG (`providers`/`orchestrator` at
the base, `kernel` at the top depending on all others) with no back-edge. One internal near-duplicate
worth flagging (not a cycle, but adjacent risk): `src/kernel/event_bus/` (the full pub/sub bus) and
`src/kernel/events/EventBus.ts` (a second, simpler bus) coexist in the same package — if both are ever
wired into the same code path, verify neither ends up depending on the other in a loop.

**If a cycle is introduced in a future sprint**, it will show up as a non-zero "Strict cycles" count in
`docs/architecture_baseline/DEPENDENCY_GRAPH.md` the next time `generate_architecture_baseline.py` runs
— treat any non-zero value there as a regression to fix before merging, not something to document
around.

---

## 9. Communication summary (all confirmed live links between subsystems)

| From | To | Mechanism | Confirmed by |
|---|---|---|---|
| Telegram bot (`main.py`/`bootstrap.py`) | `routers/*`, `handlers.py` | aiogram dispatcher registration | `startup.py::BOT_ROUTER_PATHS` |
| `startup.py` | `api/server.py` | in-process call (`start_api_server`) | `startup.py` |
| `api/server.py` | 15× `applications/*/api/register.py` | in-process route mounting | `api/server.py` body |
| `services/*` | `events.event_bus` (`PlatformEventBus`) | in-process pub/sub | `events/event_bus.py`, `events/crm_publisher.py` |
| `src/web` | `api/server.py` (`/api`, `/management`) | HTTP, via Vite dev proxy to `:8080` | `src/web/vite.config.ts` |
| `platform_console` | `api/server.py` (`/management/*`) | HTTP (`services/management.ts`) | `platform_console/src/services/management.ts` |
| `platform_console` | TS kernel `RuntimeServer` | HTTP + WS, `:3000` / `:3000/ws` | `platform_console/src/services/runtimeApi.ts` |
| `@ados/mcp` | `src/kernel` `RuntimeServer` | in-process callback (`setRuntimeInvoker`) | `src/kernel/runtime/RuntimeServer.ts` |
| `@ados/chat-bridge`/`@ados/voice` | `@ados/orchestrator`, `@ados/providers` | direct TS import | package.json `file:` deps |
| Python backend | TS kernel ecosystem | **none found** | repo-wide grep, §2 |
| `repositories/*` | `src/platform/layers/base_repository.py` | direct Python import | `docs/architecture_baseline/IMPORT_GRAPH.md` |

---

## Related documents

- `ARCHITECTURE_MAP.md` — full narrative architecture map (structure, per-subsystem detail).
- `MODULES.md` — per-module catalog (purpose/owner/API/dependencies/status/debt/plans).
- `API_MAP.md` — concrete endpoint-level API inventory (REST/WS/MCP/events).
- `TECH_DEBT.md` — living registry; §7 of this document feeds its "architecture violations" entries.
