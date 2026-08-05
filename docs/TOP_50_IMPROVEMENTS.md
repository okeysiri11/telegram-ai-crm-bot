# Sprint CQ-30.6 — Top 50 Improvements

**Relationship to `docs/TOP_50_REMAINING_REFACTORINGS.md` (CQ-30):** that list remains valid for items
not re-touched here. This document refreshes it against Sprint 30.0's real fixes (TD-17 resolved,
TD-57 hardened, TD-58 now has a real 79-item audit) and adds this review's new findings. Items already
shipped are marked done and removed from the ranking rather than left cluttering it.

## Tier 1 — act before Beta (1–15)

| # | Improvement | Source | Cost |
|---|---|---|---|
| 1 | Triage the 79 heuristic tenant-isolation findings | `docs/SECURITY_REVIEW.md` §8 (new, sharpened) | M |
| 2 | Add `Project` table + `Deal.project_id` FK | `TD-51` | M |
| 3 | Build the AI Production Center consent-record gate before any generation backend | `TD-46` | M |
| 4 | Document the Kernel/Orchestrator/CityVisualization three-layer relationship | `TD-59` | S |
| 5 | Add explicit "Kernel"/"Orchestrator" disambiguation notes wherever either pair appears | `TD-60` | S |
| 6 | Complete Platform Builder's token-only auth cutover for remaining vertical middlewares | `TD-08`, partially mitigated Sprint 30.0 | L |
| 7 | Confirm every backend Owner-scoped endpoint enforces server-side checks, not just UI hiding | `docs/SECURITY_REVIEW.md` §8 (new) | M (verify) |
| 8 | Add the four Knowledge Graph + Digital Twin prefixes to `API_MAP.md` | `TD-49` | S |
| 9 | Confirm `src/domains`'s 141 files are unused, then document-or-delete | `TD-55` | S |
| 10 | Decide keep-code-defined vs. make-runtime-registrable for `ENTITY_TYPES`/`RELATION_TYPES`, document it | `docs/ARCHITECTURE_REVIEW_V2.md` §6 (new) | S (document the decision this review already recommends: keep code-defined) |
| 11 | Verify Registration/Invitation flow reality before Beta launch | `docs/LOGIN_USER_FLOW.md` §3, CQ-30.1 | S (verify) |
| 12 | Bundle `tasks.Task.project_id` → real FK with #2 | `docs/ENTITY_CONSISTENCY.md` Issue 3 | S |
| 13 | State the Beta org-count target explicitly (10–100) in Beta-facing materials | `docs/SCALABILITY_REVIEW.md` §9 (new) | S |
| 14 | Add a real generation-status indicator to every Production Studio card | `docs/PRODUCTION_STUDIO_UX.md` §3, CQ-30.1 | M |
| 15 | Unify or explicitly justify keeping separate the three permission-scope vocabularies | `TD-52` | L |

## Tier 2 — next (16–35)

