# Enterprise Operations — Operational Dashboards

**Sprint:** CQ-17 — Architecture Research + UX Research. Documentation only, `src` not modified.

**Do not duplicate:** Real, domain-keyed operational dashboards already exist
(`applications/enterprise_hub/command_center/dashboards/`). This document's core finding is that they
are organized by **business domain** (operations, construction, manufacturing, logistics, healthcare,
maritime, finance, security, ai), not by **org-chart role** (Owner, Manager, Department Head, …) — the
brief asks for the second axis, which is a real gap, not a naming collision.

## 1. What is real today

`applications/enterprise_hub/command_center/dashboards/operations.py:9-13` returns a real
`"Operational Dashboard"` blueprint: `sections: [production, warehouse, logistics, construction,
maritime, healthcare, service]`, `default_widgets: [kpi, alerts, ai_summary]`. Sibling real files in
the same directory (`construction.py`, `manufacturing.py`, `logistics.py`, `healthcare.py`,
`maritime.py`, `finance.py`, `security.py`, `ai.py`) follow the identical shape — each a domain
blueprint, not a role-scoped one. `applications/enterprise_hub/command_center/executive_dashboard.py`'s
real `ExecutiveDashboard` class is the closest real precedent for an "Owner"-level view. `src/web` has
10 real `dashboard/` subfolders (`organization-brain`, `ai-os`, `command-center`, `vertical-federation`,
`workspace`, `navigation`, `release`, `auth`, plus `src/dashboard/`'s `MissionControlStrip`/
`ExecutiveMorningBrief` and `src/live-dashboard/`) — all feature-keyed, same pattern.

## 2. Per-role mapping (brief's six) — composition over the real domain dashboards, not a new engine

| Brief role | Design |
|---|---|
| Owner | Real `ExecutiveDashboard` (`executive_dashboard.py`) + `ExecutiveMorningBrief`/`MissionControlStrip` (`src/web/src/dashboard/`) — already the closest real match, reused as-is |
| Manager | **New composition, SPEC** — the real `operations.py` blueprint's sections, filtered to the departments a `Membership.role: "manager"` (`CITIZEN_ORGANIZATION_MEMBERSHIP.md`, CQ-12) has scope over — a query filter over real blueprint data, not a new dashboard type |
| Department Head | Same composition mechanism as Manager, filtered to exactly one `department` (real field, `CalendarEvent.department`/`BUSINESS_CALENDAR.md` already carries this exact scoping concept — reused, not reinvented) |
| Project Manager | **New composition, SPEC** — real `ProjectParticipant`/`projectParticipation` (`DAILY_OPERATIONS_MODEL.md`, Sprint 29.2) already tracks `attendance`/`participationScore`/`assignments` per project; a Project Manager dashboard is a read view over that real data, filtered to projects where the viewer's role is `"lead"`/`"owner"` (real `ProjectMemberRole`) |
| Operations Center | **Real, near-exact match** — `dashboards/operations.py`'s blueprint, used directly |
| Regional Manager | **New composition, SPEC** — the same domain blueprints (`operations.py`, etc.), filtered to a `SpatialEntity` of `kind: "region"` (`REGIONAL_DIGITAL_TWIN.md`, CQ-16) rather than a single building — the one role that requires the CQ-16 territory hierarchy as a filter dimension, not just an org-role filter |

## 3. The filtering principle (SPEC, applies to all four new compositions)

```ts
// SPEC — every "new" role dashboard in §2 is the same real domain blueprint,
// scoped by one of two real dimensions already established in this engagement.
interface DashboardScope {
  domainBlueprint: "operations" | "construction" | "manufacturing" | "logistics" | "healthcare" | "maritime" | "finance" | "security" | "ai"; // real, unchanged
  scopedBy:
    | { kind: "membership_role"; role: string }          // real Membership.role
    | { kind: "department"; department: string }          // real CalendarEvent.department
    | { kind: "project"; projectId: string }              // real ProjectParticipant.projectId
    | { kind: "territory"; entityId: string };            // real SpatialEntity id (region/city/district)
}
```

No new dashboard rendering engine is proposed — this is a scope/filter object applied to the real,
existing blueprint data.

## Non-goals

- No new dashboard engine or widget system — the real `dashboards/*.py` blueprints and `src/web`
  dashboard components are reused unchanged.
- No role table — `DashboardScope.scopedBy` reuses real `Membership.role`/`department`/`projectId`/
  spatial-entity fields, never a new role enum.

## Related documents

`docs/EXECUTIVE_OPERATING_SYSTEM.md` (CQ-15, the Owner-level real dashboard composite this doesn't
repeat), `docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md` (CQ-12, real `Membership.role`), `docs/BUSINESS_
CALENDAR.md` (CQ-17 sibling, real `department` field), `docs/DAILY_OPERATIONS_MODEL.md` (CQ-17 sibling,
real `ProjectParticipant`), `docs/REGIONAL_DIGITAL_TWIN.md` (CQ-16, real territory hierarchy for
Regional Manager scoping), `docs/TERRITORIAL_GOVERNANCE.md` (CQ-16, the governance-role precedent this
mirrors).
