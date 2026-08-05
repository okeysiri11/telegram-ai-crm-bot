# Module Catalog — ADOS / BIDEX Enterprise Platform

**Status:** permanent, living document. **Update this file in the same PR/sprint that adds, renames,
retires, or changes the status of a module** — see `CLAUDE.md`'s "Every sprint must generate a
RESULT.md" rule; note any module-catalog change in that sprint's RESULT.md.

**Scope decision:** "every module" is catalogued at the **package/directory level** — every
`platform_*` package (106), every `applications/*` vertical (17), every TS kernel package (7), both
frontends (2), and the root-level infrastructure packages (`services/`, `repositories/`, `database/`,
`events/`, `api/`, `middleware/`, `routers/`, `container.py`, `platform_legacy/`). Cataloguing every
individual `.py`/`.ts` file (there are 800+ in the Python dependency graph alone) would not stay
maintainable as living documentation; per-file detail belongs in `DEPENDENCY_MAP.md`'s edge lists and
in each package's own `README.md`/docstrings.

**Ownership convention:** this repo has one `.github/CODEOWNERS` file, currently assigning
`@macbook` to `/platform_*/`, `/applications/`, `/docs/`, `/ecosystem/`, `/knowledge/`, `/.github/`.
Paths not covered by any CODEOWNERS pattern are marked **Unassigned** below — that is a factual
statement about the current CODEOWNERS file, not a judgment; add a pattern to
`.github/CODEOWNERS` when a module gets a real owner/team.

**Status vocabulary used below** (inferred from manifests, sprint docstrings, test presence, and
docs — not all packages self-declare a status, so treat inferred statuses as a starting point to
confirm, not a certified fact):

- **Production** — manifest/docs explicitly say so, or it's mounted in `api/server.py` and has tests.
- **Active** — real implementation, integrated into the platform, ongoing sprint work.
- **Additive/Parallel** — deliberately added alongside an older sibling per repo policy (mostly
  `platform_enterprise_*`), not yet consolidated.
- **Scaffold/Stub** — thin implementation, few files, or explicitly commented as scaffolding.
- **Legacy (frozen)** — superseded by a modern equivalent but still imported; do not extend, migrate
  off per `LEGACY_MIGRATION.md`.
- **Disconnected** — real code, but confirmed to have no runtime link to the production Python
  backend (the TS kernel ecosystem).

---

## 1. Bot & startup (repo root)