| # | Improvement | Source | Cost |
|---|---|---|---|
| 16 | Confirm `alembic.ini`'s authoritative migrations directory | `TD-31` | S |
| 17 | Standardize pagination `limit` defaults across `management_router.py` | `docs/API_REVIEW.md` §3 (new) | S |
| 18 | Add a shared filter-parsing utility (opportunistic, not urgent) | `docs/API_REVIEW.md` §4 (new) | M |
| 19 | Evaluate consolidating the three in-process task queues, or explicitly document why not | `docs/SCALABILITY_REVIEW.md` §10 (new) | L (evaluate) |
| 20 | Wire or remove `platform_console`'s unrouted pages / unused `ProtectedRoute` | `TD-28` | S |
| 21 | Retire the orphaned frontend Command Palette copy | `TD-40` | M |
| 22 | Unify duplicated favorites/recent-history managers, add real persistence | `TD-41` | M |
| 23 | Route legacy `pg_*` engines' `crm_event_bus` imports through the canonical bus | `TD-39` | M |
| 24 | Reconcile the 29 `reverse_layer_dependency` warnings | `TD-24` | L |
| 25 | Fix `database/__init__.py`'s import of `database_legacy` | `TD-19`, re-confirmed still open | M |
| 26 | Add index/partition review for `DealStageHistory`-shaped tables ahead of 1,000-org scale | `docs/SCALABILITY_REVIEW.md` §9 (new) | M |
| 27 | Add a connection pooler ahead of 1,000-org scale | `docs/SCALABILITY_REVIEW.md` §9 (new) | M |
| 28 | Confirm which Knowledge Graph systems persist to Postgres vs. in-memory | `docs/SCALABILITY_REVIEW.md` | S (verify) |
| 29 | Consolidate `platform_builder`'s four near-identical center directories | `TD-27` | M |
| 30 | Publish `CanonicalStageMapping` lookup tables for the six deal systems | `TD-47`, Phase 0 still not implemented | S |
| 31 | Bridge `assetRuntime.move()`/`Membership.role` changes into the Life Engine event stream | `docs/DAILY_OPERATIONS_MODEL.md` §3 | M |
| 32 | Enforce real Visibility/permission composition at cross-org membership time | `docs/CROSS_ORG_DAILY_COOPERATION.md` §2 | M |
| 33 | Add `ProjectQualityCheck`/`CorrectiveAction` | `docs/QUALITY_ASSURANCE_ARCHITECTURE.md` §3 | M |
| 34 | Add a one-line caveat to `ENTERPRISE_ONTOLOGY.md` for entity types without real backing tables | `docs/ENTITY_CONSISTENCY.md` Issue 4 | S |
| 35 | Scope Client/Dealer portal UX as its own follow-up sprint | `docs/ROLE_NAVIGATION.md` §3, CQ-30.1 | L (design) |

## Tier 3 — defer (36–50)

| # | Improvement | Source | Cost |
|---|---|---|---|
| 36 | Publish alias maps for the three "ecosystem" layers | `TD-01` | S |
| 37 | Clarify Mission Control / Executive Center / drone Mission scopes | `TD-02` | S |
| 38 | Publish an alias map for `recommendation_engine`'s 6+ locations | `TD-05` | S |
| 39 | Decide the canonical Enterprise City route among its three aliases | `TD-43` | S |
| 40 | Fill the 8 frame-only Platform Builder builders via UBF | `TD-10` | L |
| 41 | Fix the two dead links in `src/web/README.md` | `TD-34` | S |
| 42 | Add CODEOWNERS coverage for root infra directories | `TD-35` | S |
| 43 | Standardize the "X Ready" doc-footer convention | `docs/TOP_100_RECOMMENDATIONS.md` #62 | M |
| 44 | Add `ResourceAllocation` over the nine real resource registries | `docs/RESOURCE_ORCHESTRATION.md` §2 | M |
| 45 | Add `CustomerFeedback` (plain rating) | `docs/CUSTOMER_JOURNEY.md` §2 | M |
| 46 | Generalize `Supplier`/`Contractor`/`Subcontractor` beyond automotive | `docs/SUPPLY_CHAIN.md` §2 | L |
| 47 | Extend `?embed=1` chrome handling beyond `WorkspaceLayout`/`SettingsPage` | `TD-44` | M |
| 48 | Confirm `src/verticals`/`src/platform`/`src/events` share `src/domains`'s orphaned status or not | New, verify | S |
| 49 | Add a repo-root `find`-based CI check flagging new top-level directories | Prior recommendation | S |
| 50 | Evaluate a real GraphQL surface only if a specific enterprise integration requires it | `docs/API_REVIEW.md` §6 (new) | XL (deferred, not scheduled) |

## Items resolved since the last such list (removed from ranking, not repeated above)

- `TD-17` (`os.environ` bypass) — resolved, Sprint CQ-30 confirmed.
- `TD-57` (JWT dual-path) — hardened, single canonical `resolve_iam_signing_secret()` now in place.

## Related documents

`docs/TOP_50_REMAINING_REFACTORINGS.md` (CQ-30, the prior version this refreshes), `docs/TECH_DEBT_
V2.md` (this review's ranked-severity view), `docs/TECH_DEBT.md` (canonical registry).
