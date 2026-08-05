# Enterprise Overnight Audit — Top 100 Recommendations

The 20 highest-severity items are in `docs/TOP_20_CRITICAL_FIXES.md` and are not repeated here. This
document is the broader sweep — every recommendation carries why/impact/risk/complexity/priority in
condensed form. Grouped by category. Sourced from `docs/TECH_DEBT.md` (TD-01–TD-58) and the SPEC
recommendations made across this engagement's twenty prior sprints (CG-4 through CQ-20).

## A. Architecture debt (21–40)

| # | Recommendation | Why | Risk | Complexity | Priority |
|---|---|---|---|---|---|
| 21 | Publish an alias map for the three "ecosystem" layers (`TD-01`) | Naming collision, real risk of accidental reimplementation | Low | S | P2 |
| 22 | Clarify Mission Control / Executive Center / drone Mission scopes in docs (`TD-02`) | Same pattern as #21 | Low | S | P2 |
| 23 | Add navigation-label disambiguation for the three visible Command Centers (`TD-03`) | User-facing confusion, not just dev confusion | Medium | S | P2 |
| 24 | Publish a Digital Twin namespace glossary (`TD-04`) | Five real systems share the name | Low | S | P2 |
| 25 | Publish an alias map for `recommendation_engine`'s 6+ locations (`TD-05`) | Same collision pattern | Low | S | P3 |
| 26 | Document a deprecation schedule for unversioned legacy CRM `/api/*` (`TD-06`) | Sits beside the frozen `/api/v1` | Low | M | P2 |
| 27 | Document subpath ownership for shared `/api/ai-os/v1` (`TD-07`) | Three packages answer one prefix | Low | S | P2 |
| 28 | Fix `database/__init__.py`'s import of `database_legacy` (`TD-19`) | Modern package depends on the layer it should be isolated from | Medium | M | P1 |
| 29 | Reconcile the 29 `reverse_layer_dependency` warnings (`TD-24`) | Governance gate tolerates real violations | Medium | L | P1 |
| 30 | Re-verify TD-36's "47 legacy pg-engine cycles" against current `validate_architecture.py` output | Possible contradiction with a 0-cycles report elsewhere | Low | S | P2 |
| 31 | Resolve the `WorkflowEngine` name-collision alias properly, not just via adapter (`TD-37`) | Cosmetic fix masking a real naming issue | Low | M | P2 |
| 32 | Re-verify the 4-file handler DB-access allowlist against current rules (`TD-38`) | Stale reference in the registry itself | Low | S | P3 |
| 33 | Route legacy `pg_*` engines' `crm_event_bus` imports through the canonical bus (`TD-39`) | Bypasses the intended integration point | Medium | M | P1 |
| 34 | Decide `container.py`'s fate: wire in or retire (`TD-18`) | Zero production consumers today | Low | S/L | P2 |
| 35 | Confirm root `memory.db` is unused, then delete (`TD-30`) | Leftover SQLite artifact under a Postgres-only policy | Low | S | P3 |
| 36 | Confirm the example vertical plugins are intentionally unloaded, or wire them in (`TD-29`) | Dead-looking code with an unclear intent | Low | M | P3 |
| 37 | Extend `?embed=1` chrome handling beyond `WorkspaceLayout`/`SettingsPage` (`TD-44`) | Visible double-chrome defect, self-admitted in its own doc | Low | M | P2 |
| 38 | Decide the canonical route among Enterprise City's three aliases (`TD-43`) | One is already labeled "legacy... optional" by its own doc | Low | S | P3 |
| 39 | Generalize the tab-bar drag/reorder/context-menu patterns into shared primitives (`TD-42`) | Only one surface has these; every other list/grid lacks them | Low | L | P3 |
| 40 | Fill the 8 frame-only Platform Builder builders via the Universal Builder Framework, not forks (`TD-10`) | Navigation destinations with no real content | Low | L | P3 |

