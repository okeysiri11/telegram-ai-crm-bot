# Sprint CQ-30.8 — Top 100 Beta Fixes

Structured per the brief's explicit ask: TOP 20 before Beta, TOP 50 improvements after Beta, TOP 100
long-term. Sourced from `docs/BETA_READINESS_REVIEW.md`'s ranked blockers plus this engagement's prior
`docs/TOP_50_IMPROVEMENTS.md`/`docs/TOP_100_UX_IMPROVEMENTS.md`/`docs/TOP_100_RECOMMENDATIONS.md`.
Documentation only.

## TOP 20 — before Beta

| # | Fix | Priority | Effort |
|---|---|---|---|
| 1 | Configure real TLS at the nginx layer (port 443 is open, unconfigured) | Critical | S-M |
| 2 | Verify/fix nginx's placeholder catch-all response | Critical | S |
| 3 | Remove Grafana's default admin password fallback | Critical | S |
| 4 | Add a basic prompt-injection/AI-abuse protection layer | Critical | M |
| 5 | Verify Registration/Invitation flow reality | Critical | S |
| 6 | Triage all 79 tenant-isolation findings | Critical | M |
| 7 | Fix Маркетинг→Маркетплейс in the 3 real label dictionaries | High | S |
| 8 | Add a Docker healthcheck to the `bot` service | High | S |
| 9 | Build a Dealer navigation surface (real data already exists) | High | M |
| 10 | Trace the two real rate limiters' relationship | High | S |
| 11 | Add `limit_req` rate limiting at the nginx/edge layer | High | S |
| 12 | Build the AI Production Center consent-gate before any voice/avatar generation work | High | M |
| 13 | Add a real-status indicator to Production Studio's sidebar entry and every studio card | High | M |
| 14 | Confirm every backend Owner-scoped endpoint enforces server-side checks | High | M (verify) |
| 15 | Document Owner Dashboard vs. God Mode's intended relationship | Medium | S |
| 16 | Scope Client portal design as its own explicit follow-up (not silently deferred) | High | S (decision) |
| 17 | Confirm/remove the second SQLite artifact in `backups/` | Medium | S |
| 18 | Add explicit Beta org-count scope (10–100) to launch materials | Medium | S |
| 19 | Sequence Beta's first cohort as internal-role-only, pending #9/#16 | Medium | S (decision) |
| 20 | Resync `docs/UI_NAVIGATION.md`'s sidebar count with the real 23-item catalog | Low | S |

## TOP 50 — improvements after Beta launches (21–70)

