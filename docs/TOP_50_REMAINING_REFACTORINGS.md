# Sprint CQ-30 — Top 50 Remaining Refactorings

Re-prioritized against `docs/TOP_20_CRITICAL_FIXES.md`/`docs/TOP_100_RECOMMENDATIONS.md`: resolved
items (`TD-17`) are dropped, partially-resolved items are re-scoped to their remaining gap, and new
items found this sprint are inserted at their evidence-based priority. Documentation only.

## Tier 1 — P0/P1, act first (1–15)

| # | Item | Source | Priority | Cost |
|---|---|---|---|---|
| 1 | Flip `startup.py:54` to `fail_fast=True` (or `is_production`) for JWT-secret validation | `docs/ARCHITECTURE_CONSISTENCY.md` Issue 1 (new, precise) | P0 | S |
| 2 | Build the AI Production Center consent-record gate before any avatar/voice provider work | `TD-46` | P0 | M |
| 3 | Extend Platform Builder header-only auth with live identity — confirmed still fully unverified this sprint | `TD-08`, re-confirmed | P0 | L |
| 4 | Add `Project` table + `Deal.project_id` FK — confirmed still absent | `TD-51`, re-confirmed | P1 | M |
| 5 | Bundle `tasks.Task.project_id` → real FK conversion with #4 | `docs/ENTITY_CONSISTENCY.md` Issue 3 | P1 | S |
| 6 | Confirm `src/domains`'s 141 files are unused, then document-or-delete — confirmed still zero real usage | `TD-55`, re-confirmed | P1 | S |
| 7 | Document the Orchestrator/Kernel/CityVisualization three-layer relationship — new finding | `docs/RUNTIME_CONSISTENCY.md` Issue 1 | P1 | S |
| 8 | Disambiguate frontend "Kernel"/"Orchestrator" from the TS `@ados/kernel`/`@ados/orchestrator` ecosystem in docs | `docs/RUNTIME_CONSISTENCY.md` Issue 2 (new) | P1 | S |
| 9 | Add the four Knowledge Graph + Digital Twin API prefixes to `API_MAP.md` | `docs/API_CONSISTENCY.md` Issue 1 (new) | P1 | S |
| 10 | Verify tenant-filter completeness across `repositories/` | `TD-58`, not re-verified this sprint | P1 | M |
| 11 | Trace whether frontend `workflowRuntime` should call backend workflow engines | `TD-48` | P1 | M |
| 12 | Decide whether `orchestrator` should be the single source of runtime health truth vs. `cityVisualization` deriving its own | `docs/DOMAIN_BOUNDARIES.md` Issue 1 (new) | P1 | S/M |
| 13 | Write down the `src/kernel`/`src/orchestrator` TS-ecosystem-to-Python-backend relationship decision | `TD-33` | P1 | S |
| 14 | Publish `CanonicalStageMapping` lookup tables for the six deal systems | `TD-47`, Phase 0 still not implemented | P2 | S |
| 15 | Unify or document why the three permission-scope vocabularies must stay separate | `TD-52` | P1 | L |

## Tier 2 — P2, next (16–35)

