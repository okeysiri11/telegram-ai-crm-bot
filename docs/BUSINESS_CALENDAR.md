# Enterprise Operations — Business Calendar

**Sprint:** CQ-17 — Architecture Research. Documentation only, `src` not modified.

**Do not duplicate:** A real, unified business calendar already exists — `database/models/calendar.py`'s
`CalendarEvent` plus `services/calendar_service.py`'s "Unified CalendarService for hub modules, tasks
and future notifications." This document maps the brief's calendar vocabulary onto that real system; it
does not propose a second calendar. `docs/EBN_COMMUNICATION.md` (CQ-10) and `docs/DIGITAL_LIFE.md`
(CQ-12) already found no real *cross-company shared* calendar exists — restated in §2, not re-derived.

## 1. What is real today

`CalendarEvent` (`database/models/calendar.py:22-58`) is a substantial, real, already-generalized
model: `title`, `module` (per-vertical scoping), `event_type`, `creator_id`/`owner_id`/
`assigned_user_id`/`responsible_user_id`, `start_datetime`/`end_datetime`, `remind_before`/
`reminder_minutes`, `repeat_rule`, `status`, `priority`, `department`, `visibility`. Real
`CALENDAR_EVENT_TYPES` (`database_legacy.py:3610-3613`): `general, task, meeting, deadline, reminder,
agro, agro_task, payment, delivery`. Real `CALENDAR_MODULES` scope events per vertical (crypto, agro,
legal, drone, beauty, …). Real access control via `services/calendar_access.py` (department/visibility
ACL). Real vertical extensions already exist: `services/crypto_erp_calendar.py`,
`services/agro_erp_calendar.py`, and `applications/legal_enterprise/case_management/calendar.py` (a
real court calendar, `docs/COURT_CALENDAR.md`).

## 2. Per-item mapping (brief's eight)

| Brief item | Real mapping |
|---|---|
| Meetings | Real `event_type: "meeting"`; also independently real-time-tracked by `LifeMeeting` (`DAILY_OPERATIONS_MODEL.md`, this sprint) — a scheduled meeting becomes a `CalendarEvent` first, then a `LifeMeeting` when it actually starts. These are complementary, not duplicate: `CalendarEvent` is the plan, `LifeMeeting` is the real-time state |
| Deadlines | Real `event_type: "deadline"` |
| Projects | **Not a distinct calendar `event_type`** — a project's milestones are real `Task`s (FK'd from `CalendarEvent`, per the model's `TYPE_CHECKING` import of `database.models.tasks.Task`) linked to `ProjectParticipant` (`lifeTypes.ts`, Sprint 29.2), not a new calendar concept |
| Maintenance | **Not a distinct real `event_type`** — recommend an additive value, `"maintenance"`, to `CALENDAR_EVENT_TYPES` (non-breaking enum growth, same pattern `REGIONAL_DIGITAL_TWIN.md` used for `SpatialDistrictKind`) |
| Deliveries | Real `event_type: "delivery"` **already exists** — bridges directly to the real `vehicle_assigned`/`MovementKind: "warehouse_to_client"` (`DAILY_OPERATIONS_MODEL.md`) once a delivery's scheduled time arrives |
| Inspections | **Absent** — no real `event_type` or precedent found; recommend an additive `"inspection"` value, same non-breaking pattern as Maintenance |
| Approvals | **Not a calendar concept** — real approvals already flow through the Approval Center's three real gates (`EXECUTIVE_DECISION_CENTER.md` §2, CQ-15); a calendar entry for an approval deadline reuses `event_type: "deadline"`, it does not need its own type |
| Business Events | Real `event_type: "general"` plus `module` scoping already covers arbitrary business events; no new type needed |

## 3. The one real gap: cross-organization calendar sharing

`EBN_COMMUNICATION.md` §2 (CQ-10) already found no real shared calendar/meeting system between two
independent companies exists; `DIGITAL_LIFE.md` (CQ-12) reached the same conclusion from the citizen
side. This document's contribution is narrowing that gap precisely: the **per-organization** calendar
is real and rich (`CalendarEvent`, above); what's missing is a `CalendarEvent` visible across two
different `owner_id` tenants for a shared meeting/deadline — real `visibility` (`DEPARTMENT`, etc.) is
an intra-tenant concept only. SPEC: a `visibility: "partner_shared"` value, gated by the real
`Relationship`/`Visibility` composition `DIGITAL_TWIN_STANDARDS.md` §3 (CQ-16) already designed for
Public/Private Layers — reusing that composition, not inventing a fourth access model.

## Non-goals

- No new calendar engine, model, or service — `CalendarEvent`/`calendar_service.py` remain
  authoritative.
- No merge of Calendar and `LifeMeeting` into one entity — kept complementary (plan vs. real-time
  state), per §2.
- No new approval-scheduling mechanism — Approvals reuse the real `deadline` type and the real
  Approval Center, never a calendar-native approval flow.

## Related documents

`docs/DAILY_OPERATIONS_MODEL.md` (CQ-17 sibling, `LifeMeeting`/delivery bridge), `docs/EBN_
COMMUNICATION.md` (CQ-10, the cross-org gap this restates), `docs/DIGITAL_LIFE.md` (CQ-12),
`docs/EXECUTIVE_DECISION_CENTER.md` §2 (CQ-15, Approval Center), `docs/DIGITAL_TWIN_STANDARDS.md` §3
(CQ-16, the Visibility composition reused for partner-shared events), `docs/COURT_CALENDAR.md` (real,
the legal-vertical calendar extension).
