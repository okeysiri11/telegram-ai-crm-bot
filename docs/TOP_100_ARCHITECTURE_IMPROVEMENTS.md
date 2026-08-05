# Sprint CQ-32.2 — Top 100 Architecture Improvements

Ranked using the brief's seven categories: **Critical** (blocks safe operation), **High** (real risk,
should precede scale), **Medium** (real but not urgent), **Low** (cosmetic/discoverability),
**Quick Win** (cheap + high value regardless of severity), **Technical Debt** (tracked, accepted,
scheduled deliberately), **Future Improvement** (deferred by design, not urgency). Documentation only.

## Critical (1–8)

| # | Item | Source |
|---|---|---|
| 1 | Add a CI lint rule for insecure-default-secret patterns; fix the two new instances found (`API_JWT_SECRET`, `N8N_ENCRYPTION_KEY`) | `docs/SECURITY_ARCHITECTURE_REVIEW.md` §2 |
| 2 | Configure real TLS at the nginx layer | `docs/PRODUCTION_GAPS.md`, CQ-30.8 |
| 3 | Verify Knowledge Base tenant isolation on the real RAG/context-assembly path before any semantic search work begins | `docs/AI_RUNTIME_REVIEW.md` §4, `docs/SECURITY_ARCHITECTURE_REVIEW.md` §4 |
| 4 | Triage the 79 tenant-isolation findings | `docs/TENANT_ISOLATION_AUDIT.md`, CQ-30.6 |
| 5 | Verify Registration/Invitation flow reality | `docs/LOGIN_USER_FLOW.md`, CQ-30.1 |
| 6 | Fix nginx's placeholder catch-all response | `docs/PRODUCTION_GAPS.md`, CQ-30.8 |
| 7 | Remove Grafana's default admin password fallback | `docs/SECURITY_REVIEW.md` §9, CQ-30.8 |
| 8 | Add a basic prompt-injection layer — **superseded, already real (Sprint 30.9)**, kept here only to show the item closed | `docs/SECURITY_ARCHITECTURE_REVIEW.md` §1 |

## High (9–25)

| # | Item | Source |
|---|---|---|
| 9 | Pick one canonical AI agent registry among 3-4 real candidates | `docs/AI_RUNTIME_REVIEW.md` §1 |
| 10 | Centralize Workflow as a real Platform Core service (7 real engines today) | `docs/PLATFORM_CORE_REVIEW.md` |
| 11 | Centralize Marketplace as a real Platform Core service (4+ real systems today) | `docs/PLATFORM_CORE_REVIEW.md` |
| 12 | Centralize Knowledge Base as a real Platform Core service (4 real systems today) | `docs/PLATFORM_CORE_REVIEW.md` |
| 13 | Centralize AI Runtime as a real Platform Core service | `docs/PLATFORM_CORE_REVIEW.md` |
| 14 | Introduce a real `DealAggregate` facade enforcing the Deal/DealStage/DealTask/DealStageHistory write path | `docs/DDD_REVIEW.md` |
| 15 | Decide whether `src/events`'s real DDD `DomainEvent` pattern should be adopted platform-wide or left as historical reference | `docs/DDD_REVIEW.md` |
| 16 | Document the Kernel/Orchestrator/CityVisualization three-layer relationship | `TD-59` |
| 17 | Confirm MCP Authentication's tenant-scoping matches the Python backend's model | `docs/SECURITY_ARCHITECTURE_REVIEW.md` §3 |
| 18 | Trace the two real rate limiters' relationship | `docs/ARCHITECTURE_CONSISTENCY.md` Issue 4 |
| 19 | Build a Dealer navigation surface (real data already exists) | `docs/DEALER_EXPERIENCE.md`, CQ-30.7 |
| 20 | Complete Platform Builder's token-only auth cutover | `TD-08` |
| 21 | Fix Маркетинг→Маркетплейс in the 3 real label dictionaries | `docs/UX_AUDIT.md`, CQ-30.7 |
| 22 | Add a Docker healthcheck to the `bot` service | `docs/OBSERVABILITY_REVIEW.md` §2, CQ-30.8 |
| 23 | Build the AI Production Center consent-gate before any voice/avatar generation work | `TD-46` |
| 24 | Add per-tenant queue quotas ahead of 1,000+ org scale | `docs/AI_RUNTIME_REVIEW.md` §6 |
| 25 | Confirm explicit per-task timeout handling exists in both real task queues | `docs/AI_RUNTIME_REVIEW.md` §7 |

## Medium (26–50)

