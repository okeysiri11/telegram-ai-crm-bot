# Enterprise City — Recommendation & Predictive Engine

**Sprint:** CQ-14 — Architecture Research + AI Orchestration. Documentation only, `src` not modified.
Covers the brief's §3 (Recommendation Engine) and §4 (Predictive Analytics) together.

**Do not duplicate:** `PROFESSIONAL_NETWORK_DISCOVERY.md` §2.2 (CQ-13) already designed the
Recommendation Engine's ranking-input composition (trust proximity, relationship proximity) for
partner/contact discovery specifically — this document generalizes that same engine to the brief's
nine categories rather than re-deriving it. `platform_predictive_intelligence` and `platform_decision`
are both real, confirmed this sprint — cited, not re-implemented.

## 1. Recommendation Engine (brief §3) — one real pipeline, nine categories

### 1.1 Real foundation

Two real, wired pipelines already exist: `platform_decision.decision_engine`'s `DecisionEngine.decide()`
(scores candidates via `DecisionPolicy` weight vectors — `balanced`, `cost_first`, `risk_averse`,
`business_priority`, real dict-based weighted scoring) and `platform_learning.recommendation_engine`'s
`RecommendationEngine.generate()` (rule-based, real, requires human `accept()`/`reject()`,
`ENTERPRISE_INTELLIGENCE_CORE.md` §3). Both are real, deterministic, and already produce a
confidence-scored, traceable recommendation — this document routes all nine brief categories through
these two, never a new scoring pipeline.

### 1.2 Per-category mapping

| Brief category | Candidate source | Scoring policy |
|---|---|---|
| Recommend Partners | `EBN_BUSINESS_GRAPH.md` §1 real `RelationshipType` graph (CQ-10) | `balanced` `DecisionPolicy` |
| Recommend Employees | Real `Citizen`/`Membership` (Sprint 29.1) filtered by role/skill (`DIGITAL_CITIZEN.md` §1, CQ-12) | `balanced` |
| Recommend AI Agents | Real `MARKETPLACE.md` agent registry (Sprint 12.1, CQ-13) | `cost_first` (real policy name, fits agent selection by resource cost) |
| Recommend Contractors | `CITIZEN_ORGANIZATION_MEMBERSHIP.md` §1 real `consultant`/`external_contractor` roles (CQ-12) | `risk_averse` (real policy — contractor vetting favors caution) |
| Recommend Suppliers | Real `Relationship.type: "supplier"` (Sprint 29.0) | `business_priority` |
| Recommend Customers | Real `Relationship.type: "customer"` | `business_priority` |
| Recommend Investments | `INVESTMENT_LAYER.md` (CQ-13) `InvestmentOpportunity`/`InvestorProfile` | `risk_averse` |
| Recommend Automations | Real `AutomationEngine` templates (Sprint 28.9) | `cost_first` |
| Recommend Knowledge | Whichever real surface `AI_MEMORY.md`'s (CG-8) reconciliation resolves to | `balanced` |

Every category reuses one of the four **real, already-named** `DecisionPolicy` values — this document
does not invent a fifth policy per category, matching the platform's own real design (a small, fixed
policy set applied broadly, not one policy per feature).

## 2. Predictive Analytics (brief §4) — real, but honestly scoped

### 2.1 What exists today (verified) — hardcoded formulas, advisory-only by explicit design

`platform_predictive_intelligence/facade.py`'s `PredictiveIntelligenceLibrary` is real and composes 11
sub-modules — but **every formula found this sprint is fixed arithmetic, not statistics or ML**:
`BusinessForecastEngine.forecast()` computes `baseline * (1 + 0.02*(horizon_days/30))` — a flat 2%/
30-day growth constant, not a learned trend. `CustomerPredictionEngine.predict()` uses linear formulas
(`revisit = max(0.05, min(0.95, 0.9 - days/200))`). `RiskIntelligence.assess()` averages five
hardcoded-default risk scores. `PredictionRegistry`'s stored "accuracy" values are seeded literals
(e.g. `0.82`, `0.78`) at bootstrap, **not measured against real outcomes**. Critically, the real
`bootstrap()` call explicitly sets `"ai_may_act": False, "auto_actions": False` — the platform's own
code already enforces the advisory-only posture this brief's §9 (Ethics & Governance) independently
asks for.

**Also confirmed**: the real frontend `src/web/src/predictive-intelligence/derivePredictive.ts` does
**not** call this real backend library at all — its own file header states "Pure client forecasts...
No new Prediction Engine," and it derives forecasts purely from local, already-simulated snapshot
data (`aiLoad = clamp(20 + snapshot.aiOps.running.length*22 + ...)`). This is the same "real backend,
disconnected simulated frontend" pattern found at every other layer of this platform (AI OS, CG-8;
City AI, CG-6) — restated here because Predictive Analytics is the one brief section most likely to
be assumed more sophisticated than it is without this specific check.

### 2.2 Per-item mapping

| Brief item | Real foundation |
|---|---|
| Business Growth Forecast | `BusinessForecastEngine` (real, fixed-formula) |
| Project Risks | `RiskIntelligence` (real, fixed-formula) |
| Partner Reliability | **SPEC, new** — no real module scores relationship reliability specifically; proposed as a `RiskIntelligence`-pattern extension reading real `Relationship.state`/history (Sprint 29.0), not a new engine |
| Resource Forecast | `operations/__init__.py`'s real operations module |
| Workload Prediction | Same real operations module, or real `AutomationEngine` queue depth (Sprint 28.9) |
| Financial Trends | `BusinessForecastEngine` + real `DIGITAL_ASSET_TREASURY.md` data (Sprint 18.4, CQ-13) if extended to read it (not currently wired, per `DIGITAL_ASSETS.md`'s explicit non-integration) |
| Operational Bottlenecks | `OpportunityDetector`'s real if/else threshold rules, inverted (a "bottleneck" is the same threshold-crossing shape as an "opportunity," opposite direction) |
| Citizen Productivity | **SPEC, new** — no real module; proposed as reading real per-citizen `AuditLog` activity volume (CQ-12), explicitly *not* a surveillance-style scoring system — see `ETHICS_GOVERNANCE.md` for the constraint this item must satisfy before any implementation |

### 2.3 The one governance implication worth stating here

Because the real Predictive Intelligence library already enforces `ai_may_act: False`, **every
prediction this document proposes routing through it inherits that same advisory-only guarantee
automatically** — this is a structural safety property, not a policy this document has to separately
design and enforce.

## 3. Non-goals

- No new scoring/decision pipeline — §1 routes every category through the two real, existing engines.
- No claim that Predictive Analytics uses statistics or ML — §2.1's hardcoded-formula finding is
  stated as fact, not softened.
- No Citizen Productivity scoring is designed in a way that enables surveillance — flagged for
  `ETHICS_GOVERNANCE.md` to constrain, not solved here.

## Related documents

`ENTERPRISE_INTELLIGENCE_CORE.md` (real Decision Engine), `PROFESSIONAL_NETWORK_DISCOVERY.md` §2.2
(CQ-13, the recommendation-input pattern this document generalizes), `AI_AGENT_LIFECYCLE.md` (CG-8,
agent selection inputs), `EBN_BUSINESS_GRAPH.md`/`ENTERPRISE_ECONOMY.md` (CQ-10/13, relationship/
economy inputs), `AUTOMATION_ENGINE.md` (Sprint 28.9), `ETHICS_GOVERNANCE.md` (CQ-14 sibling, the
constraint on Citizen Productivity).