| # | Improvement | Source |
|---|---|---|
| 21 | Add log aggregation (Loki, pairs with real Grafana) | `docs/OBSERVABILITY_REVIEW.md` §3 |
| 22 | Extend real `request_id` correlation into structured logs platform-wide | `docs/PERFORMANCE_REVIEW.md` §1 |
| 23 | Audit error-response consistency across non-management domains | `docs/API_REVIEW.md` §8 |
| 24 | Add `Project` table + `Deal.project_id` FK | `TD-51` |
| 25 | Document the Kernel/Orchestrator/CityVisualization three-layer relationship | `TD-59` |
| 26 | Add explicit Kernel/Orchestrator disambiguation notes | `TD-60` |
| 27 | Run a real load test on `management_router`/`dashboard_service` fan-out | `TD-32` |
| 28 | Add the missing Knowledge Graph API prefixes to `API_MAP.md` | `TD-49` |
| 29 | Confirm `src/domains`'s 141 files are unused, then document-or-delete | `TD-55` |
| 30 | Standardize pagination `limit` defaults | `docs/API_REVIEW.md` §3 |
| 31 | Unify or explicitly justify keeping separate the three permission-scope vocabularies | `TD-52` |
| 32 | Complete Platform Builder's token-only auth cutover | `TD-08` |
| 33 | Retire the orphaned frontend Command Palette copy | `TD-40` |
| 34 | Unify duplicated favorites/recent-history managers, add real persistence | `TD-41` |
| 35 | Consolidate `platform_builder`'s four near-identical center directories | `TD-27` |
| 36 | Fix `database/__init__.py`'s import of `database_legacy` | `TD-19` |
| 37 | Add a connection pooler ahead of 1,000-org scale | `docs/SCALABILITY_REVIEW.md` §9 |
| 38 | Add index/partition review for `DealStageHistory`-shaped tables | `docs/SCALABILITY_REVIEW.md` §9 |
| 39 | Confirm `alembic.ini`'s authoritative migrations directory | `TD-31` |
| 40 | Wire or remove `platform_console`'s unrouted pages | `TD-28` |
| 41 | Add a shared filter-parsing utility for the API | `docs/API_REVIEW.md` §4 |
| 42 | Evaluate consolidating the three in-process task queues | `docs/SCALABILITY_REVIEW.md` §10 |
| 43 | Publish `CanonicalStageMapping` lookup tables for the six deal systems | `TD-47` |
| 44 | Bridge `assetRuntime.move()`/`Membership.role` changes into Life Engine events | `docs/DAILY_OPERATIONS_MODEL.md` §3 |
| 45 | Enforce real Visibility/permission composition at cross-org membership time | `docs/CROSS_ORG_DAILY_COOPERATION.md` §2 |
| 46 | Add `ProjectQualityCheck`/`CorrectiveAction` | `docs/QUALITY_ASSURANCE_ARCHITECTURE.md` §3 |
| 47 | Add `ResourceAllocation` over the nine real resource registries | `docs/RESOURCE_ORCHESTRATION.md` §2 |
| 48 | Add `CustomerFeedback` (plain rating) | `docs/CUSTOMER_JOURNEY.md` §2 |
| 49 | Generalize `Supplier`/`Contractor`/`Subcontractor` beyond automotive | `docs/SUPPLY_CHAIN.md` §2 |
| 50 | Add a bundle-size CI check for `src/web` | `docs/PERFORMANCE_REVIEW.md` §5 |
| 51 | Add distributed tracing once request-ID correlation is platform-wide | `docs/PERFORMANCE_REVIEW.md` §1 |
| 52 | Design the six real `NotificationBucket` values' Russian labels | `docs/RUSSIAN_LOCALIZATION_REVIEW.md` §4 |
| 53 | Update `docs/RUSSIAN_UI_DICTIONARY.md`'s Production Studio term to match shipped "Продакшн" | `docs/RUSSIAN_LOCALIZATION_REVIEW.md` §2 |
| 54 | Give Organizations/Users dedicated Owner-nav entries | `docs/OWNER_EXPERIENCE.md` §1 |
| 55 | Extend `?embed=1` chrome handling beyond `WorkspaceLayout`/`SettingsPage` | `TD-44` |
| 56 | Add mobile-responsive navigation shell | `docs/UI_NAVIGATION.md` §5 |
| 57 | Add a repo-root CI check flagging new top-level directories | Prior recommendation |
| 58 | Publish alias maps for the three "ecosystem" layers | `TD-01` |
| 59 | Clarify Mission Control / Executive Center / drone Mission overlap | `TD-02` |
| 60 | Publish an alias map for `recommendation_engine`'s 6+ locations | `TD-05` |
| 61 | Decide the canonical Enterprise City route among its three aliases | `TD-43` |
| 62 | Fill the 8 frame-only Platform Builder builders via UBF | `TD-10` |
| 63 | Fix the two dead links in `src/web/README.md` | `TD-34` |
| 64 | Add CODEOWNERS coverage for root infra | `TD-35` |
| 65 | Add generic history/versioning pattern for new entities | `TD-54` |
| 66 | Confirm which Knowledge Graph systems persist to Postgres vs. in-memory | `docs/SCALABILITY_REVIEW.md` |
| 67 | Review real dialog/form button labels for verb-first consistency | `docs/RUSSIAN_LOCALIZATION_REVIEW.md` §6 |
| 68 | Add real Ukrainian (`uk`) translations for every new Russian namespace | `docs/RUSSIAN_UI_DICTIONARY.md`, CQ-30.1 |
| 69 | Audit remaining docs for further duplicate-topic clusters | `docs/DOCUMENTATION_REVIEW.md` |
| 70 | Add a real unified query/view over `AuditLog` + `PlatformAuditLog` for on-call use | `docs/OBSERVABILITY_REVIEW.md` §4 |

## TOP 100 — long-term (71–100)

