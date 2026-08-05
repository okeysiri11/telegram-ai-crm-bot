# Technical Debt Registry — ADOS / BIDEX Enterprise Platform

**Status:** permanent, **living** document. This is the single registry for tracked debt across the
whole platform. **Every sprint that introduces, fixes, or re-scopes a debt item must update this file**
(per `CLAUDE.md`'s sprint-closeout rule) and note the change in that sprint's `docs/SPRINT_<id>_RESULT.md`.

**Relationship to existing reports — this file supersedes both and keeps their IDs:**
- `docs/TECHNICAL_DEBT_REPORT.md` (Sprint 30.2) tracked naming/API/web debt as `TD-01`…`TD-16` under an
  explicit "do not remove functionality, prefer documentation/extension" policy. Kept verbatim below.
- The previous `docs/TECH_DEBT.md` (auto-generated 2026-07-19, machine-authored, unattributed IDs)
  tracked 4 items from an architecture-baseline run — folded in below as `TD-36`–`TD-39`, since those
  facts (legacy pg-engine cycles, handler DB-access allowlist, WorkflowEngine naming collision, direct
  `crm_event_bus` imports) were never superseded, just never given a durable ID.

This registry adds the categories neither prior report covered (dead code, full architecture-governance
violation list, performance, missing tests/docs) and continues numbering from `TD-17`. **Do not renumber
`TD-01`–`TD-16`** — other docs may already reference them.

**Severity:** P0 (blocks CI / actively wrong today) · P1 (real risk, no active break) · P2 (worth
doing, not urgent) · P3 (cosmetic/nice-to-have).
**Estimated effort:** S (<1 day) · M (1–3 days) · L (1–2 weeks) · XL (multi-sprint, needs an
architectural decision first — see `CLAUDE.md`'s "every architectural decision must be documented").

---

## 1. Master registry (sorted by priority)

| ID | Category | Debt | Severity | Effort | Evidence |
|---|---|---|---|---|---|
| TD-17 | Architecture violation | ~~`platform_security/config.py:23,24` and `platform_security/secrets.py:30,80` read `os.environ` directly, bypassing `ConfigurationCenter`~~ **RESOLVED — Sprint CQ-30**: both files now read through `configuration_center.settings` (`config.py:20-24`, `secrets.py:77-84`); re-run `scripts/validate_architecture.py` to confirm the CI gate is green before closing fully | ~~P0~~ RESOLVED | S | `docs/ARCHITECTURE_CONSISTENCY.md` Issue 2 (Sprint CQ-30 re-verification) |
| TD-08 | Auth | Header-only auth (`X-Principal`, `X-Platform-Role`) across Platform Builder — **Sprint 30.0:** live JWT/API-key preferred; headers only when `ALLOW_HEADER_AUTH` (off by default in production) | P0 → **Mitigated** | L | Sprint 30.0 · full token-only cutover remaining for all vertical middlewares |
| TD-09 | Missing feature | No industry-vertical customer-facing web app for Automotive/Agriculture/Beauty/Cafe/Crypto/Legal/Drone | P0 | XL | `docs/TECHNICAL_DEBT_REPORT.md`, `docs/WEB_READINESS_AUDIT.md` |
| TD-01 | Duplicate naming | Three "ecosystem" layers: root `ecosystem/`, `applications/ecosystem/`, `applications/platform_builder`'s `business_ecosystem` | P0 | M (docs) | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-02 | Duplicate naming | Mission Control / Executive Center / drone Mission overlap | P0 | M (docs) | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-03 | Duplicate naming | "Command Center" branding collides across web global command-center, PB OS, hub ECC | P0 | M (docs) | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-36 | Architecture violation | 47 legacy `services/pg_*` engine dependency cycles, contained within the compatibility layer | P0 (per prior report) | XL | previous `docs/TECH_DEBT.md` (generated 2026-07-19); deferred with justification — see §2.4 |
| TD-18 | Dead code | `container.py` (`AppContainer`/`ServiceRegistry`) has zero production consumers — only exercised by `tests/unit/test_container_scaffold.py` | P1 | M (decide) / L (wire in) | grep `get_container`/`AppContainer` repo-wide |
| TD-19 | Architecture violation | `database/__init__.py` imports `database_legacy` — the modern DB package depends on the legacy monolith it's supposed to be independent of | P1 | M | direct read of `database/__init__.py` |
| TD-20 | Duplicate code | 6+ independent `EventBus`/`*EventBus` class definitions outside canonical `events/event_bus.py::PlatformEventBus`: `platform_events_legacy.py:170`, `ecosystem/communication/event_bus/bus.py:14`, `applications/finance_enterprise/integration/event_bus.py:22` (`FinancialEventBus`), `applications/enterprise_hub/event_platform/event_bus.py:13`, `applications/platform_builder/team_map/engine.py:40` (`VisualEventBus`), `src/kernel/events/EventBus.ts` (coexists with `src/kernel/event_bus/`) | P1 | L | repo-wide grep for `class.*EventBus` |
| TD-21 | Duplicate code | Two independent Python "memory" stacks: `platform_memory/` and `platform_ai/memory/` (both define their own `memory_service.py`), plus `ecosystem/assistant/global_memory/`, `applications/ai_os/memory.py`, `applications/ecosystem/memory.py` | P1 | L | direct package reads, `DEPENDENCY_MAP.md` §3.2 |
| TD-22 | Duplicate code | 4+ independent Python "workflow engine" implementations: `platform_workflow/`, `platform_workflows/`, `platform_workflow_intelligence/`, plus TS `src/kernel/workflow/` | P1 | L (docs) / XL (consolidate) | `docs/TECHNICAL_DEBT_REPORT.md` (subsystem note), `DEPENDENCY_MAP.md` §3.1 |
| TD-37 | Architecture violation | `WorkflowEngine` name collision resolved today only via a legacy-adapter alias, not a real namespace split | P1 (per prior report) | M | previous `docs/TECH_DEBT.md`; overlaps TD-22 — treat together |
| TD-38 | Architecture violation | Handler DB direct access — 4 allowlisted files bypass the repository layer | P1 (per prior report) | M | previous `docs/TECH_DEBT.md` — allowlist not re-enumerated in this pass; re-verify which 4 files against current `platform_architecture/rules.py` |
| TD-39 | Duplicate code / architecture violation | Legacy `pg_*` engines import `services.crm_event_bus` directly instead of going through `events.event_bus.PlatformEventBus` | P1 (per prior report) | M | previous `docs/TECH_DEBT.md`; related to TD-20 |
| TD-40 | Duplicate code | Two separate Command Palette implementations in `src/web` — `command-center/components/UniversalCommandPalette.tsx` is live (mounted via `CommandCenterProvider`); `navigation/components/CommandPalette.tsx` is real, compiled, exported code that is **never imported/rendered anywhere** — a second command catalog (`navigation/managers/commandPalette.ts`) that silently never runs | P1 | M (retire the orphaned copy, or merge its catalog entries into the live one) | `ENTERPRISE_NAVIGATION.md` §0, §5, §22 |
| TD-41 | Duplicate code / missing feature | Favorites and recent-history are implemented **twice** (`navigation/managers/favoritesManager.ts`+`navigationHistory.ts` vs. `workspace/managers/favoritesManager.ts`+`recentActivity.ts`, distinct instances, no shared state) and **neither persists** — both are plain in-memory module-level arrays that reset on page reload; separately, `workspace/managers/layoutManager.ts` stores dashboard/widget layout in an in-memory `Map` despite its own `features()` method listing `"drag_drop"`/`"docking"`/`"responsive_grid"` as capability strings that aren't actually implemented | P1 | M (unify favorites/history) / L (real persistence layer for layout, favorites, history) | `ENTERPRISE_NAVIGATION.md` §0, §22; `WORKSPACE_INTERACTIONS.md` §0, §19 — **partial progress (Sprint 27.8):** `cityNavigation.ts` now persists City building favorites to `localStorage` (`ews_city_favorites_v1`) and bridges into the shared navigation `favoritesManager` — verify whether `favoritesManager` itself gained persistence or only City's own layer did before marking this resolved |
| TD-42 | Missing feature | No general-purpose drag-and-drop, multi-selection, context-menu, or undo/redo primitive exists anywhere in `src/web` — the only real precedents are single-purpose and confined to `WorkspaceTabBar.tsx` (drag-reorder, right-click menu, one-level "reopen last closed"); dashboard widgets only support button-driven move/resize, not drag; `src/web` has no `dnd-kit`-equivalent dependency (unlike `platform_console`, which does use `@dnd-kit`) | P2 | L (generalize the tab-bar patterns into shared primitives) / XL (real undo/redo with a history log) | `WORKSPACE_INTERACTIONS.md` §0, §1–§5, §14–§15 — **a second real precedent now exists (Sprint 27.7):** the Enterprise Desktop's `WindowFrame.tsx` implements real move/resize/snap, independent of the tab bar's implementation; a future generalization pass should unify both, not just the tab bar |
| TD-43 | Naming / routing | Enterprise City has **three** route aliases (`/enterprise-city`, `/city`, `/city-hub`) and the Production Center has **two** (`/production-studio`, `/production`) — `ENTERPRISE_CITY_CORE.md` itself labels `/city-hub` "legacy module hub (optional)," suggesting even the implementing sprint considers it a candidate for removal, not a settled design | P2 | S (decide canonical route, deprecate the rest) | `ENTERPRISE_CITY_CORE.md`, `AI_PRODUCTION_CENTER_ARCHITECTURE.md` |
| TD-44 | Self-admitted UX debt | `WINDOW_MANAGER.md` explicitly states: *"`WorkspaceLayout` and `SettingsPage` honor `?embed=1`... Other hubs render their existing page; double chrome is acceptable until deeper embed coverage."* I.e., opening most modules inside a Desktop window currently shows nested/duplicate chrome (the module's own header on top of the window's) — a real, currently-visible visual defect the implementing sprint chose to ship with, tracked in its own doc but not previously in this registry | P2 | M (extend `?embed=1` handling to every hub, not just `WorkspaceLayout`/`SettingsPage`) | `WINDOW_MANAGER.md` |
| TD-45 | Missing backend / UI ahead of capability | The AI Production Center's 17-studio UI shell, agent-assignment controls, and approval-gated pipeline are real and shipped, but **no studio can actually generate anything** — no image/video/voice/avatar provider, no Content Factory HTTP route, no real publish trigger exist anywhere in the backend (unchanged since `AI_PRODUCTION_STUDIO.md` §0's original research). This is a real, present risk: a future sprint could be tempted to wire a quick generation call directly into the UI to "make a studio work," bypassing the provider-registry/approval/consent architecture `AI_PRODUCTION_STUDIO.md` and `AI_PRODUCTION_CENTER_BIBLE.md` §9 specify | P1 | XL (the real backend work `AI_PRODUCTION_CENTER_BIBLE.md` §10 sequences) | `AI_PRODUCTION_CENTER_BIBLE.md` §0, §9–§10 |
| TD-46 | Missing governance | Consent-record infrastructure for avatar/voice — **Sprint 30.0:** `platform_security.consent.ConsentRegistry` gate shipped; providers still must not be wired without calling `require_likeness_consent` | P0 → **Gate ready** | M | Sprint 30.0 · provider work still blocked until callers use the gate |
| TD-05 | Duplicate naming | `recommendation_engine` implemented independently in 6+ locations | P1 | M (docs) | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-06 | API | Unversioned legacy CRM `/api/*` mounted beside frozen `/api/v1` | P1 | M (docs only — do not remove) | `docs/TECHNICAL_DEBT_REPORT.md`, `API_MAP.md` |
| TD-07 | API | `/api/ai-os/v1` prefix shared between `applications/ai_os`, `platform_ai_os`, and hub MAOS | P1 | S (docs) | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-12 | Missing tests | Near-zero Vitest coverage for `src/web`'s `platform-builder/` pages | P1 | L | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-23 | Missing tests | `src/web` has **zero** `.test.tsx` component/route-render tests — all tests are `.test.ts` unit tests of config/registries/stores | P1 | M | direct test-file inventory |
| TD-13 | Missing documentation | Uneven OpenAPI spec coverage for Platform Builder / verticals | P1 | L | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-14 | Missing documentation / Ops | Dual runtime (Telegram bot + aiohttp API in one process) has no unified deploy story; `docker-compose.yml` defines only `postgres`+`redis`, no app service | P1 | M | `docs/TECHNICAL_DEBT_REPORT.md`, `docs/PRODUCTION_READINESS_AUDIT.md`, direct `docker-compose.yml` read |
| TD-15 | Product gap | Cafe vertical is catalog-only, no operational app | P1 | XL | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-24 | Architecture violation | 29 non-critical `reverse_layer_dependency` warnings across `platform_identity`, `platform_operations`, `platform_sdk`, `platform_integrations`, `platform_ai`, `repositories/` (9 files → `src/platform/layers`), etc. | P1 | L | `ARCHITECTURE_REPORT.md`, `docs/architecture_baseline/IMPORT_GRAPH.md`; full list in `DEPENDENCY_MAP.md` §7.2 |
| TD-25 | Legacy | `database_legacy.py` (11,205 lines) still imported outside `platform_legacy/`: `database/__init__.py`, `platform_architecture/*`, `scripts/check_no_sqlite.py`, `src/platform/layers/architecture_policy.py` | P1 | XL (full migration) / S (stop the `database/__init__.py` import specifically) | grep for `database_legacy` importers |
| TD-31 | Architecture / duplicate infra | Two Alembic-relevant migration directories exist: `./migrations` (pointed to by `alembic.ini`) and `./database/migrations` | P1 | S (confirm authoritative one) / M (consolidate) | `alembic.ini` + directory listing |
| TD-28 | Missing tests | `platform_console` has 10 built page components never wired into `App.tsx`'s route tree, and `ProtectedRoute`/`AdminShell` are defined but unused — no route currently enforces auth | P1 | S (wire in) | direct `App.tsx`/`pages/` comparison |
| TD-26 | Legacy | ~146 `# TODO: future implementation` markers in `database_legacy.py` (85), `handlers.py` (~40), `keyboards.py` (17) | P2 | XL | repo-wide grep |
| TD-04 | Duplicate naming | Digital Twin: PB visual vs hub EDT vs drone twin vs `applications/executive_center/twins.py` | P1 | M (docs) | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-27 | Duplicate code | `applications/platform_builder` has four structurally near-identical directories: `command_center/`, `control_center/`, `mission_control/`, `operations_center/` (same file shape, different name) — within a *single* application, not cross-repo naming drift | P2 | M | direct file-tree comparison |
| TD-10 | Product/UI | 8 frame-only Platform Builder builders (navigation destinations with no real content yet) | P2 | L | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-11 | Duplicate code | Duplicate `LoginPage` implementations: `src/web` auth flow vs `platform_console/src/pages/LoginPage.tsx` (unrouted) | P2 | S | `docs/TECHNICAL_DEBT_REPORT.md`, direct `platform_console` route read |
| TD-16 | Product gap | Beauty vertical exists only as libraries + hub integration, no `applications/beauty_*` app facade | P2 | L | `docs/TECHNICAL_DEBT_REPORT.md` |
| TD-29 | Dead code / scaffolding | Example vertical plugins (`plugins/agro`, `auto`, `construction`, `insurance`, `legal`, `medical`, `realty`) are never imported by any application/handler/router; `tests/test_plugins.py` exercises the plugin *system* via synthetic temp-dir fixtures, not these files | P2 | M | grep for `plugins.<name>` imports repo-wide |
| TD-30 | Dead code | Root `memory.db` (577 KB SQLite file) sits at repo root despite `POSTGRES_ONLY=true` / `scripts/check_no_sqlite.py` policy | P2 | S (confirm unused, then delete) | file listing + no-sqlite policy cross-check |
| TD-32 | Performance (unverified — flagged, not profiled) | No performance profiling was performed in this documentation pass; `platform_management.management_router` fans out to 9+ packages per request and `platform_operations.dashboard_service` aggregates 7 sub-services synchronously — worth a load-test pass before assuming it scales | P2 | L (profile first) | inferred from `DEPENDENCY_MAP.md` §3.1 fan-out; **not measured** |
| TD-33 | Disconnected system | The entire TS "ADOS OS" ecosystem (`src/kernel` + 6 packages, real non-trivial code) has no runtime connection to the Python backend — only `platform_console` calls it, over HTTP, with zero shared package dependency | P2 (not broken, just architecturally unresolved) | XL (needs a product decision, not a code fix) | `DEPENDENCY_MAP.md` §2, §6; `ARCHITECTURE_MAP.md` §15 |
| TD-34 | Missing documentation | `src/web/README.md` links to `docs/SPRINT_27_1_1_AUTH_RECOVERY.md` and `docs/SPRINT_27_1_RESULT.md` under a `src/web/docs/` directory that does not exist | P3 | S | direct file check |
| TD-35 | Missing documentation | Root-level infra (`services/`, `repositories/`, `database/`, `events/`, `api/`, `middleware/`, `routers/`, `src/`, `tests/`, `scripts/`) is not covered by any `.github/CODEOWNERS` pattern | P3 | S | direct `CODEOWNERS` read |

---

## 2. By category (detail)

### 2.1 Duplicate code

See TD-20 (EventBus ×6), TD-21 (memory ×2 full stacks + 3 minor), TD-22/TD-37 (workflow engine ×4 +
naming-collision alias), TD-27 (platform_builder command/control/mission/operations center ×4), TD-11
(LoginPage ×2), TD-05 (recommendation_engine ×6+), TD-39 (direct `crm_event_bus` imports bypassing the
canonical bus), TD-40 (two Command Palette implementations, one orphaned), TD-41 (favorites/recent-
history implemented twice with no shared state). Per the repo's own stated policy
(`docs/TECHNICAL_DEBT_REPORT.md` "Explicit non-actions"), **most of the backend-side duplication is
not slated for merging** — several are deliberately additive per-vertical or per-sprint
implementations. TD-40 and TD-41 are different in kind from those: they are frontend duplication with
**no additive justification** (one copy of each is simply dead or redundant), so unlike the backend
naming overlaps, these are worth fixing outright rather than documenting as accepted policy — see
`ENTERPRISE_NAVIGATION.md` §22 for the specific consolidation this registry recommends.

### 2.2 Dead code

- TD-18 — `container.py` DI scaffold, zero production consumers.
- TD-28 — `platform_console`'s 10 unrouted pages + unused `ProtectedRoute`/`AdminShell`.
- TD-29 — example vertical plugins never loaded outside their own protocol-conformance test.
- TD-30 — root `memory.db` leftover artifact.
- TD-40 — `navigation/components/CommandPalette.tsx` is real, compiled, exported code that is never
  imported or rendered anywhere in the app — a complete second command palette that silently never
  runs.

### 2.8 Missing interaction primitives (frontend)

New category, surfaced by `ENTERPRISE_NAVIGATION.md` and `WORKSPACE_INTERACTIONS.md`'s research —
not tracked by any prior report:

- TD-41 — no persistence layer for favorites, recent history, or dashboard/widget layout (dock layout
  is the sole exception, persisted to `localStorage`); `layoutManager.features()` lists
  `"drag_drop"`/`"docking"` as capability metadata strings that are not actually implemented.
- TD-42 — no general-purpose drag-and-drop, multi-selection, context-menu, or undo/redo primitive
  exists in `src/web`; the only real precedents (drag-reorder, right-click menu, one-level "reopen
  last closed") are confined to `WorkspaceTabBar.tsx` and have never been generalized to other
  surfaces (widgets, asset lists, City buildings).

### 2.3 Legacy modules

- TD-25 — `database_legacy.py` still imported outside `platform_legacy/`.
- TD-26 — ~146 unresolved `# TODO: future implementation` markers in the legacy monolith
  (`database_legacy.py`, `handlers.py`, `keyboards.py`).
- TD-36 — 47 legacy `services/pg_*` dependency cycles, per the prior architecture-baseline run;
  explicitly deferred with the justification "contained in compatibility layer... removing them
  requires Sprint 2 adapter extraction without business logic change" — re-verify this justification
  still holds before treating it as settled.
- TD-38 — 4 allowlisted files with direct handler→DB access bypassing the repository layer.
- Every subsystem in `LEGACY_MIGRATION.md`'s 10-subsystem matrix (ai, configuration, managers,
  notifications, repositories, requests, scheduler, telegram, users, workflow) currently has its
  migration feature flag at `False` and its "deprecated API removal date" at "None" — i.e. **no
  legacy subsystem has an active migration in flight**; this is a standing fact worth periodically
  re-checking rather than a one-time debt item (re-verify each sprint against the live file).

### 2.4 Architecture violations

- TD-17 (P0, CI-blocking) — the 4 critical `env_access_outside_center` violations.
- TD-19 — `database/__init__.py` → `database_legacy` (a modern package depending on the legacy layer
  it should be isolated from).
- TD-24 — the 29 non-critical `reverse_layer_dependency` warnings (full list: `DEPENDENCY_MAP.md` §7.2).
- TD-31 — two migrations directories.
- TD-36/TD-37/TD-38/TD-39 — carried over from the prior architecture-baseline run (2026-07-19); note
  that `docs/architecture_baseline/DEPENDENCY_GRAPH.md` (also generated 2026-07-19) reports **0 strict
  cycles in governed layers**, which sounds like it contradicts TD-36's "47 legacy pg engine
  dependency cycles" — the likely reconciliation is that TD-36's cycles are *within* the
  `platform_legacy` compatibility layer specifically (excluded from the "governed layers" cycle count),
  not a contradiction in the data. **Re-run both tools together next sprint and confirm this
  reconciliation explicitly** rather than assuming it.

Full detail and regeneration instructions: `DEPENDENCY_MAP.md` §7–8; regenerate via
`scripts/validate_architecture.py` each sprint and reconcile this section against its output.

### 2.5 Performance issues

**Not profiled in this documentation pass** — no load-testing or query-plan analysis was performed
while compiling this registry (`ARCHITECTURE_MAP.md`/`DEPENDENCY_MAP.md`/this file are a structural
read of the codebase, not a runtime audit). `platform_performance/`, `platform_enterprise_
performance_testing/`, and `docs/API_CORE_AUDIT.md`/`docs/PRODUCTION_READINESS_AUDIT.md` are the
existing sources of truth for actual measured performance; consult those before treating TD-32 as
more than a hypothesis. TD-32 records the one structurally-visible fan-out risk worth a deliberate
load test (`platform_management.management_router`'s 9-package fan-out,
`platform_operations.dashboard_service`'s 7-service synchronous aggregation) — it is a candidate to
verify, not a confirmed problem.

### 2.6 Missing tests

- TD-12 — near-zero Vitest coverage for Platform Builder pages in `src/web`.
- TD-23 — zero `.test.tsx` render tests anywhere in `src/web`.
- TD-28 — `platform_console` auth is untested because it's unrouted.
- None of the 17 `applications/*` verticals has its own dedicated test directory (coverage, if any,
  lives in root `tests/` — not verified file-by-file in this pass; worth a targeted check per app).
- `container.py` is only exercised by scaffold tests (TD-18), not real usage tests — expected, since
  it has no real usage.

### 2.7 Missing documentation

- TD-13 — uneven OpenAPI coverage for PB/verticals.
- TD-34 — two dead doc links in `src/web/README.md`.
- TD-35 — CODEOWNERS gaps for root infra and `src/`.
- The relationship between the TS "ADOS OS" ecosystem and the Python platform (TD-33) has never been
  written down as a decision anywhere found in `docs/` — it exists as an emergent fact of the
  codebase, not a documented choice. This is the single highest-value documentation gap to close,
  since it affects how much future work should go into `src/kernel` and friends at all.

---

## 3. How to keep this registry current

1. When you fix an item, move it out of §1 (or mark it `RESOLVED — <sprint id>` and keep the row for
   history) rather than deleting the row silently — the sprint `RESULT.md` should reference the ID.
2. When you find new debt, add a new `TD-<next number>` row — never reuse or renumber an existing ID.
3. Re-run `scripts/validate_architecture.py` and `scripts/generate_architecture_baseline.py` each
   sprint; reconcile §2.4 against their fresh output (counts drift as the codebase grows).
4. If a debt item here is deliberately accepted as permanent (e.g. most of the "additive naming"
   items per repo policy), say so explicitly in the row rather than leaving it looking unresolved —
   add a `Severity: P3 (accepted)` note.

## 4. Overnight Architecture Audit addition (TD-47 onward)

**Source:** a full-repo overnight architecture audit (documentation only, `src` not modified),
building on a twenty-sprint architecture-research engagement (Sprints CG-4 through CQ-20) that
independently re-derived several items already in §1 above (TD-01–TD-05, TD-20, TD-21, TD-22) via
direct code research, plus found the following genuinely new items. Per this file's own §3 rule,
these continue the numbering — nothing above is renumbered.

| ID | Category | Debt | Severity | Effort | Evidence |
|---|---|---|---|---|---|
| TD-47 | Duplicate code | **Six**, not four, independent real deal/pipeline implementations — `TD-22` undercounts this specific case: `deals.py`'s generic `Deal`, `deal.py`'s `DealEngineDeal`, `deal_engine_v1.py`'s superseded `DealEngineV1Deal`, `deal_pipeline_engine.py`'s `PipelineDeal`/`DealPipelineStageCode` (most mature — real tenant-configurable `DealStage.allowed_next_stages`, real SLA, real `DealStageHistory.validation_passed` audit trail), `lead_engine.py`'s `LeadEngineLead`, `automotive_sales.py`'s `Lead`/`SalesPipelineStage` | P1 | L (docs) / XL (consolidate) | `docs/ENTERPRISE_VALUE_CHAIN.md` §2, `docs/SPRINT_CQ_18_RESULT.md` |
| TD-48 | Duplicate code | `TD-22`'s "4+ workflow engines" is stale — confirmed **seven**: the four/six backend engines plus a real, substantial, previously-uncited **frontend** engine, `src/web/src/runtime/workflowRuntime/` (Sprint 29.4-ish), architecturally disconnected from all backend engines (composes only `commandRuntime`/`enterpriseEventBus`, no backend call). Also confirmed: none of the backend engines has a tenant-configurable transition table — that pattern is unique to `deal_pipeline_engine.py` | P1 | L (docs) / XL (consolidate) | `docs/ENTITY_RECONCILIATION.md` §3, `docs/SPRINT_CQ_19_RESULT.md` |
| TD-49 | Duplicate naming | Four real, sequential, **self-aware** "unify the knowledge/ontology model" systems, each announcing itself as the consolidator of the one before and each choosing addition over merge: `docs/KNOWLEDGE_GRAPH.md` (12.0, `/api/ai-ecosystem/v1/knowledge`), `docs/UNIFIED_KNOWLEDGE_GRAPH.md` + `docs/ENTERPRISE_ONTOLOGY.md` (19.2, `/api/enterprise-kg/v1`), `docs/ENTERPRISE_KNOWLEDGE_PLATFORM.md` (20.3, `/api/enterprise-ekp/v1` — explicitly renamed its own package because `knowledge/` was "reserved"), `docs/ENTERPRISE_KNOWLEDGE_GRAPH.md` (24.2, `/api/enterprise-ekg/v1`, real `ENTITY_TYPES`/`RELATION_TYPES`, self-described "additive to legacy"). A bare top-level `./knowledge` directory also exists at repo root, separate from all four | P1 | M (docs) | `docs/ENTERPRISE_ONTOLOGY.md` (Sprint CQ-20 addition), `docs/SPRINT_CQ_20_RESULT.md` |
| TD-50 | Duplicate code | At least three independent real "task" concepts, none reconciled: `database/models/tasks.py`'s generic `Task` (has a `module` field and a real FK to `calendar_events.id`, but its own `project_id` column is **not a real foreign key** — untyped, no relationship), `deal_pipeline_engine.py`'s `DealTask` (separate table, separate `DealTaskStatus` enum, Telegram-`BigInteger` assignee instead of `users.id`), and the frontend `ProjectParticipant.assignments` (plain `string[]`, not a task entity at all) | P1 | M (docs) / L (reconcile) | `docs/ENTITY_RECONCILIATION.md` §2, `docs/SPRINT_CQ_19_RESULT.md` |
| TD-51 | Missing feature | No real backend `Project` entity exists anywhere (`grep "class Project" database/models/*.py` → zero hits), despite `platform_enterprise_knowledge_graph.ENTITY_TYPES` already naming `"project"` as a first-class entity kind (TD-49's system). The sales side of the value chain (Lead→Contract) is real and rich (TD-47); execution/delivery has only the thin frontend `ProjectParticipant` (participation only, no status/budget/milestone fields) | P1 | M (add `Project` table + `Deal.project_id` FK) | `docs/PROJECT_LIFECYCLE.md`, `docs/SPRINT_CQ_18_RESULT.md` |
| TD-52 | Duplicate code | Three real, unreconciled permission-scope vocabularies with different ranks/meanings for the same word: `SpatialPermissionScope` (`spatialPermissions.ts`: public<citizen<company<assigned<enterprise_admin`), `AssetPermissionScope` (`assetTypes.ts`: owner<assignee<department<company<partner<public<enterprise_admin — not even the same rank order for `company`), and business `Visibility` (`public\|network_only\|partners_only\|private`) | P1 | M (docs) / L (unify Spatial+Asset) | `docs/DIGITAL_TWIN_STANDARDS.md` §2, `docs/SPRINT_CQ_16_RESULT.md` |
| TD-53 | Duplicate code | Three real, independently-authored notification-category vocabularies, none mapping cleanly onto each other: legacy `NOTIFICATION_CATEGORIES` (`database_legacy.py:5904`, per-vertical), the unified `docs/NOTIFICATION_CENTER.md`/`NOTIFICATION_CHANNELS.md` system (`/api/enterprise-comms/v1`), and frontend `NotificationKind`/`NotificationBucket` (`notificationStore.ts`) | P2 | M (docs) | `docs/OPERATIONAL_NOTIFICATIONS.md`, `docs/SPRINT_CQ_17_RESULT.md` |
| TD-54 | Missing infra → **RESOLVED (Sprint 35.1)** | `VersionMixin` / `VersionColumnsMixin` retrofitted across SQLAlchemy persistent models; Alembic `h1b234567890` adds columns to core tables + optional `platform_state_events`. Entity UUID `tenant_id` preserved (mixin does not declare String tenant_id). Runtime VersionEngine + HA warm_start shipped. | P2 → **Done** | — | `docs/FOUNDATION_COMPLETION_35_1.md`, `docs/VERSION_ENGINE.md` |
| TD-55 | Dead code | `src/domains` (a Python package tree under `src/`, distinct from the TS kernel and from root-level `platform_*`/`applications/*`) contains **141 real `.py` files** with essentially zero external imports found repo-wide (`grep -rl "from src.domains\|import src.domains"` outside its own tree returns effectively nothing) — a large, apparently-abandoned parallel domain-model effort, larger in file count than most single `platform_*` packages | P1 | S (confirm zero usage, then decide: delete or document as intentionally dormant) | direct `find`/`grep` this audit, `src/verticals`/`src/platform`/`src/events` likely share this status — not individually re-verified |
| TD-56 | Naming / code organization | Repo root has **~100 top-level directories** with no grouping/namespace — 60+ `platform_*`/`platform_enterprise_*` packages sit at the same directory level as core infra (`api/`, `database/`, `services/`, `middleware/`). Two bare top-level directories, `./platform` and `./workflow`, exist alongside (and are trivially confusable with) `platform_*`/`platform_workflow`/`platform_workflows` — an import-time footgun (`import platform` shadows/confuses with the stdlib module name too) | P2 | XL (would require a real restructure, out of scope for "don't move files without being asked") | direct `find . -maxdepth 1 -type d` this audit |
| TD-57 | Security — **CONFIRMED, re-scoped Sprint CQ-30** | `configuration_center.py` now has real validation logic (`validate(*, fail_fast: bool = False)`, a real `_INSECURE_JWT_SECRETS` frozenset check, a real passing test `tests/test_configuration_center.py:47-53`), but `startup.py:54` calls it with `fail_fast=False` — the real production-startup call site explicitly does not block on an insecure `JWT_SECRET`/`IAM_JWT_SECRET`. Meanwhile `platform_identity/jwt_service.py`'s separate `validate_iam_jwt_secret()` **does** unconditionally raise and **is** called at startup (`startup.py:57-59`) — one of the platform's two JWT-secret paths is fail-closed, the other is fail-open by explicit configuration. **Sprint 30.0:** secrets normalized via `platform_security.jwt_secrets`; single `resolve_iam_signing_secret()`; production validate now also checks API JWT + SECURITY_MASTER_KEY; startup uses fail_fast in production | P0 → **Hardened** | S | Sprint 30.0 + CQ-30 |
| TD-58 | Missing tests / security | Tenant-filter completeness — **Sprint 30.0:** `TenantIsolationError` + required filters by default + `scripts/audit_tenant_isolation.py` → `docs/TENANT_ISOLATION_AUDIT.md`; residual heuristic findings remain | P1 → **In progress** | M | Sprint 30.0 |
| TD-59 | Duplicate infra / duplicated runtime concepts | A third and fourth real cross-runtime layer have appeared over the same 11 base frontend runtimes since the last audit: `src/web/src/runtime/orchestrator/EnterpriseOrchestrator.ts` (Sprint 29.8, "Central coordination layer") and `src/web/src/runtime/kernel/EnterpriseKernel.ts` (Sprint 29.9, wraps the orchestrator for bootstrap) — in addition to the already-known `cityVisualization` (Sprint 29.5). No relationship between `cityVisualization` and the new `orchestrator` was found; each independently derives its own view of runtime health | P1 | S (document the intended layering) / M (re-plumb `cityVisualization` to consume `orchestrator`'s health state, if that's the right answer) | `docs/RUNTIME_CONSISTENCY.md` Issue 1, `docs/DOMAIN_BOUNDARIES.md` Issue 1 (Sprint CQ-30) |
| TD-60 | Duplicate naming | "Kernel" and "Orchestrator" now each name **two** fully independent real systems: the standalone TS `@ados/kernel`/`@ados/orchestrator` packages (`src/kernel`, `src/orchestrator`, already tracked by `TD-33`) and the new frontend `src/web/src/runtime/kernel`/`src/web/src/runtime/orchestrator` (TD-59). No cross-import between either pair; a more acute instance of the `TD-01`–`TD-05`/`TD-49` naming-collision pattern because both terms are unusually generic, load-bearing architecture vocabulary | P1 | S (add explicit disambiguation notes wherever either pair is introduced in docs; no rename) | `docs/RUNTIME_CONSISTENCY.md` Issue 2 (Sprint CQ-30) |

## 5. Sprint 32.2 Platform Core Governance addition (TD-61 onward)

**Source:** Sprint 32.2 Platform Core Refactoring & Architecture Governance track (composed Core inventory + sprint review; no `platform_core/` package). Categorized index: [`TECH_DEBT_REGISTRY.md`](./TECH_DEBT_REGISTRY.md).

| ID | Category | Debt | Severity | Effort | Evidence |
|---|---|---|---|---|---|
| TD-61 | Architecture / adapters | Auto marketplace still ships local `authentication/`, `notifications/`, `search/`, `pricing/` trees that look like Core services; SoR remains Platform Core (`platform_identity`, comms hub / `notification_center`, `search_service`, `pricing_engine`). Adapters must stay thin via `PlatformBridge` — migration is multi-sprint | P1 | L | `platform_architecture/core_inventory.py`, `docs/CORE_SERVICES.md`, `docs/SPRINT_32_2_RESULT.md` |
| TD-62 | Architecture / organization | There is no single `platform_core/` package — Core is intentionally **composed**. Without continuous inventory discipline, teams re-invent "Platform Core" folders. Mitigated by `core_inventory.py` + `architecture_sprint_review.py`; full physical regroup remains out of scope (related TD-56) | P2 | XL (restructure) / S (keep inventory current) | `docs/PLATFORM_CORE.md`, Sprint 32.2 |
| TD-63 | Missing feature | Universal Service Constructor is **foundation-only** (`service_constructor_foundation.py`) — no UI, no wire-up to ServiceListing / marketplace publish path | P2 | L (product track) | `docs/PLATFORM_CORE.md`, Sprint 32.2 |

## 6. Sprint 32.3 Enterprise Consolidation addition (TD-64 onward)

| ID | Category | Debt | Severity | Effort | Evidence |
|---|---|---|---|---|---|
| TD-64 | Architecture / adapters | Canonical owners declared (deal / workflow / knowledge / notify / queue) but legacy engines remain runnable adapters — full cutover is multi-sprint (TD-22/47/48/49/53) | P1 | XL | `docs/CANONICAL_SERVICES.md`, `SPRINT_32_3_RESULT.md` |
| TD-65 | Security | `configuration_center` / `settings.py` still use load-time placeholder strings for local boot (`change-me-in-production`); production `validate(fail_fast=True)` rejects them — remaining risk is non-production mis-deploy without ENVIRONMENT=production | P1 | M | `secret_policy.py`, Sprint 32.3 |

## 7. Sprint 32.4 Security Center addition (TD-66 onward)

| ID | Category | Debt | Severity | Effort | Evidence |
|---|---|---|---|---|---|
| TD-66 | Security / integration | Security Center policies (anti-parsing, external AI signing, incident disable flags) are platform SoR but not yet wired into every HTTP/APH path — callers must adopt `enterprise_security_center` progressively | P1 | L | `SPRINT_32_4_RESULT.md` |
| TD-67 | UX / security | Owner `securityCenter.ts` still seeds demo metrics when ISAM owner dashboard is unreachable — live-only cutover remaining | P2 | M | `src/web/auth/managers/securityCenter.ts` |

### Note (TD-22 / TD-05 staleness)

- **TD-22 is stale**: written when 4 backend workflow engines were known; TD-48 records the
  now-confirmed 7 (6 backend + 1 disconnected frontend). Left as-is per this file's own "never
  renumber" rule; TD-48 is the correction.
- **TD-05's "6+ locations" for `recommendation_engine`** was not independently re-verified in the overnight pass —
  carried forward as-is.

## Related documents

- `ARCHITECTURE_MAP.md` — narrative context for why each violation/duplication exists.
- `DEPENDENCY_MAP.md` — the exact edges behind TD-17, TD-19, TD-24, TD-31.
- `MODULES.md` — per-module "Tech debt" column links back to the IDs in this registry.
- `API_MAP.md` — endpoint-level detail behind TD-06, TD-07, TD-08, TD-13.
- `docs/TECHNICAL_DEBT_REPORT.md` — the original Sprint 30.2 report this registry extends (TD-01–TD-16).
- `docs/TECH_DEBT_REGISTRY.md` — categorized index (Architecture / Performance / Security / UX / Infrastructure).
- `docs/PLATFORM_CORE.md` · `docs/CANONICAL_SERVICES.md` · `docs/ARCHITECTURE_GOVERNANCE.md` — Sprint 32.2–32.3 Core + consolidation.