| Module | Purpose | Owner | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|---|
| `main.py` | Bot process entrypoint (asyncio loop, polling lifecycle) | Unassigned | `main()` | `bootstrap`, `startup` | Active | None significant | — |
| `bot.py` | Backward-compatible re-export shim | Unassigned | re-exports `bot`, `build_dispatcher`, `close_fsm_storage`, `create_fsm_storage`, `main` | `bootstrap`, `main` | Legacy (frozen) | Kept only for import compatibility | Remove once no external code imports `bot.py` directly |
| `bootstrap.py` | Builds aiogram `Dispatcher` + FSM storage | Unassigned | `bot`, `build_dispatcher`, `close_fsm_storage`, `create_fsm_storage` | `config`, aiogram | Active | — | — |
| `startup.py` | Background services, API server, diagnostics before polling | Unassigned | `run_startup()`, `shutdown_startup()`, `register_routers()`, `BOT_ROUTER_PATHS` | `platform_configuration`, `platform_identity`, `api.server`, `platform_legacy`, `events.handlers`, `events.crm_publisher` | Active | Central place new services must be wired into by hand (no DI) | See `container.py` decision in `TECH_DEBT.md` |
| `config.py` | Legacy config facade — proxies `ConfigurationCenter` | Unassigned | module-level constants (`API_HOST`, `API_PORT`, etc.) | `platform_configuration.configuration_center` | Legacy (frozen), but load-bearing | Still directly imported by `bootstrap.py`, `startup.py`, `openrouter.py`, `fsm_storage.py`, `database_legacy.py`, several `*_handlers.py` | Migrate remaining direct importers to `platform_configuration` directly |
| `container.py` | DI scaffold (`AppContainer`/`ServiceRegistry`) | Unassigned | `get_container()`, `AppContainer`, `ServiceRegistry` | none (deliberately standalone) | Scaffold/Stub — **not wired into bot startup** | Zero production consumers; only used by `tests/unit/test_container_scaffold.py` | Decide: wire in or remove (see `TECH_DEBT.md` TD item) |
| `handlers.py` | Original monolithic Telegram bot handlers (~5,000+ lines) | Unassigned | aiogram router registrations | `database_legacy`, `services.*`, `keyboards` | Legacy (frozen) | ~40 `# TODO: future implementation` markers | Migrate features into `platform_workflow`/domain services per `LEGACY_MIGRATION.md` |
| `keyboards.py` | Telegram inline/reply keyboard builders (65KB) | Unassigned | keyboard-builder functions | aiogram | Legacy (frozen) | 17 `# TODO: future implementation` markers for unbuilt hub UIs | — |
| 21× root `*_handlers.py` | Legacy feature handlers (ai_sales, anti_loss_layer, auto_vertical, automotive_partner/revenue, bidex_quote, cart_engine, crm_pipeline_boards, deal_engine/workflow, dealer_onboarding/quote_authority, lead_engine, owner_dashboard/panel/payment_profile, partner_cabinet, payment_engine, revenue_engine, start_routing, tenant_guard, vertical_onboarding) | Unassigned | aiogram router registrations | `services.pg_*`, `database_legacy` | Legacy (frozen) | Wrapped by `platform_legacy`, not to be extended directly | Migrate per `LEGACY_MIGRATION.md`'s 10-subsystem matrix |
| `database_legacy.py` | Monolithic legacy DB module (11,205 lines) | Unassigned | dozens of direct functions (`ensure_user()`, `get_user_roles()`, `assign_role()`, `save_memory()`, etc.) | none upstream; imported by `database/__init__.py`, `platform_architecture/*`, `scripts/check_no_sqlite.py`, `src/platform/layers/architecture_policy.py` | Legacy (frozen) | 85 `# TODO`; still imported by non-legacy code (§ policy violation, see `TECH_DEBT.md`) | Fully replace with `repositories/`+`database/` |
| `platform_events_legacy.py` | Legacy event bus (own `EventBus` class, 345 lines) | Unassigned | `EventBus` | none upstream; imported by `platform_architecture/*`, `tests/test_unified_event_bus.py`, `platform_legacy/*` | Legacy (frozen) | A 6th independent `EventBus`-named class in the repo | Retire once all legacy event flows move to `events.event_bus.PlatformEventBus` |
| `openrouter.py` | OpenRouter LLM API client | Unassigned | client functions | `config` | Legacy-adjacent | — | Migrate to `platform_ai.provider_manager` |
| `fsm_storage.py` | FSM storage factory (Redis/memory) | Unassigned | `create_fsm_storage()`, `close_fsm_storage()` | `config` | Active | — | — |

---

## 2. Core data/service infrastructure (repo root)