| # | Item | Source |
|---|---|---|
| 26 | Fix `database/__init__.py`'s import of `database_legacy` | `TD-19` |
| 27 | Reconcile the 29 `reverse_layer_dependency` warnings | `TD-24` |
| 28 | Add `Project` table + `Deal.project_id` FK | `TD-51` |
| 29 | Unify or explicitly justify keeping separate the three permission-scope vocabularies | `TD-52` |
| 30 | Add log aggregation (Loki) | `docs/OBSERVABILITY_REVIEW.md` §3 |
| 31 | Extend real `request_id` correlation into structured logs platform-wide | `docs/PERFORMANCE_REVIEW.md` §1 |
| 32 | Audit error-response consistency across non-management domains | `docs/API_REVIEW.md` §8 |
| 33 | Run a real load test on `management_router`/`dashboard_service` fan-out | `TD-32` |
| 34 | Add a connection pooler ahead of 1,000-org scale | `docs/SCALABILITY_REVIEW.md` §9 |
| 35 | Evaluate consolidating the three in-process task queues | `docs/SCALABILITY_REVIEW.md` §10 |
| 36 | Confirm which Knowledge Graph systems persist to Postgres vs. in-memory | `docs/SCALABILITY_REVIEW.md` |
| 37 | Add a shared filter-parsing utility for the API | `docs/API_REVIEW.md` §4 |
| 38 | Standardize pagination `limit` defaults | `docs/API_REVIEW.md` §3 |
| 39 | Complete a Pricing service location trace | `docs/PLATFORM_CORE_REVIEW.md` |
| 40 | Complete a Catalog convention audit across `productionCatalog.ts`/design-system/business-capabilities | `docs/PLATFORM_CORE_REVIEW.md` |
| 41 | Confirm/remove the second SQLite artifact in `backups/` | `docs/SECURITY_REVIEW.md`, CQ-30.8 |
| 42 | Add explicit caching-invalidation strategy documentation for Redis usage | `docs/PERFORMANCE_REVIEW.md` §6 |
| 43 | Audit streaming architecture (not covered in any prior review) | `docs/PERFORMANCE_REVIEW.md` §6 |
| 44 | Scope Client portal design as its own explicit follow-up | `docs/CLIENT_EXPERIENCE.md`, CQ-30.7 |
| 45 | Confirm every backend Owner-scoped endpoint enforces server-side checks | `docs/SECURITY_REVIEW.md` §8 |
| 46 | Add explicit Beta org-count scope (10–100) to launch materials | `docs/BETA_READINESS_REVIEW.md`, CQ-30.8 |
| 47 | Confirm `src/domains`'s 141 files are unused, then document-or-delete | `TD-55` |
| 48 | Consolidate `platform_builder`'s four near-identical center directories | `TD-27` |
| 49 | Add a real unified query/view over `AuditLog` + `PlatformAuditLog` for on-call use | `docs/OBSERVABILITY_REVIEW.md` §4 |
| 50 | Add explicit Bounded Context documentation for Sales/Operations/AI/Territory domains | `docs/DDD_REVIEW.md` |

## Low (51–65)

| # | Item | Source |
|---|---|---|
| 51 | Resync `docs/UI_NAVIGATION.md`'s sidebar count with the real 23-item catalog | `docs/UX_AUDIT.md`, CQ-30.7 |
| 52 | Disambiguate `./platform`/`./workflow` bare top-level directories | `TD-56` |
| 53 | Confirm `alembic.ini`'s authoritative migrations directory | `TD-31` |
| 54 | Fix the two dead links in `src/web/README.md` | `TD-34` |
| 55 | Add CODEOWNERS coverage for root infra | `TD-35` |
| 56 | Publish alias maps for the three "ecosystem" layers | `TD-01` |
| 57 | Clarify Mission Control / Executive Center / drone Mission overlap | `TD-02` |
| 58 | Publish an alias map for `recommendation_engine`'s 6+ locations | `TD-05` |
| 59 | Decide the canonical Enterprise City route among its three aliases | `TD-43` |
| 60 | Add a bundle-size CI check for `src/web` | `docs/PERFORMANCE_REVIEW.md` §5 |
| 61 | Add mobile-responsive navigation shell | `docs/UI_NAVIGATION.md` §5, CQ-30.1 |
| 62 | Standardize the "X Ready" doc-footer convention | Prior recommendation |
| 63 | Add real Ukrainian (`uk`) translations for new Russian namespaces | `docs/RUSSIAN_UI_DICTIONARY.md`, CQ-30.1 |
| 64 | Add the missing Knowledge Graph API prefixes to `API_MAP.md` | `TD-49` |
| 65 | Publish `CanonicalStageMapping` lookup tables for the six deal systems | `TD-47` |

