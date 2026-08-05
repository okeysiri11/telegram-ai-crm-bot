# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
It is the permanent engineering manual for the ADOS Enterprise Platform. It does not expire at the
end of a sprint — treat it as binding for every session, every module, every language in this repo.

## What this is

BIDEX / ADOS Enterprise Platform — originally a Telegram-bot automotive CRM, now grown into a large
"Enterprise AI Operating System" (ADOS) with dozens of `platform_*` capability layers, multiple
vertical marketplace applications, and several independent frontend apps. The Telegram bot (`main.py`,
`bootstrap.py`, `handlers.py`, `routers/`) is still a live channel, but most new work happens in the
`platform_*` layers and the web consoles.

This repo is in continuous "sprint" development — commit messages and `docs/` filenames are numbered
by sprint (e.g. `Sprint 34.0`, `SPRINT_1_1_1_RESULT.md`). Check the latest `docs/` files and recent
git log for the current sprint/version before assuming a doc is current — many docs describe a past
milestone, not the present state.

## Engineering philosophy (non-negotiable)

Everything else in this file is an elaboration of these principles. When a specific instruction is
ambiguous, resolve it in the direction of these principles, not the shortest path to green tests.

- **Enterprise-first architecture.** Every decision is made for a multi-tenant, multi-vertical
  enterprise platform, not for a single bot or a single customer. Local convenience never overrides
  platform consistency.
- **AI-first development.** The platform's core value is its AI agent stack (memory → orchestration
  → agent registry → workflow/tool execution → reasoning/planning/decision → learning/collaboration —
  see `platform_memory/` … `platform_collaboration/` below). New capability should be designed to be
  usable by agents and workflows, not only by direct human-facing UI.
- **Never break existing APIs.** `/api/v1` and `/management/v1` contracts are frozen. Additive changes
  only (new fields, new endpoints, new versions). If a breaking change is unavoidable, it needs an
  explicit version bump and a migration path — never a silent behavior change on an existing route.
- **Prefer extension over replacement.** Extend an existing `platform_*` package, service, or
  component before creating a new one. Replacing or redesigning a completed module requires an
  explicit request — it is never an incidental side effect of an unrelated task.
- **Preserve clean architecture.** Respect the layering (Platform core → Providers → AI services →
  Business modules → Vertical solutions → Customer applications). Don't let a lower layer import
  upward, and don't let vertical/customer code leak into shared platform packages.
- **Avoid duplicate code. Reuse services before creating new ones.** Before writing a new
  function/service/component, search for an existing one in `services/`, `repositories/`,
  `platform_*`, or the frontend `design-system/`. Two similar implementations of the same concept is
  a defect, not a style choice.
- **Use feature modules.** New functionality is added as a cohesive module (its own directory, own
  tests, own docs) inside the appropriate layer — not scattered across unrelated files, and not as a
  new top-level `platform_*` package unless it is genuinely a new capability layer.
- **Use dependency injection where possible.** Prefer `container.py` (`AppContainer`/`ServiceRegistry`)
  for new code's dependencies over hardcoded imports/singletons, even though legacy code still wires
  dependencies directly (see the DI note below). New modules should be constructed so they *could* be
  resolved through the container even if the surrounding code isn't yet.
- **Every new module must be scalable and multi-tenant-ready.** Assume concurrent tenants, concurrent
  verticals, and horizontal scaling from day one: no in-process global mutable state keyed only by a
  single tenant, no assumptions that there is exactly one customer, one bot instance, or one region.
  Tenant scoping goes through `middleware/tenant_middleware.py`, not ad hoc per-handler checks.
- **Never modify unrelated modules.** A change scoped to one capability touches that capability's
  package (and its direct integration points: events, docs, tests). It does not opportunistically
  refactor, rename, or "clean up" other modules in the same commit.
- **Every architectural decision must be documented**, at the point it's made — not reconstructed
  later from code. See "Documenting decisions" below.

## Repository layout (three languages, four run targets)

1. **Python bot + platform backend** (repo root): aiogram Telegram bot + aiohttp API server +
   ~60 `platform_*` packages implementing enterprise capabilities (see Architecture below).