## B. Security (41–48)

| # | Recommendation | Why | Risk | Complexity | Priority |
|---|---|---|---|---|---|
| 41 | Trace `PlatformSettings.jwt_secret` consumers (see Top 20 #2) | — | — | — | P0 (listed here for completeness) |
| 42 | Re-verify Enterprise City frontend permission gating is still absent or has since closed | Last confirmed absent in Sprint CG-6, not re-checked this pass | Medium | S (verify) | P1 |
| 43 | Confirm CORS configuration is intentionally scoped, not wide-open by default in prod | Not fully traced this pass | Low–Medium | S | P2 |
| 44 | Confirm `VITE_DEMO_AUTH` cannot be reachable in a production frontend build | Fallback auth exists by design; needs a build-time guard confirmed | Medium | S | P2 |
| 45 | Add a load-tested confirmation (or fix) for `TD-32`'s fan-out risk (`management_router`, `dashboard_service`) | Currently a hypothesis, not measured | Unknown | M | P2 |
| 46 | Audit `platform_security/`'s remaining `os.environ` direct reads beyond `TD-17`'s two files | Same violation class, possibly more instances | Low | S | P2 |
| 47 | Confirm secrets are never logged by any real logging/observability path | Not checked this pass | Unknown | S | P2 |
| 48 | Document the real scope of what `/management/v1`'s security test suite actually covers vs. assumes | The suite is real and CI-enforced; its exact coverage boundary wasn't read line-by-line this pass | Low | S | P3 |

## C. Scalability (49–56)

| # | Recommendation | Why | Risk | Complexity | Priority |
|---|---|---|---|---|---|
| 49 | Confirm which (if any) of the eleven frontend runtimes have unbounded in-memory growth and cap them | Only `lifeEventEngine` (400) and `businessInteractions` (200) confirmed capped this pass | Medium | M | P2 |
| 50 | Decide whether a real vector/search backend is needed for v1, and if so which | All "semantic search" today is fake-hash-backed | Medium | XL | P2 |
| 51 | Evaluate whether the seven workflow engines need a shared queue before any multi-process execution | Currently no real cross-process job infra | Medium | XL | P3 |
| 52 | Confirm `openrouter.py`'s error-handling/backpressure behavior under real load | Single point of failure for all real AI calls | Medium | M | P2 |
| 53 | Evaluate a Redis pub/sub adapter before activating dormant Socket.IO collaboration features | Would need it to scale past one process | Low today | M | P3 |
| 54 | Add eviction policy to `routingEngine`'s route cache | No confirmed cap found this pass | Low | S | P3 |
| 55 | Confirm whether any of the four Knowledge Graph systems persist to Postgres vs. in-memory | Not confirmed for all four this pass | Medium | S (verify) | P2 |
| 56 | Add a connection pooler (e.g. PgBouncer) ahead of any real production traffic growth | No pooler found in `docker-compose.prod.yml` | Medium | M | P2 |

## D. Documentation (57–64)

| # | Recommendation | Why | Risk | Complexity | Priority |
|---|---|---|---|---|---|
| 57 | Refresh `00_MASTER_PRODUCT_BIBLE.md`'s "TD-01 through TD-42" reference to include TD-47–TD-58 | Natural drift, cheap fix | Low | S | P3 |
| 58 | Add a one-line pointer from `00_MASTER_PRODUCT_BIBLE.md` to `FINAL_AUDIT_RESULT.md` | Keeps the audit trail discoverable from the real entry point | Low | S | P3 |
| 59 | Fix the two dead links in `src/web/README.md` (`TD-34`) | Confirmed broken | Low | S | P3 |
| 60 | Add CODEOWNERS coverage for root infra directories (`TD-35`) | Currently uncovered | Low | S | P3 |
| 61 | Do a full (not sampled) broken-link sweep across all 1,190 docs before any doc-corpus reorganization | This audit only sampled 7 files | Low | L | P3 |
| 62 | Standardize the "X Ready · Y Ready" doc-footer convention to distinguish foundation-readiness from production-readiness | Real ambiguity found in multiple docs | Low | M | P2 |
| 63 | Publish uneven OpenAPI coverage as a tracked gap per vertical (`TD-13`) | Already flagged twice (original report + master bible) | Low | L | P2 |
| 64 | Add a "last verified" date convention check across the four-document set each sprint | Currently manual | Low | S | P3 |

## E. Code organization (65–70)

| # | Recommendation | Why | Risk | Complexity | Priority |
|---|---|---|---|---|---|
| 65 | Add disambiguating docstrings to `applications/port_enterprise/__init__.py` and `port_erp/__init__.py` | Shared prefix, different scale/purpose | Low | S | P2 |
| 66 | Audit `services/` naming conventions (`pg_*` vs `*_engine` vs `*_service`) for a documented rule | Inconsistency found, not yet a documented standard | Low | M | P3 |
| 67 | Consider (not execute) a future namespace grouping for the 30 `platform_enterprise_*` packages | Root-level sprawl, out of scope to act on now | Low | XL (future) | P3 |
| 68 | Confirm `src/verticals`/`src/platform`/`src/events` share `src/domains`'s orphaned status or not | Only `src/domains` was directly measured this pass | Low | S (verify) | P2 |
| 69 | Add a repo-root `find`-based sanity check to CI that flags new top-level directories for review | Prevents further undocumented sprawl | Low | S | P3 |
| 70 | Document the intentional three-system split (Python backend / `src/web` / TS kernel) in `ARCHITECTURE_MAP.md`'s own words, not just inferred from `CLAUDE.md` | Closes `TD-33`'s documentation gap directly | Low | S | P1 |

## F. Product/feature gaps from the CQ-10–CQ-20 engagement (71–95)

| # | Recommendation | Source | Priority |
|---|---|---|---|
| 71 | Add `technology_park`/`port`/`special_economic_zone` as additive `SpatialDistrictKind` values | `docs/REGIONAL_DIGITAL_TWIN.md` §1 | P3 |
| 72 | Implement `TerritoryProfile` generalization of `seedOdessaSpatial()` | `docs/REGIONAL_DIGITAL_TWIN.md` §2 | P2 |
| 73 | Insert territorial governance scope tiers into `spatialPermissions` rank | `docs/TERRITORIAL_GOVERNANCE.md` §3 | P3 |
| 74 | Add `Branch.spatial_city_entity_id` to bind real branches to real Spatial Runtime cities | `docs/REGIONAL_ECONOMY.md` §1 | P3 |
| 75 | Add `"maintenance"`/`"inspection"` to `CALENDAR_EVENT_TYPES` | `docs/BUSINESS_CALENDAR.md` §2 | P3 |
| 76 | Design cross-org `visibility: "partner_shared"` calendar value | `docs/BUSINESS_CALENDAR.md` §3 | P3 |
| 77 | Compose (not replace) the three notification vocabularies with a business-category tag | `docs/OPERATIONAL_NOTIFICATIONS.md` §3 | P2 |
| 78 | Add `DashboardScope` filtering over real domain dashboards for Manager/Dept Head/PM/Regional roles | `docs/OPERATIONAL_DASHBOARDS.md` §2 | P3 |
| 79 | Bridge `assetRuntime.move()` and `Membership.role` changes into the Life Engine event stream | `docs/DAILY_OPERATIONS_MODEL.md` §3 | P1 |
| 80 | Enforce the real Visibility/permission composition at cross-org project/meeting membership time | `docs/CROSS_ORG_DAILY_COOPERATION.md` §2 | P1 |
| 81 | Generalize `Supplier`/`Contractor`/`Subcontractor` beyond automotive | `docs/SUPPLY_CHAIN.md` §2 | P2 |
| 82 | Add `ProjectQualityCheck`/`CorrectiveAction` (generalizes real `DealStageHistory`) | `docs/QUALITY_ASSURANCE_ARCHITECTURE.md` §3 | P2 |
| 83 | Add `ResourceAllocation` over the nine real resource registries | `docs/RESOURCE_ORCHESTRATION.md` §2 | P2 |
| 84 | Add `CustomerFeedback` (plain rating, no NPS/CSAT methodology yet) | `docs/CUSTOMER_JOURNEY.md` §2 | P2 |
| 85 | Build `BusinessValueSnapshot` composite (reuses `ENTERPRISE_HEALTH.md`'s read-only pattern) | `docs/BUSINESS_VALUE_METRICS.md` §2 | P3 |
| 86 | Publish `CanonicalStageMapping`/`SemanticAlias` lookup tables (Phase 0 of the CQ-19/20 migration strategy) | `docs/SPRINT_CQ_19_RESULT.md` §7, `docs/SEMANTIC_VERSIONING.md` | P1 |
| 87 | Add `process_created`/`stage_changed` `LifeEventKind` values | `docs/PROCESS_EVENT_MODEL.md` §2 | P3 |
| 88 | Bridge the Approval Center and `ServiceOrder` into the Life Engine event stream | `docs/PROCESS_EVENT_MODEL.md` §1 | P2 |
| 89 | Add missing `ENTITY_TYPES` values for Spatial/Life-Engine/Role concepts (additive only) | `docs/ENTERPRISE_ONTOLOGY.md` | P3 |
| 90 | Decide the "Blocked vs Waiting" state modeling explicitly if a future sprint wants it distinct | `docs/PROCESS_STATE_MACHINE.md` §4 | P3 |
| 91 | Reconcile `tasks.Task`/`DealTask`/`ProjectParticipant.assignments` deliberately | `docs/ENTITY_RECONCILIATION.md` §2 | P1 |
| 92 | Add territory-scoped event payload field (`territoryId`) ahead of multi-city rollout | `docs/DIGITAL_TWIN_STANDARDS.md` §4 | P2 |
| 93 | Decide whether to generalize the real CPL Loyalty/Membership Center beyond cafe/beauty | `docs/CUSTOMER_JOURNEY.md` §3 | P3 |
| 94 | Add `Company Card` real-map skin work only after confirming product wants the "Digital Odessa" narrative direction | `docs/CITY_LIVING_ECONOMY.md` §2 | P3 |
| 95 | Confirm the one-directional favorites bridge bug (`cityNavigation.ts` → `favoritesManager`) is now bidirectional or still isn't | `docs/CITY_NAVIGATION_GUIDE.md` (CG-5) | P2 |

## G. City / visualization (96–100)

| # | Recommendation | Why | Priority |
|---|---|---|---|
| 96 | Treat `cityVisualizationRuntime.ts` with elevated review care given its 8-runtime fan-in | New finding this audit, real wide blast radius | P2 |
| 97 | Confirm no second cross-runtime aggregator is introduced alongside `cityVisualization` | Prevents an eighth/ninth integration point from emerging | P2 |
| 98 | Extend `SMART_INFRASTRUCTURE.md`'s still-thin Utilities/Airports/Telecom/Energy categories only when a real product need exists | Avoid fabricating placeholder models | P3 |
| 99 | Re-verify the LOD/performance-budget discipline in the real Graphics Engine still holds after any new City feature work | Confirmed real and good; worth protecting as new features accrete | P2 |
| 100 | Confirm City's `?embed=1` iframe boundary is documented wherever a future multi-window collaboration feature is designed | Real cross-window state-sharing constraint, easy to forget | P2 |

## Related documents

`docs/TOP_20_CRITICAL_FIXES.md`, `docs/TECH_DEBT.md`, `docs/ARCHITECTURE_IMPROVEMENTS.md`,
`docs/ENTERPRISE_V1_READINESS.md`.
