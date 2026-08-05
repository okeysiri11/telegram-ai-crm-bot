# Enterprise Value Chain — Business Value Metrics

**Sprint:** CQ-18 — Architecture Research + Intelligence Design. Documentation only, `src` not
modified.

**Do not duplicate:** `docs/TERRITORIAL_ANALYTICS.md`/`docs/ENTERPRISE_HEALTH.md` (CQ-15/CQ-16) already
established the read-only composite-snapshot pattern and `docs/ETHICS_GOVERNANCE.md`'s (CQ-14)
confidence-labeling discipline — every metric below follows both, and none is a new scoring engine.
Confirmed this sprint by direct search: **no real NPS/CSAT/project-success/on-time-delivery metric
exists anywhere** in `database/models/` or `platform_predictive_intelligence` — several of the brief's
seven metrics are genuinely new, stated honestly rather than backed with invented precedent.

## 1. Per-metric mapping (brief's seven)

| Brief metric | Real/SPEC source |
|---|---|
| Project Success | **New** — computed from `ProjectQualityCheck.validationPassed` ratio + on-time delivery (`Project` state timestamps vs. `DealStage.sla_hours` at each stage, both real/SPEC from `QUALITY_ASSURANCE_ARCHITECTURE.md`/`ENTERPRISE_VALUE_CHAIN.md`) — a derived ratio, not a new tracked field |
| Customer Satisfaction | Real `CustomerFeedback.rating` (`CUSTOMER_JOURNEY.md`, this sprint) averaged per company/project — no NPS/CSAT methodology implied, per that document's own constraint |
| Partner Trust | Real `BusinessProfile.trust_level` (Sprint 29.0) — already exists, reused directly, no new field |
| Operational Efficiency | **New, but built from real time data** — real `DealStage.sla_hours` vs. actual `DealStageHistory` transition timestamps already gives real "planned vs. actual" duration data; efficiency is that ratio, computed, not stored |
| Asset Utilization | Real `AssetOwnership`/`assetRuntime` usage counts (`DIGITAL_TWIN_STANDARDS.md`, CQ-16), same aggregation approach `TERRITORIAL_ANALYTICS.md`'s (CQ-16) Infrastructure Utilization already used |
| Knowledge Growth | Real `platform_enterprise_knowledge_graph`'s entity/memory-version count (`AI_MEMORY.md`, CG-8) — a count of real stored knowledge artifacts, not a "learning" claim |
| AI Contribution | Real `platform_learning`'s accept/reject counts (`Recommendation.accept()`/`.reject()`, CQ-14) — a concrete, already-real measure of how often an AI recommendation was actually acted on, the most defensible "AI Contribution" metric available since it requires a real human decision, not a self-reported AI confidence score |

## 2. Composite Business Value Snapshot (SPEC, same discipline as `EnterpriseHealthSnapshot`/`TerritorialAnalyticsSnapshot`)

```ts
// SPEC — read-only, every field traces to a real or clearly-labeled-new signal, confidence labeled
// per ETHICS_GOVERNANCE.md (CQ-14). No field is a vanity metric a company/citizen can inflate directly.
interface BusinessValueSnapshot {
  scopeId: string;                    // Project.id, BusinessProfile.id, or territory SpatialEntity.id
  projectSuccessRate?: number;         // validationPassed ratio + on-time ratio, "heuristic" confidence
  customerSatisfaction?: number;       // avg CustomerFeedback.rating, plain average, not NPS
  partnerTrust: number;                // real BusinessProfile.trust_level, unchanged
  operationalEfficiency?: number;      // real SLA-vs-actual ratio
  assetUtilization?: number;           // real AssetOwnership usage aggregate
  knowledgeGrowth?: number;            // real knowledge-graph entity count delta
  aiContribution?: number;             // real accepted/total recommendation ratio
}
```

## Non-goals

- No NPS/CSAT methodology adopted — `customerSatisfaction` stays a plain average pending an explicit
  future decision to adopt a named methodology.
- No new AI-confidence or sentiment model — every field is a count or ratio over real, already-existing
  data.
- No self-reported company metrics — every field derives from platform-observed data, mirroring
  `CITY_LIVING_ECONOMY.md`'s (CQ-10) `BusinessTier` "never a vanity metric" discipline.

## Related documents

`docs/CUSTOMER_JOURNEY.md`/`docs/QUALITY_ASSURANCE_ARCHITECTURE.md`/`docs/ENTERPRISE_VALUE_CHAIN.md`
(CQ-18 siblings), `docs/ENTERPRISE_HEALTH.md`/`docs/TERRITORIAL_ANALYTICS.md` (CQ-15/CQ-16, the
composite-snapshot pattern), `docs/ETHICS_GOVERNANCE.md`/`docs/RECOMMENDATION_PREDICTIVE_ENGINE.md`
(CQ-14, real `platform_learning` accept/reject and confidence-labeling discipline), `docs/CITY_LIVING_
ECONOMY.md` §1.3 (CQ-10, the non-vanity-metric discipline).