2. **`src/` ADOS Node/TS kernel ecosystem**: a separate, independent Node monorepo
   (`src/kernel`, `src/orchestrator`, `src/providers`, `src/chat_bridge`, `src/voice`, `src/mcp`,
   `src/execution`) — an AI agent runtime unrelated to the Python platform, built/tested via the
   root `package.json`. `src/domains`, `src/platform`, `src/verticals`, `src/events` are a *separate*
   Python package tree also living under `src/` (older/parallel domain model) — don't confuse
   `src/<pkg>` (TS, has its own `package.json`) with `src/domains|platform|verticals|events` (Python).
3. **`src/web`**: the main React "Enterprise Web Platform" frontend (owner/operator consoles, AI OS,
   command center, platform builder verticals). Home of the **Enterprise Dashboard**.
4. **`platform_console`**: a second, separate React admin console app (its own Vite/Vitest/oxlint setup).

Treat each of these as independent projects with their own dependency installs and test runners —
changes in one do not require touching the others unless a feature explicitly spans them.

## Primary entry point and product sequencing

- **Enterprise Dashboard is the primary entry point of the platform** (`docs/ados_os/enterprise_dashboard.md`,
  `src/web`). It is the production-facing home for Dashboard, Workflows, AI Agents, Providers, Memory,
  Timeline, Tasks, Queue, Metrics, Logs, and Events. Any work on "what a user sees first" defaults to
  the Dashboard unless told otherwise.
- **Enterprise City is sequenced after platform completion.** Enterprise City
  (`docs/EP_05_ENTERPRISE_CITY.md`) is a presentation layer on top of existing platform data (no new
  Engine/Store/Runtime/AI Core/Data Fabric of its own). Further investment in Enterprise City work is
  only in scope once all platform modules are completed — do not pull effort from platform_* module
  completion into City visual work, and do not use City requirements to justify new engine-level
  functionality (that functionality belongs in the platform layer, with City consuming it).

## Common commands

### Python bot / platform backend (repo root)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python startup.py                      # or: python main.py — starts bot polling + API server

# Tests (pytest-asyncio, auto mode; testpaths = tests/)
.venv/bin/python -m pytest tests/ -q -m "not slow"
.venv/bin/python -m pytest tests/test_some_file.py::test_name   # single test
.venv/bin/python -m pytest tests/ -q --tb=no -m "not slow"       # CI form

# Security-specific suite (also run in CI as its own job)
python -m pytest tests/test_management_security.py tests/test_api_v1_freeze.py tests/test_admin_security.py -q --tb=no