| Module | Purpose | Owner | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|---|
| `services/` (232 files) | Business logic, no direct HTTP exposure | Unassigned | one class/function set per file (too many to list; see `DEPENDENCY_MAP.md` §3.1 for hub edges) | `repositories/`, `database/`, `events/`, various `platform_*` | Mixed: 101 `pg_*` files are Legacy (frozen, classified as "legacy" layer by the module graph); the rest are Active | `*_test.py` files co-located here instead of `tests/` | Continue migrating `pg_*` engines into `platform_*` capability packages |
| `repositories/` (111 files) | Postgres data access, all SQLAlchemy | Unassigned | one repository class per file (`*Repository`) | `database/`, and (9 files) `src/platform/layers/base_repository.py` | Active | 9 files cross the `src/` tree boundary (`DEPENDENCY_MAP.md` §7.2); `base_repository.py` itself is a 4-line re-export shim | Move the real `BaseRepository` into `repositories/` itself, or formally adopt `src/platform/layers/` as the canonical home |
| `database/` | Canonical DB package: models/, engine, session, migrations | Unassigned | `database.session` (`check_db_health`, `shutdown_db`), `database.engine`, `database.models.*` (119+ model files) | `platform_configuration.configuration_center`, imports `database_legacy` from its own `__init__.py` | Active, but entangled with legacy | `database/__init__.py` imports `database_legacy` — violates the intended legacy-isolation boundary | Remove the `database_legacy` import from `database/__init__.py` |
| `migrations/` (root) | Alembic migrations, `script_location` per `alembic.ini` | Unassigned | Alembic revision files | `database/` models | Active | **Two migrations directories exist** (`./migrations` vs `./database/migrations`) — authority unclear | Consolidate to one directory; document which is canonical |
| `events/` | `PlatformEventBus` — canonical in-process event bus | Unassigned | `PlatformEventBus`, `publisher.py`, `crm_publisher.py`, `handlers/*`, `adapters/*` | `database`, `platform_legacy` (via `legacy_adapter.py`) | Active — canonical | Not the only `EventBus` in the repo (5+ others, see `TECH_DEBT.md`) | — |
| `api/` | HTTP app factory — mounts every route family | Unassigned | `create_app()` (in `api/server.py`) | `platform_management`, `platform_api`, 15× `applications/*/api/register.py` | Active — canonical entrypoint | Legacy CRM `/api/*` remains unversioned by design (documented debt, not accidental) | — |
| `platform_api/` | Frozen contracts/envelope types (no routes) | @macbook (`platform_*` CODEOWNERS pattern) | `ApiEnvelope`, `PaginatedResponse`, `ErrorResponse`, `API_CONTRACT_VERSION` | none | Production — frozen contract | — | Never break; version any change |
| `platform_management/` | Authenticated admin REST (`/management/v1`) | @macbook | `register_management_routes()`, `management_service`, `ManagementService` | `platform_identity`, `platform_configuration`, `platform_legacy`, `platform_ai`, `platform_plugins`, `platform_sdk`, `platform_operations`, `platform_realtime`, `platform_jobs`, `services.*` | Production — the current admin surface | Most-depended-on hub package (`DEPENDENCY_MAP.md` §3.1) — a single point of coupling for many packages | — |
| `middleware/` | `entry_point_middleware.py`, `error_tracking_middleware.py`, `tenant_middleware.py` | Unassigned | aiogram middleware classes | `services.pg_entry_point_engine`, `services.pg_vertical_onboarding_engine`, `services.error_tracking_service`, `TenantContextService` | Active | — | — |
| `routers/` (8 files + empty `admin/`) | Telegram bot routers | Unassigned | aiogram `Router` per file | `services.*`, `database.*` | Active | `routers/admin/` exists but is empty (no `.py` source) | Populate or remove `routers/admin/` |

---

## 3. Governance & cross-cutting `platform_*` packages