| # | Item | Source | Cost |
|---|---|---|---|
| 16 | Close `TD-17` in `TECH_DEBT.md` as `RESOLVED — Sprint CQ-30` | `docs/ARCHITECTURE_CONSISTENCY.md` Issue 2 | S |
| 17 | Confirm `alembic.ini`'s authoritative migrations directory | `TD-31` | S |
| 18 | Wire or remove `platform_console`'s unrouted pages / unused `ProtectedRoute` | `TD-28` | S |
| 19 | Retire the orphaned frontend Command Palette copy | `TD-40` | M |
| 20 | Unify duplicated favorites/recent-history managers, add real persistence | `TD-41` | M |
| 21 | Route legacy `pg_*` engines' `crm_event_bus` imports through the canonical bus | `TD-39` | M |
| 22 | Reconcile the 29 `reverse_layer_dependency` warnings | `TD-24` | L |
| 23 | Fix `database/__init__.py`'s import of `database_legacy` | `TD-19` | M |
| 24 | Add index/partition review for `DealStageHistory`-shaped tables ahead of real volume | `docs/SCALABILITY_REVIEW.md` | M |
| 25 | Add a connection pooler ahead of production traffic growth | `docs/SCALABILITY_REVIEW.md` | M |
| 26 | Confirm which of the four Knowledge Graph systems persist to Postgres vs. in-memory | `docs/SCALABILITY_REVIEW.md` | S (verify) |
| 27 | Add a one-line caveat to `ENTERPRISE_ONTOLOGY.md` for entity types without real backing tables | `docs/ENTITY_CONSISTENCY.md` Issue 4 | S |
| 28 | Consolidate `platform_builder`'s four near-identical center directories | `TD-27` | M |
| 29 | Disambiguate `port_enterprise`/`port_erp` package docstrings | `docs/ENTERPRISE_FULL_AUDIT.md` §6.2 | S |
| 30 | Add a repo-root `find`-based CI check flagging new top-level directories | `docs/TOP_100_RECOMMENDATIONS.md` #69 | S |
| 31 | Confirm `src/verticals`/`src/platform`/`src/events` share `src/domains`'s orphaned status or not | `docs/TOP_100_RECOMMENDATIONS.md` #68 | S (verify) |
| 32 | Extend `?embed=1` chrome handling beyond `WorkspaceLayout`/`SettingsPage` | `TD-44` | M |
| 33 | Bridge `assetRuntime.move()` and `Membership.role` changes into the Life Engine event stream | `docs/DAILY_OPERATIONS_MODEL.md` §3 | M |
| 34 | Enforce real Visibility/permission composition at cross-org project/meeting membership time | `docs/CROSS_ORG_DAILY_COOPERATION.md` §2 | M |
| 35 | Add `ProjectQualityCheck`/`CorrectiveAction` | `docs/QUALITY_ASSURANCE_ARCHITECTURE.md` §3 | M |

## Tier 3 — P3, defer (36–50)

| # | Item | Source | Cost |
|---|---|---|---|
| 36 | Publish alias maps for the three "ecosystem" layers | `TD-01` | S |
| 37 | Clarify Mission Control / Executive Center / drone Mission scopes | `TD-02` | S |
| 38 | Publish an alias map for `recommendation_engine`'s 6+ locations | `TD-05` | S |
| 39 | Decide the canonical Enterprise City route among its three aliases | `TD-43` | S |
| 40 | Fill the 8 frame-only Platform Builder builders via UBF | `TD-10` | L |
| 41 | Fix the two dead links in `src/web/README.md` | `TD-34` | S |
| 42 | Add CODEOWNERS coverage for root infra directories | `TD-35` | S |
| 43 | Standardize the "X Ready" doc-footer convention (foundation vs. production readiness) | `docs/TOP_100_RECOMMENDATIONS.md` #62 | M |
| 44 | Add `ResourceAllocation` over the nine real resource registries | `docs/RESOURCE_ORCHESTRATION.md` §2 | M |
| 45 | Add `CustomerFeedback` (plain rating, no methodology) | `docs/CUSTOMER_JOURNEY.md` §2 | M |
| 46 | Generalize `Supplier`/`Contractor`/`Subcontractor` beyond automotive | `docs/SUPPLY_CHAIN.md` §2 | L |
| 47 | Add `technology_park`/`port`/`special_economic_zone` `SpatialDistrictKind` values | `docs/REGIONAL_DIGITAL_TWIN.md` §1 | S |
| 48 | Implement `TerritoryProfile` generalization of `seedOdessaSpatial()` | `docs/REGIONAL_DIGITAL_TWIN.md` §2 | M |
| 49 | Confirm no `Deleted` event suffix is introduced in any future event vocabulary | `docs/EVENT_VOCABULARY.md` §2 | S (policy) |
| 50 | Confirm City's `?embed=1` iframe boundary is documented for any future multi-window feature | `docs/TOP_100_RECOMMENDATIONS.md` #100 | S |

## Related documents

`docs/TECH_DEBT.md`, `docs/TOP_20_CRITICAL_FIXES.md`, `docs/TOP_100_RECOMMENDATIONS.md`,
`docs/ARCHITECTURE_CONSISTENCY.md`, `docs/RUNTIME_CONSISTENCY.md`, `docs/API_CONSISTENCY.md`,
`docs/ENTITY_CONSISTENCY.md`, `docs/DOMAIN_BOUNDARIES.md` (all CQ-30 siblings/sources).
