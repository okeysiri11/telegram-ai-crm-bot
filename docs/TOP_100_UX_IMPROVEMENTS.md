# Sprint CQ-30.7 — Top 100 UX Improvements

Ranked, each with Why/Impact/Priority/Complexity/Evidence in condensed form. Drawn from this sprint's
fresh evidence (`enterpriseRuNav.ts` review) plus `docs/ROLE_NAVIGATION.md`/`docs/OWNER_MODE_UX.md`/
`docs/PRODUCTION_STUDIO_UX.md` (CQ-30.1) and `docs/TECH_DEBT.md`'s UX-relevant items. Documentation
only.

## Tier 1 — P0/P1, act before Beta (1–20)

| # | Improvement | Why | Impact | Complexity | Evidence |
|---|---|---|---|---|---|
| 1 | Fix Маркетинг → Маркетплейс in `MODULE_LABEL_RU`/`BREADCRUMB_LABEL_RU`/`SEARCH_CATEGORY_RU` | Systemic mislabeling across 3 real dictionaries | Direct comprehension failure for a brief-named module | S | `docs/UX_AUDIT.md` |
| 2 | Confirm Registration/Invitation flow reality | Gates the entire user journey | Beta-blocking if absent | S (verify) | `docs/LOGIN_USER_FLOW.md`, `docs/BETA_USER_JOURNEY.md` |
| 3 | Confirm/build a real Client-role navigation surface | No dedicated nav array found | High for any external-client Beta cohort | S (verify) / L (build) | `docs/CLIENT_EXPERIENCE.md` |
| 4 | Build a Dealer-role nav pointed at existing real automotive data | Real backend exists, no nav surface | High for automotive Beta cohort, low build cost relative to Client | M | `docs/DEALER_EXPERIENCE.md` |
| 5 | Resolve the "marketing" sidebar item — give it a real route or remove it | Currently a second door to the Marketplace page | Confusion, wasted navigation real estate | S | `docs/UX_AUDIT.md` |
| 6 | Document the Owner Dashboard vs. God Mode relationship | Two real destinations both plausibly "the Owner experience" | Medium confusion for new Owners | S | `docs/OWNER_EXPERIENCE.md` §3 |
| 7 | Clarify whether "Среда AI"/"Среда города" render Owner-elevated views or are identical to general nav | Label implies distinction the route doesn't confirm | Medium | S (confirm) / M (build if distinct view is intended) | `docs/OWNER_EXPERIENCE.md` §2 |
| 8 | Add a real-status indicator to Production Studio's sidebar entry, not just individual studio cards | Extends the card-level honesty fix to the entry point | Prevents first-contact overselling | S | `docs/FIRST_TIME_USER.md`, `docs/PRODUCTION_STUDIO_UX.md` §3 |
| 9 | Sequence Beta's first cohort as internal-role-only, defer external Client/Dealer access | Owner/Admin are mature; Client/Dealer are not | Avoids launching a confusing first experience for two personas | S (decision) | `docs/BETA_USER_JOURNEY.md` |
| 10 | Retire the orphaned frontend Command Palette copy | Dead code risk of accidental resurrection during nav polish | Low functional, real maintenance risk | M | `docs/TECH_DEBT.md` TD-40 |
| 11 | Resync `docs/UI_NAVIGATION.md`'s prose sidebar count (17) with the real 23-item array | Documentation drift found this sprint | Misleads anyone reading the doc instead of the code | S | `docs/UX_AUDIT.md` |
| 12 | Verify the AI Production Center consent-gate precedes any generation backend work | Sequencing risk, not yet triggered | High if skipped | M | `docs/TECH_DEBT.md` TD-46 |
| 13 | Add onboarding tooltip distinguishing Главная (Home) from Рабочий стол (Desktop) | Two real landing-adjacent routes, unclear naming | Minor first-time confusion | S | `docs/NAVIGATION_REVIEW.md` §3 |
| 14 | Confirm Owner-scoped backend endpoints enforce server-side checks, not just UI hiding | UI correctly hides links; server-side parity unconfirmed | Security-UX intersection | M (verify) | `docs/SECURITY_REVIEW.md` §8 |
| 15 | Give "Пользователи" (Users) an Owner-nav entry, not only the general sidebar | Natural Owner responsibility currently unsurfaced in the curated Owner nav | Minor | S | `docs/OWNER_EXPERIENCE.md` §1 |
| 16 | Give "Организации" (Organizations) an Owner-nav entry, not folded silently into "Администрирование" | Same reasoning as #15 | Minor-Medium | S (verify current behavior first) | `docs/OWNER_EXPERIENCE.md` §1 |
| 17 | Design the six real `NotificationBucket` values' Russian labels | Currently no confirmed real translation | Notification UI would otherwise ship untranslated or ad hoc | S | `docs/RUSSIAN_LOCALIZATION_REVIEW.md` §4 |
| 18 | Update `docs/RUSSIAN_UI_DICTIONARY.md`'s Production Studio proposal to match the shipped, better "Продакшн" | Prior SPEC term ("Студия продакшна") is worse than what shipped | Low, documentation accuracy | S | `docs/RUSSIAN_LOCALIZATION_REVIEW.md` §2 |
| 19 | Confirm "mission-control" and "monitoring" are intentionally the same Russian label, not accidental | Two routes, one word | Low-Medium | S (verify) | `docs/NAVIGATION_REVIEW.md` §7 |
| 20 | Triage `docs/TENANT_ISOLATION_AUDIT.md`'s 79 findings before Beta with real customer data | Carried from CQ-30.6, restated as UX-adjacent since it gates trustworthy Client/Dealer access specifically | Largest unquantified platform risk | M | `docs/SECURITY_REVIEW.md` §8 |