| Module | Purpose | Owner | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|---|
| `platform_architecture/` | Executable governance rules, dependency graph, CI validation | @macbook | `ArchitectureCertification`, `ArchitectureGovernance`, `QUALITY_GATES`, `rules.py`, `import_scanner.py` | `database_legacy`, `platform_events_legacy` (for scanning) | Production — runs in CI | Depends on the very legacy modules it's meant to police (necessary for scanning, but worth noting) | — |
| `platform_legacy/` (21 files) | Legacy compatibility/isolation boundary | @macbook | `legacy`, `legacy_registry`, `scan_legacy_import_violations`, `migration_manager`, `compatibility_layer`, `deprecation_manager`, `deprecated`, `build_migration_report`, `runtime_monitor` | `handlers.py`, `database_legacy.py`, `openrouter.py`, `services.pg_*` | Active — sanctioned boundary | Depended upon (in reverse) by `platform_identity`, `platform_integrations`, `platform_sdk`, `platform_configuration`, `events.adapters`, `platform_workflows.adapters` — see `DEPENDENCY_MAP.md` §7.2 | Reduce the 29 `reverse_layer_dependency` warnings over time |
| `platform_certification/` | Sprint 1.5 production-readiness gates | @macbook | `PlatformCertification`, `checks.py`, `gates.py`, `runner.py` | — | Production | — | — |
| `platform_validation/` | Validation/certification manager | @macbook | `CertificationManager`, `CompatibilityManager` | — | Active | — | — |
| `platform_quality/` | Sprint 21.5 test/QA library | @macbook | `QualityLibrary` | — | Additive | Docstring notes it doesn't duplicate `platform_testing` | — |
| `platform_testing/` | Sprint 25.1 "Unified Test Center" | @macbook | `TestInfrastructureLibrary` | — | Additive | Docstring: "does not duplicate platform_quality/EQA" | — |
| `platform_security/` | Sprint 21.4 security hardening | @macbook | `SecurityHardeningLibrary` | — | Production, but **failing CI governance** | `config.py:23-24`, `secrets.py:30,80` bypass `ConfigurationCenter` — the repo's 4 critical CI violations | Fix immediately (`TECH_DEBT.md` #1) |
| `platform_enterprise_security_verification/` | Enterprise security verification layer | @macbook | `*Library` facade | — | Additive/Parallel | Docstring: "Legacy ESH platform_security remains unchanged" | — |
| `platform_observability/` | Unified telemetry layer | @macbook | `AlertManager`, `DiagnosticManager`, `HealthManager`, `telemetry_router.py` | `platform_management.management_service` (reverse dep) | Production | One `reverse_layer_dependency` warning (`metrics_service.py`) | — |
| `platform_reliability/` | Fault tolerance / recovery layer | @macbook | `CheckpointManager`, `CircuitBreaker`, `FailoverManager` | — | Active | — | — |
| `platform_configuration/` | Configuration Center + deployment layer (Sprint 5.4) | @macbook | `configuration_center`, `config_provider`, `config_service`, `ConfigurationLoader`, `env_access_policy` | `platform_legacy` (reverse dep, `config_service.py`) | Production — canonical config engine | Its own `env_access_policy.py` exists specifically to prevent the violation `platform_security` currently commits | — |
| `platform_operations/` | Ops dashboard backend | @macbook | `operations_service`, `operations_dashboard_service` | `platform_management.*` (reverse dep, 3 files), `platform_jobs.job_engine`, `platform_observability.dashboard_metrics`, `services.*` | Active | 3 `reverse_layer_dependency` warnings | — |
| `platform_performance/` | Sprint 21.7 perf/load testing | @macbook | `PerformanceLibrary` | — | Additive | — | — |
| `platform_enterprise_performance_testing/` | Enterprise performance testing layer | @macbook | `*Library` facade | — | Additive/Parallel | Docstring: "Legacy EPF platform_performance remains unchanged" | — |
| `platform_release/` | Sprint 21.8 release readiness | @macbook | `ReleaseLibrary` | — | Active | — | — |
| `platform_migration/` | Sprint 25.4 DR/upgrade | @macbook | `MigrationLibrary` | — | Active | — | — |
| `platform_documentation/` | Sprint 21.6 docs platform | @macbook | `DocumentationLibrary` | — | Active | — | — |
| `platform_chaos/` | Sprint 25.3 chaos engineering | @macbook | `ChaosLibrary` | — | Active | — | — |

---

## 4. API / identity / integration `platform_*` packages

| Module | Purpose | Owner | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|---|
| `platform_identity/` | Single authorization source | @macbook | `IdentityService`, `authentication_service`, `authorization_service`, `register_identity_routes` | `platform_management.{permissions, exceptions}` (reverse dep), `platform_legacy` (4 files, reverse dep) | Active, auth is header-only pending full token flow | 5 `reverse_layer_dependency` warnings — heaviest concentration of any single package | Complete the live token round-trip (see `TECH_DEBT.md`) |
| `platform_integrations/` | Single entry point for external systems | @macbook | `IntegrationService`, `register_integration_routes` | `platform_legacy` (`webhook_manager.py`, reverse dep) | Active | 1 `reverse_layer_dependency` warning | — |
| `platform_jobs/` | Job/automation engine | @macbook | `JobEngine`, `register_jobs_routes` | — | Active | — | — |
| `platform_realtime/` | Live state publisher | @macbook | `RealtimeHub`, `RealtimeEventDispatcher`, `register_realtime_routes` | `platform_plugin_sdk` (dependent, not dependency) | Active | — | — |
| `platform_plugins/` | Installable business-domain modules | @macbook | `plugin_manager`, `PluginRecord`, `plugins_router.py` | dynamic `discover()` mechanism | Active, but **example plugins never load in production** | `plugins/agro|auto|construction|insurance|legal|medical|realty` are scaffolding — `tests/test_plugins.py` uses synthetic temp-dir fixtures, not the real files | Either wire real example plugins in, or clearly label `plugins/` as templates only |
| `platform_plugin_sdk/` | Official plugin extension API | @macbook | `PlatformPlugin`, `PluginBuilder`, `PluginContext` | `platform_ai.*`, `events.*`, `platform_configuration.config_provider`, `platform_sdk.*`, `platform_integrations.integration_service`, `platform_observability.metrics_service`, `platform_jobs.job_engine`, `platform_identity.identity_service`, `platform_realtime.*` | Active — the widest fan-out dependency of any `platform_*` package | Large surface area to keep stable given how many packages it touches | — |
| `platform_sdk/` | Extensible vertical framework (Phase 1) | @macbook | `PlatformVertical`, `VerticalBuilder`, `VerticalRegistry` | `platform_legacy` (3 files, reverse dep) | Active | 3 `reverse_layer_dependency` warnings | — |

