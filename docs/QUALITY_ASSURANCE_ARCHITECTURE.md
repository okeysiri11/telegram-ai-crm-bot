# Enterprise Value Chain — Quality Assurance Architecture

**Sprint:** CQ-18 — Architecture Research + Governance Design. Documentation only, `src` not modified.

**Do not duplicate:** `platform_quality/` (real `QualityLibrary`: Unit/Integration/E2E/Contract/AI/
Workflow test frameworks, `RegressionSuite`, `SecurityQaFramework`, `CoverageEngine`) and
`applications/enterprise_hub/quality_assurance/` (real `QualityAssuranceSuite`: `bootstrap/run_suite/
coverage/fixtures/dashboard/certify/status`) are both real and substantial — **and both are false
friends for this brief.** Confirmed this sprint by direct search: neither has any concept of a project
review, inspection, acceptance criterion, or corrective action. They test *software*, not *deliverables*.
This document does not extend them; it names the real project-quality-gate primitive that already
exists elsewhere.

## 1. The real primitive this document builds on

`DealStageHistory.validation_passed` (`database/models/deal_pipeline_engine.py:182-208`,
`ENTERPRISE_VALUE_CHAIN.md` §1, this sprint) is a real, boolean, per-stage-transition quality gate —
every time a deal moves stages, the platform already records whether that transition passed validation.
This is architecturally identical to what brief §6 asks for at the project level; it just doesn't exist
there yet.

## 2. Per-item mapping (brief's seven)

| Brief item | Design |
|---|---|
| Reviews | SPEC — a `ProjectQualityCheck` record (§3) at a `Project` stage transition, same shape as `DealStageHistory` |
| Inspections | Same `ProjectQualityCheck` shape, `kind: "inspection"` — reuses the Business Calendar's real `"inspection"` event type recommended additively in `BUSINESS_CALENDAR.md` (CQ-17) for scheduling |
| Approvals | **Not a new gate** — reuses the real Approval Center's three gates (`EXECUTIVE_DECISION_CENTER.md` §2, CQ-15) exactly, as `PROJECT_LIFECYCLE.md` already established |
| Compliance | Real `ComplianceRiskProfile`/`ComplianceVerificationLevel` (CQ-10) — a project's compliance check queries the real company-level profile, not a duplicate project-level one |
| Acceptance | SPEC — a terminal `ProjectQualityCheck` with `kind: "acceptance"`, gating the `Delivered` transition in `PROJECT_LIFECYCLE.md`'s state machine |
| Audit Trails | **Not new** — the real `DealStageHistory` pattern generalizes directly: every `ProjectQualityCheck` is itself an immutable audit row, same discipline |
| Corrective Actions | **Absent, confirmed real gap** — no real corrective-action entity exists anywhere. SPEC: a `CorrectiveAction` linked to a failed `ProjectQualityCheck`, resolved before re-attempting the same transition |

## 3. `ProjectQualityCheck` (SPEC, generalizes the real `DealStageHistory` shape)

```ts
// SPEC — same fields as the real DealStageHistory, generalized from Deal to Project.
interface ProjectQualityCheck {
  id: string;
  projectId: string;                 // real Project.id (PROJECT_LIFECYCLE.md)
  kind: "review" | "inspection" | "acceptance";
  fromStatus: string;                  // real Project.status value
  toStatus: string;
  validationPassed: boolean;           // mirrors real DealStageHistory.validation_passed exactly
  reviewedBy: string;                  // real Membership/citizen id
  notes?: string;
  correctiveActionId?: string;         // set only when validationPassed is false
  checkedAt: string;
}

interface CorrectiveAction {
  id: string;
  qualityCheckId: string;
  description: string;
  assignedTo: string;                  // real Membership/citizen id — mirrors real DealTask.assigned_to
  status: "open" | "resolved" | "cancelled";
  resolvedAt?: string;
}
```

## Non-goals

- No extension of `platform_quality`/`quality_assurance` — both remain software-testing QA, correctly
  scoped, not repurposed for project deliverables.
- No new compliance model — reuses the real company-level `ComplianceRiskProfile` as-is.
- No fourth approval gate — Approvals route through the existing three-gate Approval Center.

## Related documents

`docs/ENTERPRISE_VALUE_CHAIN.md` §1 (CQ-18 sibling, the real `DealStageHistory` primitive this
generalizes), `docs/PROJECT_LIFECYCLE.md` (CQ-18 sibling, where `ProjectQualityCheck` gates the state
machine), `docs/EXECUTIVE_DECISION_CENTER.md` §2 (CQ-15, Approval Center), `docs/ENTERPRISE_BUSINESS_
NETWORK.md` §3.3 (CQ-10, real `ComplianceRiskProfile`), `docs/BUSINESS_CALENDAR.md` (CQ-17, the
recommended additive `"inspection"` calendar type).