| # | Improvement | Source |
|---|---|---|
| 71 | Evaluate a real GraphQL surface only if a specific enterprise integration requires it | `docs/API_REVIEW.md` §6 |
| 72 | Re-architect frontend runtimes' single-process-state model for 10,000+ org scale | `docs/SCALABILITY_REVIEW.md` §9 |
| 73 | Add read replicas once past 1,000-org scale | `docs/SCALABILITY_REVIEW.md` §9 |
| 74 | Add a distributed job queue once multi-process execution is genuinely needed | `docs/SCALABILITY_REVIEW.md` §5 |
| 75 | Decide keep-code-defined vs. runtime-registrable for `ENTITY_TYPES`/`RELATION_TYPES` | `docs/ARCHITECTURE_REVIEW_V2.md` §6 |
| 76 | Design and build real Production Studio generation backends, provider by provider | `TD-45` |
| 77 | Generalize the real CPL Loyalty/Membership Center beyond cafe/beauty | `docs/CUSTOMER_JOURNEY.md` §3 |
| 78 | Add `technology_park`/`port`/`special_economic_zone` `SpatialDistrictKind` values | `docs/REGIONAL_DIGITAL_TWIN.md` §1 |
| 79 | Implement `TerritoryProfile` generalization of `seedOdessaSpatial()` | `docs/REGIONAL_DIGITAL_TWIN.md` §2 |
| 80 | Reconcile the six-way deal-pipeline collision, deliberately, once Phase 0 has been live long enough | `TD-47` |
| 81 | Reconcile the seven-way workflow-engine collision, deliberately | `TD-48` |
| 82 | Reconcile the four-way Knowledge Graph collision, deliberately | `TD-49` |
| 83 | Full accessibility (screen-reader) audit for the real Russian sidebar | `docs/TOP_100_UX_IMPROVEMENTS.md` #89 |
| 84 | Full DTO consistency audit across all real domains | `docs/API_REVIEW.md` §8 |
| 85 | Real client-portal build-out, once Client Experience design is complete | `docs/CLIENT_EXPERIENCE.md` |
| 86 | Real per-vertical extension review using the `module` discriminator pattern for a 9th vertical | `docs/CROSS_VERTICAL_EXTENSIONS.md` |
| 87 | Evaluate white-label theming (`corporate`/`custom` `ThemeId`s) for an actual customer | `docs/DESIGN_SYSTEM.md` §2 |
| 88 | Real agent-isolation/sandboxing design for the AI Runtime | New finding this sprint — zero real precedent found |
| 89 | Formalize explicit task-cancellation API across the three real task queues | Not fully confirmed this pass |
| 90 | Formalize explicit per-task timeout handling across the three real task queues | Not fully confirmed this pass |
| 91 | Add real backup restore-drill automation (beyond the real `docs/BACKUP_DRILL_32_1.md`) | `docs/BACKUP_DRILL_32_1.md` (real, not re-verified this pass) |
| 92 | Add real disaster-recovery runbook validation | `docs/ERL_BACKUP_DR_MONITORING.md` (real, not re-verified this pass) |
| 93 | Full multi-region deployment design, once multi-country territory work is prioritized | `docs/REGIONAL_DIGITAL_TWIN.md` |
| 94 | Real government-integration compliance review | `docs/ENTERPRISE_V1_READINESS.md`, CQ-30 |
| 95 | Consider namespace grouping for the ~106 top-level Python packages | `TD-56` |
| 96 | Full OpenAPI coverage across every vertical, not just management | `TD-13` |
| 97 | Real SSO/enterprise-identity-provider integration (SAML/OIDC), beyond basic email+MFA | New scope, not previously reviewed |
| 98 | Real per-tenant resource quotas/billing metering | Not previously reviewed |
| 99 | Real chaos-engineering validation of the retry/DLQ infrastructure under failure | `platform_jobs/job_queue.py`'s real DLQ, untested under load |
| 100 | Periodic re-audit cadence — formalize this engagement's own review pattern (CQ-20→30.8) as a standing quarterly process | This entire engagement's own methodology |

## Related documents

`docs/BETA_READINESS_REVIEW.md` (CQ-30.8, the source of TOP 20), `docs/TECH_DEBT.md`,
`docs/TOP_50_IMPROVEMENTS.md`/`docs/TOP_100_UX_IMPROVEMENTS.md`/`docs/TOP_100_RECOMMENDATIONS.md`
(prior ranked lists this one consolidates from), `docs/EXECUTIVE_RELEASE_REPORT.md` (CQ-30.8 sibling).