# Architecture governance (all run in CI; keep the repo passing these)
python scripts/validate_architecture.py
python scripts/validate_legacy_migration.py
python scripts/generate_architecture_baseline.py
python scripts/run_platform_certification.py
python scripts/check_no_sqlite.py        # POSTGRES_ONLY=true — no sqlite usage allowed
```

CI (`.github/workflows/architecture.yml`) runs three jobs: `pytest` (regression tests, `not slow`),
`architecture` (validate_architecture / validate_legacy_migration / generate_architecture_baseline),
and `security` (the three security test files above). `POSTGRES_ONLY=true` is set in CI — Postgres is
the only supported production DB; `database_legacy.py` and any sqlite path are legacy/disallowed
(enforced by `scripts/check_no_sqlite.py`).

### `src/` ADOS Node kernel ecosystem (root `package.json`, orchestrates all `src/<pkg>` subprojects)

```bash
npm run postinstall     # installs providers, orchestrator, chat_bridge, voice, mcp, execution, kernel, platform_console
npm run build           # builds subprojects in dependency order, then kernel
npm test                # runs vitest in each subproject in turn
npm run ados            # build + run the kernel (node dist/main.js)
```

Each subproject (`src/kernel`, `src/orchestrator`, etc.) is independently buildable/testable:
`npm run build --prefix src/orchestrator`, `npm run test --prefix src/orchestrator` (vitest), etc.
Build order matters — dependents (`kernel`, `chat_bridge`, `voice`, `execution`) require their
`@ados/*` deps built first (see each package's `prebuild`/`dependencies`).

### `src/web` (Enterprise Web Platform)

```bash
cd src/web && npm install
npm run dev      # http://localhost:5180 — login owner@demo.corp / demo (VITE_DEMO_AUTH when ISAM :8080 is down)
npm run build    # tsc -b && vite build
npm run test     # vitest run
npm run lint     # tsc -b --pretty false (typecheck-as-lint, no separate linter)
```

### `platform_console` (second admin console)

```bash
cd platform_console && npm install
npm run dev / build / preview
npm run test     # vitest run
npm run lint     # oxlint
```

## Architecture (Python backend)

### Bot entrypoint & lifecycle

`main.py` → `bootstrap.py` (builds aiogram `Dispatcher`, FSM storage) → `startup.py::run_startup()`
(loads `ConfigurationCenter`, validates IAM JWT secret, starts the aiohttp API server, registers
platform event handlers, starts the CRM event-bus worker and scheduler) → `dp.start_polling(bot)`.
`bot.py` is a backward-compatible re-export shim, not a second entrypoint.
Bot routers are registered via `platform_legacy.legacy.telegram.register_bot_routers(dp)` — the
canonical list of router modules lives in `startup.py::BOT_ROUTER_PATHS` (order matters: first
match wins).

### `platform_legacy/` — the legacy compatibility bridge

Root-level `*_handlers.py` files, `database_legacy.py`, and `platform_events_legacy.py` are the
original monolithic bot code. `platform_legacy/` wraps this legacy surface behind a facade/adapter
layer (`facade.py`, `adapter.py`, `compatibility_layer.py`, `migration_manager.py`,
`legacy_import_policy.py`) so newer `platform_*` code never imports legacy modules directly.
`scripts/validate_legacy_migration.py` enforces this boundary in CI — don't add new direct imports
of legacy modules from `platform_*` packages. This is "prefer extension over replacement" applied
literally: the legacy surface is wrapped and gradually migrated, never bulk-rewritten.

### `platform_*` capability layers (the core of ongoing work)

The backend is organized as ~60 independently-versioned `platform_<capability>/` packages, each
sprint-numbered (see README.md's "Platform overview" table for the full map and sprint history).
Dependency direction is enforced, not advisory: **Platform core → Providers → AI services → Business
modules → Vertical solutions → Customer applications**. Key layers:

- `platform_management/` — authenticated admin REST at `/management/v1` (current admin surface).
- `platform_api/`, `api/` — frozen public contract at `/api/v1` (do not break; legacy unauthenticated
  `/api/v1/admin/*` routes were removed on purpose — use `/management/v1` for admin operations).
- `platform_architecture/` — executable architecture rules + dependency graph + CI validation
  (this is what `scripts/validate_architecture.py` runs; see `ARCHITECTURE_REPORT.md` for the last
  generated report — boundaries/plugins/workflows/api/sdk/dependencies/legacy gates).
- `events/` — `PlatformEventBus`, the canonical in-process event routing (`events/event_bus.py`,
  `events/crm_publisher.py`, `events/handlers/`); services communicate through this, not direct calls.
- `services/` — business logic, no direct HTTP exposure (largest package, ~380+ modules). Check here
  first before writing new business logic.
- `repositories/` — Postgres data access (~100+ modules), one per domain entity.
- `platform_security/`, `platform_observability/`, `platform_reliability/`, `platform_configuration/`,
  `platform_validation/` — cross-cutting enterprise concerns (auth/RBAC/secrets, logging/tracing,
  fault tolerance, config/feature-flags, QA/certification gates).
- `platform_memory/`, `platform_orchestrator/`, `platform_agents/`, `platform_workflow/`,
  `platform_tools/`, `platform_reasoning/`, `platform_planning/`, `platform_decision/`,
  `platform_learning/`, `platform_collaboration/` — the AI agent stack (memory → orchestration →
  agent registry → workflow/tool execution → reasoning/planning/decision → learning/collaboration).
  This is the concrete implementation of "AI-first development" above — new AI-facing capability
  should slot into this chain rather than bypass it.
- `container.py` — a DI scaffold (`AppContainer`/`ServiceRegistry`) that is **not yet wired into
  bot startup**; legacy code still imports services directly. Prefer it for new code but don't
  assume it's used everywhere.
- `applications/` — production verticals built on "Platform Core", e.g. `applications/auto_marketplace`
  (GA marketplace) and `applications/platform_builder` (the no-code builder product, itself a large
  subtree: `ai_builder/`, `ai_team/`, `command_center/`, `concierge/`, `control_center/`,
  `workspace_os/`, etc.).

Architecture is governed, not incidental: `scripts/validate_architecture.py` scores module boundaries,
plugin/workflow/api/sdk contracts, and legacy-import discipline, and fails CI on critical violations.
Read `ARCHITECTURE_REPORT.md` (regenerated by `scripts/generate_architecture_baseline.py`) before
adding cross-package imports, and prefer extending an existing `platform_*` package over creating a
new one for a small feature.

### Multi-tenancy & middleware

`middleware/tenant_middleware.py` and `middleware/entry_point_middleware.py` wrap dispatcher-level
routing; tenant scoping is enforced at this layer, not ad hoc in handlers. Any new capability that
touches tenant-scoped data must go through this layer, not reimplement scoping locally — this is what
makes "every feature supports future multi-tenant enterprise deployment" true in practice rather than
aspirational.

## Frontend architecture

- **`src/web`** is the primary enterprise web app: React 19 + TypeScript + Vite + Tailwind +
  TanStack Query + React Router + Zustand + React Hook Form + Zod + Chart.js + Socket.IO. Shell
  lives at `src/shell/enterprise/`; auth is ISAM when the identity service (`:8080`) is reachable,
  falling back to a Demo Auth Provider (`VITE_DEMO_AUTH`) otherwise — see
  `docs/SPRINT_27_1_1_AUTH_RECOVERY.md`. Feature areas live under `src/web/<area>/` (`auth/`,
  `command-center/`, `design-system/`, `navigation/`, `platform-builder/`, `organization-brain/`,
  `portals/`, `vertical-federation/`, `workspace/`, `release/`, `ai-os/`) — reuse `design-system/`
  rather than adding new component primitives. The Enterprise Dashboard lives here (see "Primary
  entry point" above).
- **`platform_console`** is a separate admin console (React 19, dnd-kit, Chart.js, Zustand,
  Tailwind 4). Not a duplicate of `src/web` — has its own README/architecture docs
  (`platform_console/UI_ARCHITECTURE.md`, `DASHBOARD_GUIDE.md`).

## Sprint workflow — required at the end of every sprint

A sprint is not complete until all four of these pass, in this order:

1. **Build** — the affected project(s) build cleanly (`npm run build` / `pip install` + import sanity
   for Python; see per-project commands above). Don't hand back a sprint that doesn't build.
2. **Lint** — `npm run lint` for the affected frontend project(s) (`tsc -b --pretty false` for
   `src/web`, `oxlint` for `platform_console`); Python changes stay consistent with surrounding style.
3. **Tests** — the relevant test suite is green: `pytest tests/ -q -m "not slow"` for backend
   changes, `vitest run` for the affected frontend project(s), plus the security suite if
   `platform_security`/`platform_management`/API surfaces were touched. Never reduce coverage to make
   this pass — add tests for new functionality instead.
4. **Documentation** — update the relevant `docs/*.md` file(s) for what changed, and update
   `ARCHITECTURE_REPORT.md`/baseline if module boundaries moved.

### Every sprint must generate a `RESULT.md`

Following the existing convention (`docs/SPRINT_1_1_1_RESULT.md`, `docs/SPRINT_27_1_RESULT.md`,
`docs/SPRINT_27_2_RESULT.md`, `docs/SPRINT_27_3_RESULT.md`, …), each sprint produces its own
`docs/SPRINT_<id>_RESULT.md` summarizing: what shipped, what was intentionally deferred, build/lint/
test status, and any architecture/documentation follow-ups. Don't skip this for "small" sprints —
it's the durable record of what actually happened, since many other docs describe intent rather than
outcome.

### Documenting decisions

Every architectural decision (new package vs. extending an existing one, a new cross-module
dependency, a schema/contract change, a DI wiring choice, a tenant-scoping approach) gets written
down at the time it's made, not reconstructed afterward. In the absence of a dedicated ADR directory
in this repo, record the decision and its rationale in that sprint's `RESULT.md` under a clearly
labeled "Architectural decisions" section (what was decided, why, and what alternative was rejected),
and cross-link it from the relevant `docs/*.md` if one exists for that subsystem.

## Working conventions (from `.cursor/rules/`)

These apply repo-wide and are enforced by review, not just tooling:

- Prefer extending an existing module/package over creating a new one; never create isolated
  functionality that doesn't integrate into the platform (event bus, services, DI) somewhere.
- Don't rename or move modules, and don't touch unrelated files, unless explicitly asked.
- New features should communicate through `services/`/`events/`, not direct cross-module reach-ins.
- When adding a feature, update the relevant `docs/` file(s) and architecture output if the change
  affects module boundaries.
- Don't reduce test coverage; add tests for new functionality.