## Quick Win (66–75)

| # | Item | Why it's a quick win |
|---|---|---|
| 66 | Wire or remove `platform_console`'s unrouted pages | Cheap, closes a real unenforced-auth-by-omission gap |
| 67 | Retire the orphaned frontend Command Palette copy | Dead code, zero functional risk to remove |
| 68 | Add a real-status indicator to Production Studio's sidebar entry | One UI element, prevents overselling |
| 69 | Document Owner Dashboard vs. God Mode's relationship | One paragraph, resolves real confusion |
| 70 | Add Organizations/Users to Owner-nav | Two nav entries, closes two real coverage gaps |
| 71 | Update `docs/RUSSIAN_UI_DICTIONARY.md`'s Production Studio term to match shipped "Продакшн" | One-line documentation fix |
| 72 | Give explicit Kernel/Orchestrator disambiguation notes wherever either pair appears | Documentation-only, no code change |
| 73 | Design the six real `NotificationBucket` Russian labels | Small, unblocks a real UI gap |
| 74 | Close `TD-17` in the registry as formally `RESOLVED` | Administrative, already fixed |
| 75 | Add a one-line ADR-directory-absence acknowledgment cross-reference in `ARCHITECTURE_MAP.md` | Already stated in `CLAUDE.md`, just needs a pointer |

## Technical Debt — tracked, accepted, scheduled deliberately (76–90)

| # | Item | Why deliberately deferred |
|---|---|---|
| 76 | Six-way deal-pipeline collision | Real, working systems; premature consolidation risk exceeds current cost |
| 77 | Seven-way workflow-engine collision | Same reasoning |
| 78 | Four-way Knowledge Graph collision | Same reasoning |
| 79 | Four+ agent registries | Same reasoning, pending #9's canonical pick |
| 80 | `TD-36`'s 47 legacy `pg_*` cycles | Explicitly deferred with justification, confined to compatibility layer |
| 81 | `TD-25`'s `database_legacy.py` (11,205 lines) | XL effort, explicit non-action per `TECHNICAL_DEBT_REPORT.md` policy |
| 82 | Three permission-scope vocabularies | Real escalation-vector risk, but unifying is L effort — scheduled, not urgent |
| 83 | `platform_*` vs `platform_enterprise_*` naming ambiguity | Cosmetic, real cost is discoverability only |
| 84 | `~100 top-level directories` sprawl | XL restructure risk exceeds current discoverability cost |
| 85 | Three notification vocabularies | `TD-53`, real but low-severity |
| 86 | No generic history/versioning mixin | `TD-54`, pattern proposed, retrofit deferred |
| 87 | `container.py`'s unused DI scaffold | `TD-18`, decide-or-retire, not urgent |
| 88 | Two migrations directories | `TD-31`, needs a five-minute confirm, then closed |
| 89 | No formal ADR directory | Deliberate choice per `CLAUDE.md`, revisit post-Beta |
| 90 | Uneven OpenAPI coverage across verticals | `TD-13`, real but not launch-blocking |

## Future Improvement — deferred by design (91–100)

| # | Item |
|---|---|
| 91 | Real vector/RAG search engine, built tenant-isolated from day one |
| 92 | Real distributed task queue once multi-process execution is genuinely needed |
| 93 | Read replicas once past 1,000-org scale |
| 94 | Re-architect frontend runtimes' single-process-state model for high concurrent-session counts |
| 95 | Real GraphQL surface, only if a specific enterprise integration requires it |
| 96 | Real Production Studio generation backends, provider by provider, after the consent gate exists |
| 97 | Real government-integration compliance review |
| 98 | Real multi-region deployment design |
| 99 | Real per-tenant resource quotas/billing metering |
| 100 | Formalize this engagement's own review cadence (CQ-20 → CQ-32.2) as a standing quarterly architecture review process |

## Related documents

Every CQ-32.2 sibling document (`docs/ARCHITECTURE_REVIEW_32_2.md`, `docs/PLATFORM_CORE_REVIEW.md`,
`docs/DDD_REVIEW.md`, `docs/SECURITY_ARCHITECTURE_REVIEW.md`, `docs/AI_RUNTIME_REVIEW.md`,
`docs/N8N_REVIEW.md`, `docs/SCALABILITY_REVIEW.md`, `docs/PERFORMANCE_REVIEW.md`), `docs/TECH_DEBT.md`
(canonical registry), `docs/EXECUTIVE_CTO_REPORT.md` (the capstone verdict).