## Tier 2 — next (21–60)

| # | Improvement | Source | Complexity |
|---|---|---|---|
| 21 | Add a visual sub-item treatment for "Клиенты" as a CRM filtered view, not a peer sidebar item | `docs/UX_AUDIT.md` | S |
| 22 | Unify duplicated favorites/recent-history managers, add real persistence | `TD-41` | M |
| 23 | Complete Platform Builder's token-only auth cutover | `TD-08` | L |
| 24 | Add the missing Knowledge Graph API prefixes to `API_MAP.md` | `TD-49` | S |
| 25 | Add `Project` table + `Deal.project_id` FK | `TD-51` | M |
| 26 | Add generic history/versioning pattern for new entities | `TD-54` | S (document) |
| 27 | Confirm `src/domains`'s 141 files are unused, then document-or-delete | `TD-55` | S |
| 28 | Document the Kernel/Orchestrator/CityVisualization three-layer relationship | `TD-59` | S |
| 29 | Add explicit Kernel/Orchestrator disambiguation notes | `TD-60` | S |
| 30 | Standardize pagination `limit` defaults | `docs/API_REVIEW.md` §3 | S |
| 31 | Add a shared filter-parsing utility | `docs/API_REVIEW.md` §4 | M |
| 32 | Evaluate consolidating the three in-process task queues | `docs/SCALABILITY_REVIEW.md` §10 | L |
| 33 | Add `ResourceAllocation` over the nine real resource registries | `docs/RESOURCE_ORCHESTRATION.md` §2 | M |
| 34 | Add `CustomerFeedback` (plain rating) | `docs/CUSTOMER_JOURNEY.md` §2 | M |
| 35 | Generalize `Supplier`/`Contractor`/`Subcontractor` beyond automotive | `docs/SUPPLY_CHAIN.md` §2 | L |
| 36 | Add `ProjectQualityCheck`/`CorrectiveAction` | `docs/QUALITY_ASSURANCE_ARCHITECTURE.md` §3 | M |
| 37 | Bridge `assetRuntime.move()`/`Membership.role` changes into Life Engine events | `docs/DAILY_OPERATIONS_MODEL.md` §3 | M |
| 38 | Enforce real Visibility/permission composition at cross-org membership time | `docs/CROSS_ORG_DAILY_COOPERATION.md` §2 | M |
| 39 | Extend `?embed=1` chrome handling beyond `WorkspaceLayout`/`SettingsPage` | `TD-44` | M |
| 40 | Add a repo-root CI check flagging new top-level directories | Prior recommendation | S |
| 41 | Publish `CanonicalStageMapping` lookup tables for the six deal systems | `TD-47` | S |
| 42 | Consolidate `platform_builder`'s four near-identical center directories | `TD-27` | M |
| 43 | Fix `database/__init__.py`'s import of `database_legacy` | `TD-19` | M |
| 44 | Reconcile the 29 `reverse_layer_dependency` warnings | `TD-24` | L |
| 45 | Confirm `alembic.ini`'s authoritative migrations directory | `TD-31` | S |
| 46 | Wire or remove `platform_console`'s unrouted pages | `TD-28` | S |
| 47 | Add a connection pooler ahead of 1,000-org scale | `docs/SCALABILITY_REVIEW.md` §9 | M |
| 48 | Add index/partition review for `DealStageHistory`-shaped tables | `docs/SCALABILITY_REVIEW.md` §9 | M |
| 49 | Unify or document why the three permission-scope vocabularies stay separate | `TD-52` | L |
| 50 | Add explicit Beta org-count scope (10–100) to launch materials | `docs/BETA_READINESS_REPORT.md` | S |
| 51 | Add a real-status indicator standard across all "preview" features, not just Production Studio | Extends #8 platform-wide | M |
| 52 | Review every real dialog/form button label for verb-first consistency | `docs/RUSSIAN_LOCALIZATION_REVIEW.md` §6, not yet sampled | M (audit) |
| 53 | Confirm real category grouping (`CATEGORY_LABEL_RU`) is visually applied to the sidebar | `docs/NAVIGATION_REVIEW.md` §2 | S (verify) |
| 54 | Add Lawyer/Accountant/Production as real role-switcher options, not just nav-hidden roles | `docs/ROLE_NAVIGATION.md`, CQ-30.1 | M |
| 55 | Publish alias maps for the three "ecosystem" layers | `TD-01` | S |
| 56 | Clarify Mission Control / Executive Center / drone Mission overlap | `TD-02` | S |
| 57 | Publish an alias map for `recommendation_engine`'s 6+ locations | `TD-05` | S |
| 58 | Decide the canonical Enterprise City route among its three aliases | `TD-43` | S |
| 59 | Fill the 8 frame-only Platform Builder builders via UBF | `TD-10` | L |
| 60 | Fix the two dead links in `src/web/README.md` | `TD-34` | S |

