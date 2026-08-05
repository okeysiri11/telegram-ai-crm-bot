# Enterprise Value Chain — Resource Orchestration

**Sprint:** CQ-18 — Architecture Research. Documentation only, `src` not modified.

**Do not duplicate:** No new allocation engine is proposed. Every resource type below already has a
real assignment mechanism somewhere in the platform; this document's job is to point a `Project`
(`PROJECT_LIFECYCLE.md`, this sprint) at each one, not build a ninth.

## 1. Per-resource mapping (brief's nine)

| Brief resource | Real assignment mechanism |
|---|---|
| Citizens | Real `Membership`/`ProjectParticipant.assignments` (Sprint 29.1/29.2) |
| Departments | Real `CalendarEvent.department` (`BUSINESS_CALENDAR.md`, CQ-17) — the one real "department" scoping field found in this engagement; reused rather than adding a second |
| Assets | Real `AssetOwnership`/`assetRuntime.move()` (`DIGITAL_TWIN_STANDARDS.md`, CQ-16) |
| AI Agents | Real `PersonalAiAssistant` registry (`PERSONAL_AI.md`, CQ-12); broader `aiAgentRuntime` remains frontend-simulated (CG-8 finding, restated) |
| Budgets | Real `Deal.amount`/`.profit`/`.commission` (`ENTERPRISE_VALUE_CHAIN.md`, this sprint) — a project's budget is copied once from its originating `Deal`, not tracked in a second ledger |
| Time | Real `DealStage.sla_hours` (`ENTERPRISE_VALUE_CHAIN.md` §1) is the one real per-stage time-budget precedent in the codebase; real `CalendarEvent.start_datetime`/`end_datetime` for scheduled work |
| Buildings | Real `SpatialEntity: kind: "building"` + `BuildingOccupancy` (`REGIONAL_DIGITAL_TWIN.md`/`DAILY_OPERATIONS_MODEL.md`) |
| Vehicles | Real `LifeVehicle` (`DAILY_OPERATIONS_MODEL.md`, Sprint 29.2) |
| External Partners | Real `Relationship`/`BusinessProfile` (Sprint 29.0) |

## 2. `ResourceAllocation` (SPEC) — one shape, reused per resource kind

```ts
// SPEC — a thin pointer record, not a duplicate resource store. Mirrors the real DealTask's
// assigned_to pattern (deal_pipeline_engine.py) generalized across all nine resource kinds.
interface ResourceAllocation {
  id: string;
  projectId: string;             // real Project.id (PROJECT_LIFECYCLE.md)
  resourceKind: "citizen" | "department" | "asset" | "ai_agent" | "budget"
              | "time" | "building" | "vehicle" | "external_partner";
  resourceRef: string;            // real entity id — Membership.id, AssetProfile.id, LifeVehicle.id, etc.
  allocatedAt: string;
  releasedAt?: string;
}
```

Each `resourceKind` resolves against the real registry already cited in §1 — `ResourceAllocation` never
stores citizen/asset/vehicle data itself, only the pointer and the allocation window.

## 3. Allocation conflicts — reuse real scoping, don't add a scheduler

Double-booking a building or vehicle across two projects is detected by querying existing
`ResourceAllocation` rows for overlapping `[allocatedAt, releasedAt)` windows on the same
`resourceRef` — a query, not a new conflict-resolution engine. Real `spatialPermissions`/
`AssetPermissionScope` (`DIGITAL_TWIN_STANDARDS.md`, CQ-16) already gate *who* can allocate a given
resource; this document adds no new permission check.

## Non-goals

- No new resource registry for any of the nine kinds — every one already has a real owner.
- No second budget ledger — `ResourceAllocation`'s budget kind points at the real `Deal` amount,
  copied once, never recalculated independently.
- No new scheduling/conflict engine — conflict detection is a query over `ResourceAllocation`'s own
  real allocation windows.

## Related documents

`docs/PROJECT_LIFECYCLE.md` (CQ-18 sibling, the `Project` this allocates against), `docs/ENTERPRISE_
VALUE_CHAIN.md` (CQ-18 sibling, real `Deal`/`DealStage.sla_hours`), `docs/BUSINESS_CALENDAR.md` (CQ-17,
real `department` field), `docs/DIGITAL_TWIN_STANDARDS.md` (CQ-16, real `AssetOwnership`/permission
scopes), `docs/PERSONAL_AI.md` (CQ-12), `docs/DAILY_OPERATIONS_MODEL.md` (CQ-17, real `LifeVehicle`/
`BuildingOccupancy`).
