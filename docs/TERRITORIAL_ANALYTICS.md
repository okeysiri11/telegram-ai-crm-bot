# Regional Digital Twin — Territorial Analytics

**Sprint:** CQ-16 — Architecture Research + Intelligence Design. Documentation only, `src` not
modified.

**Do not duplicate:** `docs/BUSINESS_OBSERVATORY.md`/`docs/RECOMMENDATION_PREDICTIVE_ENGINE.md` (CQ-14)
already route business intelligence through the real, deterministic-heuristic `platform_reasoning →
planning → decision → learning` chain and the real `platform_predictive_intelligence` (hardcoded
arithmetic, `ai_may_act: False`). This document is that same intelligence, queried through a spatial
`groupBy`, never a new analytics engine. `docs/ETHICS_GOVERNANCE.md` (CQ-14)'s confidence-labeling
requirement applies unchanged to every number in §2.

## 1. Per-item mapping (brief's seven)

| Brief item | Design |
|---|---|
| Economic Activity | Real `CompanyTimelineEvent` count (Sprint 29.0) grouped by `LocationAssignment.entityId` ancestry (region/city/district) via real `spatialRegistry.ancestors()` — a groupBy, not a new metric |
| Business Density | Count of `BusinessProfile`s whose `LocationAssignment` resolves under a given territory node, divided by the real district `capacity` field already present on `Building` entities (`spatialTypes.ts:115`) |
| Growth Trends | Real `platform_predictive_intelligence`'s hardcoded trend arithmetic (CQ-14, `forecast_value = baseline*(1+0.02*(horizon_days/30))` pattern), applied per-territory instead of per-company — same formula, new groupBy key |
| Investment Opportunities | **Advisory-only, no execution** — reuses the real Recommendation Engine chain (CQ-14) and inherits `docs/INVESTMENT_LAYER.md`'s (CQ-13) explicit "zero financial fields" constraint; a territorial investment opportunity is a `Recommendation` (real shape) scoped to a territory, never a transaction |
| Traffic Analysis | Real `routingEngine.cachedCount()`/route `distanceM`/`travelTimeSec` (Sprint 29.4) aggregated per territory, plus the real City `.ec-link-line.is-flowing` traffic-visual trigger (`CITY_VISUAL_STATES.md`, CG-9) reused for territory-level traffic-volume signals |
| Infrastructure Utilization | Count of real `poi`-kind entities with `metadata.infrastructureType` (`SMART_INFRASTRUCTURE.md`, this sprint) active per territory — a count, not a new utilization model |
| Business Clusters | Real `OwnershipEdge`-pattern grouping (`"cluster_member"` edge kind, `TERRITORIAL_GOVERNANCE.md` §2, this sprint) queried per territory |

## 2. Composite Territorial Snapshot (SPEC, mirrors `EnterpriseHealthSnapshot`'s read-only pattern)

```ts
// SPEC — read-only composite, same discipline as ENTERPRISE_HEALTH.md's EnterpriseHealthSnapshot
// (CQ-15): every field traces to a real, existing signal; confidence is labeled per ETHICS_GOVERNANCE.md.
interface TerritorialAnalyticsSnapshot {
  territoryEntityId: string;          // any real SpatialEntity id (region/city/district)
  economicActivityCount: number;      // real CompanyTimelineEvent count
  businessDensity: number;            // real BusinessProfile count / real capacity
  growthTrend: { value: number; confidence: "heuristic" };  // real predictive_intelligence formula, labeled per CQ-14
  investmentOpportunities: Recommendation[];  // real shape, advisory only — never auto-executed
  trafficVolume: number;              // real routingEngine aggregate
  infrastructureUtilization: number;  // real poi count
  businessClusters: string[];         // real cluster edge query result
}
```

## 3. Non-goals

- No new forecasting/ML model — every number reuses the real, already-documented heuristic formulas
  from `platform_predictive_intelligence` and the reasoning/planning/decision/learning chain.
- No autonomous investment action — Investment Opportunities produces a `Recommendation`, never a
  transaction, per `INVESTMENT_LAYER.md`'s (CQ-13) standing constraint.
- No duplicate traffic-visualization mechanism — reuses the real City traffic-flow visual trigger
  (CG-9) at a coarser (territory) aggregation level.

## Related documents

`docs/BUSINESS_OBSERVATORY.md`/`docs/RECOMMENDATION_PREDICTIVE_ENGINE.md`/`docs/ETHICS_GOVERNANCE.md`
(CQ-14, the real intelligence chain and its governance constraints), `docs/ENTERPRISE_HEALTH.md` (CQ-15,
the composite-snapshot pattern reused in §2), `docs/INVESTMENT_LAYER.md` (CQ-13, the
no-financial-execution constraint), `docs/SMART_INFRASTRUCTURE.md`/`docs/TERRITORIAL_GOVERNANCE.md`
(CQ-16 siblings).