---

## 5. AI agent stack `platform_*` packages

| Module | Purpose | Owner | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|---|
| `platform_memory/` | "AI context engine for all agents" | @macbook | `MemoryService`, `ContextAssembler`, `context_assembler.py`, `summarizer.py` | — | Active | **Second, unrelated memory stack exists at `platform_ai/memory/`** — no shared code between them | Consolidate or clearly document why two memory stacks coexist |
| `platform_ai/` | Provider-agnostic AI abstraction (largest service subtree — see `DEPENDENCY_MAP.md` §3.2) | @macbook | `ai_service`, `ai_router.py`, `skills_router.py`, `memory_router.py`, `workflows_router.py` | `platform_management.*`, `platform_api.versioning`, `platform_identity.identity_service` (all as reverse deps on its router files) | Active, densest internal package | Contains its own memory (`platform_ai/memory/`) and workflow (`platform_ai/workflows/`) subsystems, parallel to `platform_memory`/`platform_workflows` | See §3.2 of `DEPENDENCY_MAP.md` |
| `platform_orchestrator/` | Central execution layer for all AI agents | @macbook | `AgentRegistry`, `CapabilityRouter`, `AgentMessageBus`, `OrchestratorMetrics` | — | Active — used by the real bot backend | Near-identical exports to `platform_agents` (`BaseAgent`, `BUILTIN_AGENTS`, `register_builtin_agents`) | Clarify division of responsibility vs. `platform_agents` |
| `platform_agents/` | Plugin-based AI agent registry | @macbook | `BaseAgent`, `BUILTIN_AGENTS`, `register_builtin_agents` | — | Active | Near-duplicate of `platform_orchestrator`'s exports | Same as above |
| `platform_workflow/` | Task engine with agent/human assignment | @macbook | `AgentAssignmentService`, `HumanAssignmentService` | — | Active | One of 4+ "workflow"-named packages (see `TECH_DEBT.md`) | — |
| `platform_workflows/` | "Unified Workflow Engine — single runtime for all business flows" | @macbook | `WorkflowContext`, `WorkflowDefinition`, `register_service`, `workflow_engine.py` | `services.*`, `events.*`, `repositories.workflow_execution_repository`, `database.session`, `platform_ai.skills.skill_manager`, `platform_legacy` (via `adapters/legacy_rules.py`) | Active — the one Python workflow engine with real execution/scheduling code | Confusing naming overlap with `platform_workflow` (singular) and `platform_workflow_intelligence` | Rename one of the three, or document the split explicitly |
| `platform_workflow_intelligence/` | Sprint 24.1 — "unifies Workflow Engine, AI Orchestrator/Council, Advisor, Marketing, Commerce, Comms" | @macbook | `WorkflowIntelligenceLibrary` | — | Additive | Third workflow-named package | — |
| `platform_tools/` | Universal tool & integration framework | @macbook | `AgentToolBridge`, `ToolAuditLog` | — | Active | — | — |
| `platform_reasoning/` | AI reasoning/confidence engine | @macbook | `ConfidenceEstimator`, `ReasoningEngineConfig` | — | Active | — | — |
| `platform_planning/` | Goal-oriented execution planning | @macbook | `PlanningEngineConfig`, `ExecutionPlan`, `PlanningResult` | — | Active | — | — |
| `platform_decision/` | Adaptive execution strategy selection | @macbook | `DecisionEngine` + decision event classes | — | Active | — | — |
| `platform_learning/` | Continuous improvement from feedback | @macbook | `ExperienceStore`, `FeedbackCollector` | — | Active | — | — |
| `platform_collaboration/` | Multi-agent coordination & consensus | @macbook | `CollaborationEngine` + collaboration event classes | — | Active | — | — |

---

## 6. Vertical/sprint-flavored `platform_*` packages (single-facade libraries)

All of the following follow the same shape: one `*Library` facade class, a sprint number in the
docstring, and (for most) no dependents outside their own vertical. Catalogued together for brevity —
each still gets its own entry in `.github/CODEOWNERS`'s `/platform_*/` pattern (owner: `@macbook`).

