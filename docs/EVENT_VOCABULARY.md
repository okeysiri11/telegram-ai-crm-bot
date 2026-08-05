# Enterprise Semantic Model — Event Vocabulary

**Sprint:** CQ-20 — Architecture Research + Ontology Design. Documentation only, `src` not modified.

**Do not duplicate:** Five real, independently-authored event-name vocabularies already exist. This
document is a canonical suffix dictionary layered over all five, following exactly the same
"composition, not a fourth taxonomy" discipline `OPERATIONAL_NOTIFICATIONS.md` (CQ-17) already applied
to notification categories.

## 1. The five real event-name vocabularies

| Vocabulary | Case style | Example values | Where |
|---|---|---|---|
| `LifeEventKind` | snake_case | `citizen_enters_office`, `meeting_started`, `project_completed` | Sprint 29.2, `DAILY_OPERATIONS_MODEL.md` (CQ-17) |
| `BUS_EVENT_NAME` (Life Engine → EventBus bridge) | PascalCase | `CitizenMoved`, `MeetingCreated`, `WorkflowCompleted` | `lifeEventEngine.ts:16-34` |
| `AssetEventName` | PascalCase | `AssetCreated`, `AssetAssigned`, `AssetTransferred`, `AssetRetired`, `AssetArchived` | `assetTypes.ts:86-95` (`DIGITAL_TWIN_STANDARDS.md`, CQ-16) |
| `SpatialEventName` | PascalCase | `LocationChanged`, `EnteredBuilding`, `BuildingRegistered` | Sprint 29.4, `REGIONAL_DIGITAL_TWIN.md` (CQ-16) |
| `CityVisEventName` | PascalCase | `BuildingUpdated`, `MeetingFinished`, `WorkflowExecuted`, `SceneRebuilt` | Sprint 29.5, `CROSS_SYSTEM_SEMANTIC_MAPPING.md` (this sprint) |

Real convergence already exists without top-down enforcement: `"CitizenMoved"` appears identically in
both `BUS_EVENT_NAME` and `CityVisEventName`; `"AssetMoved"` appears identically in both
`SpatialEventName` and `CityVisEventName`. This document's canonical suffixes formalize a pattern the
platform's own engineers already gravitate toward independently.

## 2. Per-suffix mapping (brief's ten)

| Brief suffix | Real precedent | Note |
|---|---|---|
| Created | `AssetCreated`, `MeetingCreated` — real, consistent | — |
| Updated | `CompanyUpdated`, `DistrictUpdated`, `AssetUpdated` — real, consistent | — |
| Deleted | **Absent from all five** — no real vocabulary uses "Deleted." `AssetEventName` uses `AssetRetired` instead | Consistent with this engagement's "nothing disappears" principle (`CITY_LIVING_ECONOMY.md`, CQ-10) — recommend **not** adding a `Deleted` suffix anywhere; `Retired`/`Archived` are the real, deliberate vocabulary for end-of-life |
| Assigned | `AssetAssigned`, `AssignedWorkspace`, `VehicleAssigned` — real, consistent | — |
| Transferred | `AssetTransferred` — real, singular precedent | Only Assets currently model transfer; other entity kinds have no real equivalent yet |
| Approved | **Absent from all five** — the real Approval Center (`EXECUTIVE_DECISION_CENTER.md` §2, CQ-15) does not currently publish any event | Confirms `PROCESS_EVENT_MODEL.md`'s (CQ-19) already-identified missing bridge — restated, not re-derived |
| Rejected | **Absent**, same gap as Approved | — |
| Started | `meeting_started`/`MeetingStarted` — real | — |
| Completed | `project_completed`/`WorkflowCompleted` real, **but** `CityVisEventName` uses `MeetingFinished` for the same concept a meeting reaching its end — a real, small naming inconsistency (`Finished` vs. `Completed`) worth flagging | Recommend `Completed` as the canonical suffix, `Finished` as an alias (`SEMANTIC_VERSIONING.md` §2, this sprint) |
| Archived | `AssetArchived` — real, singular precedent | Same gap as Transferred — only Assets currently model archiving explicitly, though the broader "nothing disappears" behavior is universal |

## 3. `CanonicalEventSuffix` (SPEC) — a naming convention, not a new bus

```ts
// SPEC — a documentation convention for future additive event names, not a new publish mechanism.
// Every canonical event still rides the real enterpriseEventBus (DAILY_OPERATIONS_MODEL.md §0, CQ-17).
type CanonicalEventSuffix =
  | "Created" | "Updated" | "Assigned" | "Transferred"
  | "Approved" | "Rejected" | "Started" | "Completed" | "Archived";
// "Deleted" deliberately excluded — see §2.
```

New event names in any of the five real vocabularies (or a future sixth) should end in one of these
nine suffixes, in PascalCase, matching the four PascalCase vocabularies' existing convention —
`LifeEventKind`'s snake_case style is the one exception, already established and not worth migrating.

## Non-goals

- No sixth event bus or subscriber model — every event rides one of the five real vocabularies'
  existing real transport.
- No `Deleted` suffix introduced anywhere — deliberately excluded per the nothing-disappears principle.
- No rename of `MeetingFinished` — proposed as an alias of `Completed`, not replaced.

## Related documents

`docs/DAILY_OPERATIONS_MODEL.md` §0 (CQ-17, real `LifeEventKind`/`BUS_EVENT_NAME`), `docs/DIGITAL_
TWIN_STANDARDS.md` (CQ-16, real `AssetEventName`), `docs/REGIONAL_DIGITAL_TWIN.md` (CQ-16, real
`SpatialEventName`), `docs/CROSS_SYSTEM_SEMANTIC_MAPPING.md` (CQ-20 sibling, real `CityVisEventName`),
`docs/PROCESS_EVENT_MODEL.md` (CQ-19, the Approval/Support bridge gaps restated in §2),
`docs/OPERATIONAL_NOTIFICATIONS.md` (CQ-17, the composition discipline this mirrors),
`docs/SEMANTIC_VERSIONING.md` (CQ-20 sibling, the alias mechanism for `Finished`/`Completed`).
