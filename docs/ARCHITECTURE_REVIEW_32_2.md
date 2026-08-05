# Sprint CQ-32.2 — Enterprise Architecture Review

**Mode:** Chief Enterprise Architect / CTO / Principal Platform Engineer, performed while Cursor
implements Sprint 32.2 in parallel. Documentation only, `src` not modified, no implementation.

## 1. Platform Core — duplication, re-confirmed and quantified

| Category | Count | Canonical candidate | Source |
|---|---|---|---|
| Duplicated deal/pipeline services | 6 | `deal_pipeline_engine.py` | `TD-47` |
| Duplicated workflow runtime logic | 7 | none yet — `TD-48` unresolved | `TD-48` |
| Duplicated Knowledge Base APIs | 4 | Sprint 24.2 `platform_enterprise_knowledge_graph` | `TD-49` |
| Duplicated task/entity models | 3 | none yet — `TD-50` unresolved | `TD-50` |
| Duplicated EventBus classes | 6+ | `events/event_bus.py::PlatformEventBus` | `TD-20` |
| Duplicated memory stacks | 4+ | none yet | `TD-21` |
| Duplicated rate limiters | 2 | relationship unconfirmed | `docs/ARCHITECTURE_CONSISTENCY.md` Issue 4 |
| Duplicated agent registries | 3-4 | none yet | `docs/AI_RUNTIME_REVIEW.md` §1 |
| Duplicated cross-runtime aggregators | 3 | relationship undocumented | `TD-59` |
| Duplicated naming (Kernel/Orchestrator) | 2×2 | disambiguate, don't rename | `TD-60` |

Ten distinct duplication categories, all previously tracked individually across this engagement's
twenty-plus sprints — this table's contribution is presenting them together as one quantified picture
for a CTO-level read, not re-deriving any of them.

## 2. Module boundaries

- **Leaking responsibilities**: the six-way deal collision is the clearest instance — `deal.py`'s OTC-
  flavored statuses (`KYC_PENDING`, `FUNDS_EXPECTED`) suggest a financial-settlement concern leaking
  into what should be a generic sales-pipeline entity.
- **Mixed domains**: `applications/enterprise_hub/` remains, per prior reviews, a "kitchen sink"
  package containing AI OS, business capabilities, knowledge platform, digital twin, integrations, and
  more under one top-level directory — a real, previously-flagged (TD-01 "ecosystem" naming) instance
  of insufficient domain separation at the package level.
- **Feature coupling**: `cityVisualization`'s real 8-runtime fan-in and `orchestrator`'s real 10-
  runtime fan-in (`TD-59`) are the platform's clearest feature-coupling risk — both are single points
  with unusually wide blast radius.
- **Circular dependencies**: `TD-36`'s 47 legacy `pg_*` cycles remain confined to the compatibility
  layer (0 strict cycles in governed layers, per `docs/architecture_baseline/DEPENDENCY_GRAPH.md`) —
  restated as still the correct, reassuring read of this finding.
- **Dependency inversion violations**: `TD-19` (`database/__init__.py` → `database_legacy`) remains
  the clearest concrete instance — a modern package depending downward on the legacy layer it should
  be isolated from.

## 5. Clean Architecture

No explicit Presentation/Application/Domain/Infrastructure layer naming convention exists anywhere in
the codebase (confirmed via direct search this sprint) — but the **functional** separation is largely
real: route handlers (Presentation) → `services/` (Application) → real domain models (Domain, informal)
→ `repositories/`+`database/` (Infrastructure). This is Clean-Architecture-*shaped* without being
Clean-Architecture-*named*, which this review assesses as acceptable — retrofitting formal layer names
onto working code has real churn cost for no functional benefit. The one real violation of the
*intent* behind these layers (not just the naming) is `TD-19`'s dependency-inversion break — Domain/
Infrastructure code should never depend on legacy Infrastructure it's meant to supersede.

## 11. Enterprise City