| Module | Purpose | Status | Notes |
|---|---|---|---|
| `platform_ai_business_advisor/` | Sprint 22.1 — `AIBusinessAdvisorLibrary` | Additive | — |
| `platform_ai_marketing_os/` | Sprint 22.5 (Beauty edition) — `AIMarketingOSLibrary` | Additive | — |
| `platform_ai_os/` | Sprint 27.1 multi-agent OS — `MultiAgentOSLibrary` | Active | Shares `/api/ai-os/v1` prefix with `applications/ai_os` and hub MAOS — see `TECH_DEBT.md` |
| `platform_beauty_client_journey/` | Sprint 22.2 — booking/journey | Additive | Beauty vertical |
| `platform_beauty_os/` | Sprint 22.3 — Beauty OS | Additive | Beauty vertical |
| `platform_beauty_workspace/` | Sprint 22.4 — Beauty workspace | Additive | Beauty vertical |
| `platform_cafe_os/` | Sprint 31.0 — `CafeOSLibrary` | Additive | Cafe vertical |
| `platform_client_portal/` | Sprint 22.8 — `ClientPortalLibrary` | Additive | — |
| `platform_communications_hub/` | Sprint 22.6 — universal messaging gateway | Additive | — |
| `platform_contracts/` | Sprint 21.3 — DTO normalization | Additive | — |
| `platform_predictive_intelligence/` | Sprint 24.3 — forecasting | Additive | Docstring: "Distinct from Product Intelligence (EPI)" |
| `platform_product_intelligence/` | Sprint 22.0 — `ProductIntelligenceLibrary` | Additive | — |
| `platform_vertical_federation/` | Vertical federation | Additive | — |
| `platform_organization_brain/` | Organization brain | Additive | Backs `src/web/organization-brain/` |
| `platform_certification/` | (listed above, §3) | | |

---

## 7. `platform_enterprise_*` layer (30 packages, Sprint 23–27)

A deliberately additive "Enterprise" layer running alongside older siblings, per repo policy
(`docs/ARCHITECTURE_AUDIT_INDEX.md`: "No new Business Ecosystems after Sprint 31.4"). Owner: `@macbook`
for all (CODEOWNERS `/platform_*/`). Status: **Additive/Parallel** for all 30. Listed together —
individual purposes are one-line `*Library` facades; several explicitly document their non-duplication
intent in their own docstrings (noted where found):

