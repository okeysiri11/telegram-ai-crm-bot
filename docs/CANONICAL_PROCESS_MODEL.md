# Enterprise Process Canon — Canonical Process Model, Process Abstraction & City Visualization

**Sprint:** CQ-19 — Architecture Research + Canonical Design. Documentation only, `src` not modified.

**Do not duplicate:** This document does not propose a seventh deal/pipeline system or a seventh
workflow engine. `docs/ENTERPRISE_VALUE_CHAIN.md` §2 (CQ-18) already found six independent real deal/
pipeline implementations; `docs/ARCHITECTURE_MAP.md` §13 already found six-plus independent real
workflow engines (CG-7). This document's entire purpose is to define the **one** stage vocabulary all
of them should be read through — a canonical labeling layer, not a rewrite of any of them. `docs/
ENTITY_RECONCILIATION.md` (this sprint) is where each real system is mapped onto it in full detail.

## 1. Why a labeling layer, not a new engine

Every real system this engagement has catalogued since CG-7 already executes *some* part of this
lifecycle correctly — `deal_pipeline_engine.py` runs the sales funnel well, `platform_workflow` runs
dependency-ordered execution well, the real Approval Center (`EXECUTIVE_DECISION_CENTER.md`, CQ-15)
gates decisions well. The actual problem this sprint solves is that none of them **call the same stage
by the same name**, so no cross-system report or Cursor implementation can reason about "where is this
piece of business value right now" without bespoke per-system translation. The fix is a canonical enum
every real system's own stage maps onto — additively, via a lookup table, never by renaming a real
column.

## 2. Canonical Process Model — brief's fourteen stages

```ts
// SPEC — the canonical vocabulary. No real table is renamed to use this; every real system's own
// stage/status column maps onto one of these via ENTITY_RECONCILIATION.md's lookup tables.
type CanonicalStage =
  | "opportunity" | "lead" | "qualification" | "proposal" | "negotiation"
  | "approval" | "contract" | "project" | "execution" | "delivery"
  | "support" | "maintenance" | "renewal" | "archive";
```

| Canonical stage | Closest real precedent |
|---|---|
| Opportunity | `DealPipelineStageCode.NEW_LEAD` (pre-qualification) |
| Lead | `DealPipelineStageCode.CONTACTED` / `LeadEngineLead` (`LeadEngineStatus.NEW/CONTACTED`) |
| Qualification | `DealPipelineStageCode.QUALIFIED` / `LeadEngineStatus.QUALIFIED` — the one stage where two of the six real systems already agree on both name and position |
| Proposal | `DealPipelineStageCode.VIEWING` |
| Negotiation | `DealPipelineStageCode.NEGOTIATION` / `LeadEngineStatus.NEGOTIATION` — second point of real agreement |
| Approval | Real Approval Center (`EXECUTIVE_DECISION_CENTER.md` §2, CQ-15) — not a deal-pipeline stage in any of the six real systems today, a genuine canonical-model addition |
| Contract | `DealPipelineStageCode.DOCUMENTS` |
| Project | **New entity** — real `Project` (`PROJECT_LIFECYCLE.md`, CQ-18), bridged from a won deal via the recommended `Deal.project_id` |
| Execution | Real `ProjectParticipant`/`project_started` `LifeEvent` (Sprint 29.2) + real `workflow_executed` (Automation Engine, Sprint 28.9) |
| Delivery | `DealPipelineStageCode.DELIVERED` / `project_completed` |
| Support | Real `ServiceOrder` (automotive-only, `automotive_service.py`) |
| Maintenance | Real `ServiceOperation` (automotive-only) |
| Renewal | Real CPL Loyalty/Membership Center (cafe/beauty-only, `CPL_LOYALTY_CALENDAR.md`) |
| Archive | Real "nothing disappears" principle — stays in `CompanyTimelineEvent`/`activityTimeline`, never deleted |

## 3. Process Abstraction — six stage kinds, orthogonal to the fourteen canonical stages (brief §2)

Every canonical stage is tagged with one or more **kinds**, so a Cursor implementation knows which real
subsystem actually owns the transition — this is the axis that keeps the canonical model from
conflating "what business step is this" with "which engine executes it":

| Stage kind | Real owner |
|---|---|
| Business Stage | Real `Deal`/`BusinessProfile` fields — no execution logic, pure state |
| Technical Stage | Real `platform_workflow` (dependency-ordered execution engine) |
| Workflow Stage | Real Automation Engine (Sprint 28.9) — trigger fan-in over the Technical Stage |
| Approval Stage | Real Approval Center's three gates (`EXECUTIVE_DECISION_CENTER.md` §2) |
| Automation Stage | Real `automationEngine.runAutomation()` — fully unattended |
| Human Stage | Real `platform_workflow`'s human-task pause, or a real `Membership`-scoped manual action |

```ts
// SPEC — a canonical stage carries one or more kinds; e.g. "Approval" is both Approval Stage and
// Human Stage; "Execution" is both Technical Stage and Workflow Stage; "Renewal" is a pure Business
// Stage today (no automation exists for it in any real vertical yet).
interface CanonicalStageDefinition {
  stage: CanonicalStage;
  kinds: ("business" | "technical" | "workflow" | "approval" | "automation" | "human")[];
}
```

## 4. City Visualization (brief §7) — same real mechanism as every prior sprint

Every example is the real Life Engine → `city_update` bridge (`DAILY_OPERATIONS_MODEL.md` §3, CQ-17),
triggered by canonical-stage transitions rather than a new visualization system:

| Brief example | Canonical stage → real trigger |
|---|---|
| Project starts | `project` → `project_started` |
| Construction progresses | `execution` → `project_updated`, scoped to a `construction_site` `LocationAssignment` (CQ-16) |
| Warehouse prepares shipment | `delivery` (pre-transit) → real `MovementKind: "warehouse_to_client"` prep |
| Vehicle dispatched | `delivery` → real `vehicle_assigned` |
| Customer served | `support` → real `business_visit` |
| Support request opened | `support` → **new**, `SupportOpened` (canonical event, §6 of `PROCESS_EVENT_MODEL.md`) |

## Non-goals

- No new deal, workflow, or project execution engine — every real system named above keeps running
  exactly as it does today.
- No renaming of any real database column or enum value to match `CanonicalStage` — the canonical
  vocabulary is a lookup layer, per §1.
- No new City visualization pipeline — §4 reuses the real Life Engine bridge unchanged.

## Related documents

`docs/ENTERPRISE_VALUE_CHAIN.md`/`docs/PROJECT_LIFECYCLE.md` (CQ-18, the six-way pipeline collision and
`Project` entity this canonicalizes), `docs/ENTITY_RECONCILIATION.md`/`docs/PROCESS_STATE_MACHINE.md`/
`docs/CROSS_VERTICAL_EXTENSIONS.md`/`docs/PROCESS_EVENT_MODEL.md`/`docs/PROCESS_GOVERNANCE.md` (CQ-19
siblings), `docs/EXECUTIVE_DECISION_CENTER.md` §2 (CQ-15, Approval Center), `docs/AUTOMATION_ENGINE.md`
(real, Sprint 28.9), `docs/DAILY_OPERATIONS_MODEL.md` (CQ-17, real Life Engine bridge).