## Tier 3 — defer/polish (61–100)

| # | Improvement | Source | Complexity |
|---|---|---|---|
| 61 | Add CODEOWNERS coverage for root infra | `TD-35` | S |
| 62 | Standardize "X Ready" doc-footer convention | Prior recommendation | M |
| 63 | Add `technology_park`/`port`/`special_economic_zone` `SpatialDistrictKind` values | `docs/REGIONAL_DIGITAL_TWIN.md` §1 | S |
| 64 | Implement `TerritoryProfile` generalization of `seedOdessaSpatial()` | `docs/REGIONAL_DIGITAL_TWIN.md` §2 | M |
| 65 | Confirm no `Deleted` event suffix is introduced anywhere | `docs/EVENT_VOCABULARY.md` §2 | S (policy) |
| 66 | Confirm City's `?embed=1` iframe boundary stays documented for future multi-window work | Prior recommendation | S |
| 67 | Generalize the real CPL Loyalty/Membership Center beyond cafe/beauty | `docs/CUSTOMER_JOURNEY.md` §3 | L |
| 68 | Add `technology_park` naming fix for developer/ai districts currently labeled "construction" | `docs/REGIONAL_DIGITAL_TWIN.md` §1 | S |
| 69 | Review notification toast visual style against real design-system elevation/animation tokens | `docs/DESIGN_SYSTEM.md` | S (verify) |
| 70 | Confirm dark/light theme parity for every screen reviewed this sprint | Not sampled this pass | M (audit) |
| 71 | Add mobile-responsive navigation shell | `docs/UI_NAVIGATION.md` §5, CQ-30.1, flagged gap | L (design) |
| 72 | Document the real 6-category sidebar grouping's intended use even if not yet visually applied | `docs/NAVIGATION_REVIEW.md` §2 | S |
| 73 | Add breadcrumb parity check between City breadcrumbs and standard app breadcrumbs | `docs/UI_NAVIGATION.md` §4, CQ-30.1 | S (verify) |
| 74 | Review "Юридический отдел" (Legal Department) naming vs. brief's "Lawyer" role term for consistency | New, this sprint | S |
| 75 | Confirm "Производство" (Manufacturing) and "Продакшн" (Production Studio) are not confused by users despite similar English roots | New, this sprint | S (verify) |
| 76 | Add a first-login walkthrough highlighting the Command Palette shortcut | `docs/UI_NAVIGATION.md` §6, CQ-30.1 | S |
| 77 | Review Quick Actions list for completeness against the 23-item sidebar (several modules have no quick action) | New, this sprint | M |
| 78 | Add "Знания" vs "Граф знаний" distinguishing copy for Owners | `docs/OWNER_EXPERIENCE.md` §1 | S |
| 79 | Confirm `owner_flags` (Feature Flags) UI doesn't expose the raw JWT `fail_fast` setting unsafely | `docs/OWNER_MODE_UX.md` §3, CQ-30.1 | S (verify) |
| 80 | Review "Проекты" vs "Задачи" distinction clarity for new users | New, this sprint | S |
| 81 | Add real Ukrainian (`uk`) translations for every new namespace `docs/RUSSIAN_UI_DICTIONARY.md` added | CQ-30.1 non-goal, now a real follow-up | M |
| 82 | Audit remaining ~1,257 docs for further duplicate-topic clusters beyond the known five | `docs/DOCUMENTATION_REVIEW.md`, CQ-30 | L |
| 83 | Confirm Search result ranking surfaces Marketplace correctly once #1's fix ships | Follow-up to #1 | S (verify) |
| 84 | Review Notification Center's real channel fan-out UI for Critical alerts | `docs/UI_NAVIGATION.md` §3, CQ-30.1 | S (verify) |
| 85 | Confirm City search "Enter opens first hit" behavior doesn't surprise users expecting a result list | `docs/CITY_NAVIGATION.md`, real Sprint 30.4 | S (verify) |
| 86 | Review real City breadcrumb "Домой" (Home) button naming vs. sidebar's separate "Главная" (also Home) | New, this sprint — same English word, two Russian contexts | S |
| 87 | Confirm real Org Selector's hardcoded demo entries are replaced before Beta | New, this sprint (`demo-corp`/`acme-ltd`/`bidex`) | S |
| 88 | Add loading/empty states review for the 23 real sidebar destinations | Not sampled this pass | M (audit) |
| 89 | Review accessibility (screen-reader labels) for the real Russian sidebar | Not sampled this pass | M (audit) |
| 90 | Confirm real MFA setup flow is discoverable from Settings, not only Security Center | `docs/LOGIN_USER_FLOW.md`, CQ-30.1 | S (verify) |
| 91 | Review AccessDeniedPage.tsx copy for role-mismatched deep links | `docs/LOGIN_USER_FLOW.md` §4, CQ-30.1 | S (verify) |
| 92 | Add SessionExpiredPage/AccountLockedPage Russian copy review | Not sampled this pass | S |
| 93 | Confirm real `ExternalPilotOnboardPage.tsx` flow matches this sprint's first-time-user recommendations | `docs/UX_AUDIT.md` | S (verify) |
| 94 | Review Analytics module's real data freshness indicators for first-time trust-building | Not sampled this pass | M |
| 95 | Confirm real Documents module supports the file types a Beta customer would actually use | Not sampled this pass | M (verify) |
| 96 | Review Finance module naming ("Финансы") against Accountant role's expectations | New, this sprint | S |
| 97 | Confirm City's "Central Plaza" (`returnHome`) concept has a clear Russian label matching "Домой" | `docs/CITY_NAVIGATION.md`, real Sprint 30.4 | S (verify) |
| 98 | Add a design-system component catalog entry check specifically for Notification/Toast | `docs/DESIGN_SYSTEM.md` §3, CQ-30.1 | S (verify) |
| 99 | Review real Health/Monitoring page for Owner vs. general-user information density differences | `docs/OWNER_EXPERIENCE.md` §1 | S (verify) |
| 100 | Schedule a follow-up UX review after Sprint 30.7 lands, to re-verify every "unconfirmed" item in this document against the finished implementation | This document's own methodology note | S (process) |

## Related documents

`docs/UX_AUDIT.md`/`docs/NAVIGATION_REVIEW.md`/`docs/OWNER_EXPERIENCE.md`/`docs/CLIENT_EXPERIENCE.md`/
`docs/DEALER_EXPERIENCE.md`/`docs/RUSSIAN_LOCALIZATION_REVIEW.md`/`docs/BETA_USER_JOURNEY.md`/
`docs/FIRST_TIME_USER.md` (CQ-30.7 siblings, the source of every Tier 1 item), `docs/TECH_DEBT.md`
(canonical registry, source of most Tier 2/3 items), `docs/TOP_50_IMPROVEMENTS.md` (CQ-30.6, the prior
architecture-focused ranked list this one complements from the UX angle).