`_ai_orchestrator`, `_ai_provider_hub`, `_autonomous_optimization`, `_certification`, `_command_center`,
`_commerce`, `_design_system`, `_digital_twin` ("Distinct from legacy Digital Twin (EDT)"),
`_extension_sdk`, `_identity_center`, `_knowledge_graph` ("Additive to legacy KG/EKP"),
`_learning_engine`, `_navigation`, `_onboarding`, `_operations`, `_performance_testing` ("Legacy EPF
platform_performance remains unchanged"), `_pilot_readiness`, `_production`, `_release_candidate`,
`_security_verification` ("Legacy ESH platform_security remains unchanged"), `_simulation_lab`
("Distinct from legacy Simulation Engine ESI"), `_strategy_intelligence`, `_web`, `_workspace`.

**Future plans (all 30):** no new packages in this family per current policy; existing ones continue
sprint-by-sprint additive development. Revisit consolidation only as a deliberate, documented decision
(see `TECH_DEBT.md` — several are flagged as naming-duplication debt that the repo's own audit says
not to merge casually).

---

## 8. Applications (`applications/`, 17 verticals)

Owner: `@macbook` (CODEOWNERS `/applications/`).

| Module | Purpose | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|
| `auto_marketplace/` (420 files) | Auto Marketplace Enterprise Platform | `applications/auto_marketplace/api/register.py` → mounted prefix in `api/server.py` | Platform Core, `services/`, `repositories/` | Production (GA) | Largest app; no dedicated test directory of its own | — |
| `enterprise_hub/` (866 files) | Enterprise Integration Hub | own `api/register.py` | Platform Core | Active | Internally re-implements many `platform_enterprise_*` concepts locally (ai_orchestrator, digital_twin, knowledge_graph, learning_engine, simulation_lab, strategy_intelligence, workflow_intelligence, organization_brain, vertical_federation, chaos_engineering, security_hardening) — see `TECH_DEBT.md` | Reconcile hub-local modules against `platform_enterprise_*` |
| `port_erp/` (209 files) | Port ERP (berths, cranes, vessels, yard) | `api_prefix: /api/port/v1` | Platform Core | Active | — | — |
| `agro_marketplace/` (185 files) | Agro Marketplace | manifest: `application_status: Production Ready` | Platform Core | Production (per manifest) | No test directory found | — |
| `drone_platform/` (161 files) | Drone Platform (mavlink, swarm, gcs, firmware) | own `api/register.py` | Platform Core | Active | 1 test file found | — |
| `platform_builder/` (113 files) | No-code builder product | `api_prefix: /api/platform-builder/v1` | Platform Core | Active | 4 structurally near-identical dirs: `command_center/`, `control_center/`, `mission_control/`, `operations_center/` — see `TECH_DEBT.md` | Targeted review of the 4-way split |
| `legal_enterprise/` (93 files) | Legal Intelligence Platform | own `api/register.py` | Platform Core | Active | — | — |
| `finance_enterprise/` (91 files) | Finance Enterprise Platform (Bidex) | own `api/register.py` | Platform Core | Active | Has its own `FinancialEventBus` (duplicate EventBus, see `TECH_DEBT.md`) | — |
| `crypto_enterprise/` (64 files) | Crypto Intelligence Platform | own `api/register.py` | Platform Core | Active | — | — |
| `agro_enterprise/` (59 files) | Agro Enterprise Platform | own `api/register.py` | Platform Core | Active | No tests found | — |
| `port_enterprise/` (57 files) | Port Enterprise Platform | own `api/register.py` | Platform Core | Active | — | — |
| `ai_os/` (16 files) | AI Operating System | `/api/ai-os/v1` (shared with `platform_ai_os` + hub MAOS) | Platform Core | Scaffold/Stub | Shared, unversioned-in-practice prefix collision | Disambiguate the shared `/api/ai-os/v1` prefix |
| `ecosystem/` (20 files) | "Unified AI Ecosystem" | own `api/register.py` | Platform Core | Scaffold/Stub | Third "ecosystem"-named thing in the repo (root `ecosystem/`, this, `enterprise_hub`) | — |
| `enterprise/` (17 files) | "AI Ecosystem Enterprise Edition" | own `api/register.py` | Platform Core | Scaffold/Stub | — | — |
| `executive_center/` (14 files) | Executive Command Center | own `api/register.py` | Platform Core | Scaffold/Stub | `dashboard.py`, `monitoring.py`, `twins.py` only | — |
| `marketplace/` (17 files) | AI Marketplace | own `api/register.py` | Platform Core | Scaffold/Stub | — | — |
| `workflow_studio/` (14 files) | Workflow Studio | own `api/register.py` | Platform Core | Scaffold/Stub | `editor.py`, `engine.py`, `ai_builder.py` only | — |

---

## 9. TS "ADOS OS" kernel ecosystem (`src/kernel` + 6 packages)

Owner: **Unassigned** (not covered by `.github/CODEOWNERS` — the `/platform_*/` and `/applications/`
patterns don't match `src/`).

| Module | Purpose | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|
| `src/kernel` (`@ados/kernel` v1.4.0) | Runtime kernel — boot sequence, service registry, health, RuntimeServer | `Kernel`, `BootLoader`, `ServiceRegistry`, `HealthMonitor`, `Lifecycle`, `RuntimeServer` (HTTP+WS on `:3000`) | all 6 sibling `@ados/*` packages | Active, but **Disconnected** from the Python backend | Two internal event-bus implementations coexist (`event_bus/` and `events/EventBus.ts`) | Decide the kernel's relationship to `platform_orchestrator` (see `ARCHITECTURE_MAP.md` §16 item 5) |
| `src/orchestrator` (`@ados/orchestrator` v3.0.0) | `AiOrchestrator`, agent routing, collaboration engine | `AiOrchestrator`, `BaseAgent`, `AgentRegistry`, `OrchestratorService`, `CollaborationEngine` | none (base layer) | Active, Disconnected from Python | Parallel to Python's `platform_orchestrator` with no shared code | — |
| `src/providers` (`@ados/providers` v2.2.0) | Mock provider gateway (Cursor/OpenAI/Claude/GitHub) | `ProviderGateway`, `ProviderRegistry`, `BaseProvider` | none (base layer) | Active, Disconnected, **mock only** — "no real API keys" | — | Wire real provider credentials if this ecosystem becomes production |
| `src/chat_bridge` (`@ados/chat-bridge` v4.0.0) | Middleware between ChatGPT and Cursor | `ChatBridge`, `ChatBridgeService`, `CommandQueue`, `SessionManager` | `@ados/orchestrator`, `@ados/providers` | Active, Disconnected | — | — |
| `src/voice` (`@ados/voice` v4.1.0) | Speech → intent → ChatGPT Bridge pipeline | `SpeechPipeline`, `VoiceService`, `CommandInterpreter` | `@ados/chat-bridge`, `@ados/orchestrator`, `@ados/providers` | Active, Disconnected, **no real mic/audio I/O** | — | — |
| `src/mcp` (`@ados/mcp` v4.2.0) | MCP gateway — JSON-RPC tools/resources/prompts over Runtime API | `MCPServer`, `MCPGateway`, `MCPToolRegistry` | none declared; wired at runtime via `RuntimeInvoker` callback from `src/kernel` | Active, Disconnected — reachable only via `npm run ados` | Not referenced by Python, `src/web`, or `platform_console` | — |
| `src/execution` (`@ados/execution` v4.3.0) | ChatGPT specs → agent work packages | execution planner classes | `@ados/orchestrator` | Active, Disconnected | — | — |

---

## 10. Frontends

| Module | Purpose | Owner | Public API | Dependencies | Status | Tech debt | Future plans |
|---|---|---|---|---|---|---|---|
| `src/web/` (v9.5.0) | Enterprise Web Platform — primary UI for the Python backend | Unassigned (not covered by CODEOWNERS) | routed pages under `/`, `/workspace`, `/platform-builder`, `/identity`, etc. (see `API_MAP.md`) | Python `api/server.py` (`/api`, `/management`) via HTTP | Production — the Enterprise Dashboard's home | TanStack Query installed but unused (0 `useQuery` calls); no `.test.tsx` render tests; 2 dead doc links in its own README | Adopt TanStack Query or remove it; add component render tests |
| `platform_console/` (v2.0.0) | Enterprise Control Center — UI for the TS kernel ecosystem | Unassigned (not covered by CODEOWNERS; wired into root `package.json` scripts, but that's a build script, not an ownership signal) | routed pages under `/kernel`, `/services`, `/workflows`, `/agents`, `/chat-bridge`, `/voice`, `/mcp`, `/execution`, etc. (see `API_MAP.md`) | Python `/management/*` (HTTP) + TS kernel `RuntimeServer` (`:3000`, HTTP+WS) | Active | 10 built page components never routed; `ProtectedRoute`/`AdminShell` defined but unused — no route currently enforces auth | Wire or delete the unrouted pages; enforce auth on the live route tree |

---

## 11. Root supporting packages (not deeply profiled elsewhere)

These exist and are referenced in `ARCHITECTURE_MAP.md`'s tree but weren't individually catalogued
above; listed here so the catalog is complete at the top level. **Update this section as these are
inspected in depth** — treat entries here as placeholders pending a fuller pass, not settled facts.

| Module | Purpose (best available signal) | Owner | Status |
|---|---|---|---|
| `knowledge/` | Large docs/knowledge tree (120 subdirs) | @macbook (CODEOWNERS `/knowledge/`) | Active |
| `ecosystem/` (root) | Root-level "ecosystem" concept, distinct from `applications/ecosystem/` | @macbook (CODEOWNERS `/ecosystem/`) | Active — needs disambiguation, see `TECH_DEBT.md` |
| `workflow/`, `workers/`, `storage/`, `models/`, `states/`, `audit/`, `connectors/`, `lib/` | Supporting root packages (not individually profiled in this pass) | Unassigned | Unverified — needs a dedicated catalog pass |
| `tests/` | pytest suite (342 files/dirs) | Unassigned | Active |
| `scripts/` | Architecture/legacy/certification validation scripts | Unassigned | Active — these are what regenerate `ARCHITECTURE_MAP.md`/`DEPENDENCY_MAP.md`'s numbers |

---

## Related documents

- `ARCHITECTURE_MAP.md` — narrative architecture overview.
- `DEPENDENCY_MAP.md` — dependency graph detail behind the "Dependencies" column above.
- `API_MAP.md` — full endpoint inventory behind each module's "Public API" column.
- `TECH_DEBT.md` — full detail behind every "Tech debt" column entry, with priority/effort estimates.
