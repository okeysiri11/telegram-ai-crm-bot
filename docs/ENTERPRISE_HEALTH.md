# Enterprise City — Enterprise Health Model

**Sprint:** CQ-15 — Architecture Research + Governance Design. Documentation only, `src` not modified.

**Do not duplicate:** `healthService`/`RuntimeHealthId` (CG-4/CG-6) already implement real Infrastructure
Health. `ENTERPRISE_BUSINESS_NETWORK.md` §3.3 (CQ-10) already implements real Company verification/
compliance tiers. `ETHICS_GOVERNANCE.md` (CQ-14) already established the governance posture this
document's one sensitive item (Citizen Wellbeing) must satisfy.

## 1. Per-health-dimension mapping (brief's eight)

| Brief dimension | Real/SPEC source |
|---|---|
| Organization Health | Real `BusinessProfile.trust_level`/`verification_status` (Sprint 29.0) composed with `Membership` activity count (`ENTERPRISE_ECONOMY.md` §2, CQ-13) |
| Project Health | Real `AutomationEngine` task status (Sprint 28.9) — `failed`/`retrying` ratio |
| Financial Health | Real `BusinessForecastEngine`/`RiskIntelligence` (`platform_predictive_intelligence`, CQ-14) — **not** connected to the real `DIGITAL_ASSET_TREASURY.md` (Sprint 18.4), per `DIGITAL_ASSETS.md`'s explicit non-integration decision (CQ-13) — Financial Health here means business-forecast health, not real treasury/portfolio health |
| Operational Health | Real `healthService`/`RuntimeHealthId` (CG-4/CG-6) |
| AI Health | Real `AI_AGENT_GOVERNANCE.md` (Sprint per its own version string — Agent Health, Performance Metrics, real) |
| Citizen Wellbeing Indicators | **New, and the one item this document declines to design as a scoring system** — see §2 |
| Infrastructure Health | Real `healthService`, same as Operational Health — this document does not split them into two data sources, only two dashboard groupings |
| Security Health | Real `permissionManager`/`roleManager` + `database/models/compliance.py`'s real `ComplianceRiskProfile` (CQ-10/CG-6) |

## 2. Citizen Wellbeing Indicators — the one item this document constrains rather than designs

`RECOMMENDATION_PREDICTIVE_ENGINE.md` §2.2 (CQ-14) already flagged "Citizen Productivity" as needing
an explicit non-surveillance constraint before any implementation. This document extends that same
caution to "Wellbeing": **no per-citizen wellbeing score is proposed.** Reading real per-citizen
`AuditLog` activity volume (`DIGITAL_CITIZEN.md` §0, CQ-12) to infer an individual's wellbeing would
be exactly the kind of workplace-surveillance pattern this whole engagement's "business, not
entertainment/surveillance" discipline (`CITIZEN_REPUTATION_GROWTH.md` §1.1's Friends rejection, CQ-12;
`ETHICS_GOVERNANCE.md` §2's confidence-labeling requirement, CQ-14) should reject on the same grounds.

**What this document recommends instead**: an **aggregate, anonymized** organizational signal only —
e.g., "average task completion time trending up across a department" — never a per-citizen number
attributable to one person, and never surfaced to that citizen's manager as an individual metric. If a
future sprint wants real per-citizen wellbeing features, it needs its own dedicated ethics review this
documentation-only architecture pass is not positioned to perform — flagged explicitly as an
out-of-scope decision, not silently designed around.

## 3. Composite Enterprise Health (SPEC)

```ts
// SPEC — read-only composite, mirrors ENTERPRISE_ECONOMY.md §2's "Business Value is a view, not a score" pattern
interface EnterpriseHealthSnapshot {
  companyId: string;
  organizationHealth: number;    // from real BusinessProfile/Membership fields
  projectHealth: number;          // from real AutomationEngine task status
  financialHealth: number;        // from real BusinessForecastEngine/RiskIntelligence
  operationalHealth: string;      // real HealthLevel enum (healthy/warning/critical/offline)
  aiHealth: string;                // real AI_AGENT_GOVERNANCE.md data
  securityHealth: number;          // from real ComplianceRiskProfile.risk_score, inverted
  // deliberately no citizenWellbeing field — see §2
}
```

## 4. Non-goals

- No per-citizen wellbeing score of any kind — §2's explicit, load-bearing constraint.
- No new health-check mechanism — every dimension composes a real, existing signal.
- No integration with the real Digital Asset Treasury for Financial Health — consistent with
  `DIGITAL_ASSETS.md`'s (CQ-13) explicit non-integration decision.

## Related documents

`ETHICS_GOVERNANCE.md`/`RECOMMENDATION_PREDICTIVE_ENGINE.md` §2.2 (CQ-14, the surveillance-avoidance
precedent §2 extends), `healthService`/`CITY_INTEGRATIONS.md` §3 (CG-4/CG-6), `ENTERPRISE_BUSINESS_
NETWORK.md` §3.3 (CQ-10, compliance/risk), `AI_AGENT_GOVERNANCE.md` (real), `DIGITAL_ASSETS.md`
(CQ-13, the Treasury non-integration decision).
