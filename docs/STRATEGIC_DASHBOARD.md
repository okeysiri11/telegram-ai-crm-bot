# Enterprise City — Strategic Dashboard

**Sprint:** CQ-14 — Architecture Research + UX Research. Documentation only, `src` not modified.

**Do not duplicate:** `EXECUTIVE_DASHBOARD.md` (real, `/api/executive/v1/dashboard` — global, company,
project, department, finance, operations, and AI dashboards with KPIs/real-time metrics/activity feed)
and the real `DASHBOARD.md` profile system (CEO/Manager/Sales/Developer/Finance/Administrator, already
cited in `USER_JOURNEYS.md` §0, CG-5) are the real foundations this document extends — not
re-described.

## 1. What exists today (verified)

A real, general-purpose Executive Dashboard API already exists (`EXECUTIVE_DASHBOARD.md`) with the
exact scope breadth this brief asks for (global/company/project/department/finance/operations/AI). Six
of the brief's real Dashboard profiles were already confirmed in CG-5's research. **This document's
job is narrower than a first read of the brief suggests**: extend the real dashboard with City/
Economy/Citizen-Intelligence data (CQ-9 through CQ-14), not design a new dashboard system.

## 2. Per-item mapping

| Brief item | Status |
|---|---|
| CEO Dashboard | Real profile (`CITY_USER_JOURNEYS.md` §1, CG-5) — extend with `ENTERPRISE_ECONOMY.md`/`BUSINESS_OBSERVATORY.md` data, not a new dashboard |
| Owner Dashboard | New — closest real precedent is `EngineRoleCode.OWNER` (`CITIZEN_ORGANIZATION_MEMBERSHIP.md` §0, CQ-12) — an Owner's dashboard is proposed as the CEO Dashboard's real layout, scoped by the Owner's real `Membership` companies |
| Regional Dashboard | **SPEC, lowest priority** — no real "region" concept exists anywhere in this survey (City is percentage-space, not geo-scoped, `CITY_LIVING_ECONOMY.md` §2.1, CQ-10); would require the multi-city work that same document already flags as a real future cost, not solved here |
| Enterprise Health | Real `healthService`/`RuntimeHealthId` (CG-4/CG-6) — already wired into the real Executive Dashboard |
| Growth Indicators | Real `BusinessTier`/`BusinessProfile.trust_level` trend (`CITY_LIVING_ECONOMY.md` §1.3, CQ-10; Sprint 29.0) |
| Risk Indicators | Real `RiskIntelligence` (`platform_predictive_intelligence`, confirmed real this sprint, `RECOMMENDATION_PREDICTIVE_ENGINE.md` §2.1) |
| Business Opportunities | Real `OpportunityDetector` (same real module) |
| AI Recommendations | Real `platform_learning.RecommendationEngine` (`ENTERPRISE_INTELLIGENCE_CORE.md` §3) |

## 3. The one honest caveat this document must carry forward

`RECOMMENDATION_PREDICTIVE_ENGINE.md` §2.1 already found the frontend `predictive-intelligence` module
does not call its real backend — a Strategic Dashboard surfacing Growth/Risk/Opportunity indicators
must be built to call the **real** `platform_predictive_intelligence`/`platform_learning` APIs
directly, not the existing simulated frontend derivation, or it will silently inherit that same
disconnect this engagement has now found at nearly every AI-adjacent surface of this platform.

## 4. Non-goals

- No new dashboard engine — extends the real `EXECUTIVE_DASHBOARD.md` API.
- No new profile system — extends the real, already-documented CG-5 profiles.
- No Regional Dashboard design — explicitly deferred pending real multi-city/geo work.

## Related documents

`EXECUTIVE_DASHBOARD.md` (real), `DASHBOARD.md`/`CITY_USER_JOURNEYS.md` (CG-5, real profiles),
`RECOMMENDATION_PREDICTIVE_ENGINE.md` (real Risk/Opportunity/Recommendation sources, and the
frontend-disconnection caveat), `ENTERPRISE_ECONOMY.md`/`BUSINESS_OBSERVATORY.md` (CQ-13/14, the data
this dashboard surfaces), `CITY_LIVING_ECONOMY.md` §2.3 (CQ-10, the multi-city/region gap).