- **City Engine**: real, with genuine LOD/performance-budget discipline (`docs/SCALABILITY_REVIEW.md`
  §7, CQ-30.6) — a confirmed architecture strength, not re-derived here.
- **Navigation**: real, current implementation (`enterpriseRuNav.ts`, Sprint 30.2/30.7) reviewed in
  depth at `docs/UX_AUDIT.md`/`docs/NAVIGATION_REVIEW.md` (CQ-30.7) — the Маркетинг/Маркетплейс bug
  remains the sharpest finding there, not repeated here.
- **District architecture**: real 12-district model (`CITY_DISTRICTS.md`), `docs/CROSS_VERTICAL_
  EXTENSIONS.md`'s (CQ-19) `module`-discriminator pattern remains the recommended extension mechanism
  over a plugin-runtime approach — restated from `docs/ARCHITECTURE_REVIEW_V2.md` §5 (CQ-30.6).
- **Module wiring**: City's real `cityVisualization`/`orchestrator` dual-aggregator situation
  (§1 above, `TD-59`) is City-adjacent architecture's most consequential open question.
- **God Mode**: real, distinct route (`/platform-builder/god-mode`) from the real Owner Dashboard
  (`/owner`) — `docs/OWNER_EXPERIENCE.md` (CQ-30.7) already flagged the relationship between the two
  as undocumented; restated as still open.
- **Digital Twin concept**: the five-way naming collision (`TD-04` extended by CQ-16) remains
  unresolved at the naming level; the real geo-relevant lineage (Spatial Runtime) remains architecturally
  sound and distinct from the four organizational "Digital Twin" false friends.

## 13. Architecture Governance

- **Architecture Review**: real and working — this document is itself the eighth in a lineage of
  independent reviews across this engagement, each building on and re-verifying the last. The process
  works; formalizing its cadence (recommended in `docs/SPRINT_CQ_30_6_ARCHITECT_REVIEW.md` §5) remains
  the one open recommendation.
- **Technical Debt Registry**: real, mature, self-correcting (`docs/TECH_DEBT.md`, now TD-01 through
  TD-60+) — the platform's strongest governance artifact, confirmed again this sprint.
- **Dependency Graph**: real (`docs/DEPENDENCY_MAP.md`, `docs/architecture_baseline/DEPENDENCY_
  GRAPH.md`), regenerated via `scripts/generate_architecture_baseline.py` — real tooling, not just a
  document.
- **ADR process**: **confirmed absent as a formal artifact.** No `ADR*`/`decision-record*` files or
  directory exist anywhere in the repo. `CLAUDE.md` itself already acknowledges this ("In the absence
  of a dedicated ADR directory in this repo, record the decision... in that sprint's RESULT.md") — a
  deliberate, documented choice, not an oversight. This review's assessment: the RESULT.md convention
  is a reasonable substitute for a platform at this stage, but does not scale as well as a dedicated,
  searchable ADR log once decision volume grows — worth revisiting post-Beta, not before.
- **Coding Standards / Platform Standards**: not independently audited this pass.
- **Release Gates**: real — the three-job CI pipeline (`pytest`, `architecture`, `security`, per
  `CLAUDE.md`) is a genuine, working release gate.

## Non-goals

- No implementation of any recommendation.
- No re-derivation of the ten duplication categories in §1 — each is cited to its original source.

## Related documents

`docs/TECH_DEBT.md` (canonical registry), `docs/PLATFORM_CORE_REVIEW.md`/`docs/DDD_REVIEW.md`/
`docs/AI_RUNTIME_REVIEW.md`/`docs/N8N_REVIEW.md`/`docs/SECURITY_ARCHITECTURE_REVIEW.md` (CQ-32.2
siblings), `docs/RUNTIME_CONSISTENCY.md`/`docs/DOMAIN_BOUNDARIES.md` (CQ-30), `docs/UX_AUDIT.md`
(CQ-30.7, City navigation detail).
