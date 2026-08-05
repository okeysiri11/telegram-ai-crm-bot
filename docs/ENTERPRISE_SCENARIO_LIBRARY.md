# Enterprise Operations — Scenario Library

**Sprint:** CQ-17 — Architecture Research + Business Scenario Design. Documentation only, `src` not
modified.

**Do not duplicate:** Every scenario below is built entirely from real mechanisms already documented in
this sprint (`DAILY_OPERATIONS_MODEL.md`, `COMPANY_OPERATING_MODES.md`) and prior sprints (CQ-10
through CQ-16) — no scenario invents a new entity. Where a brief-requested vertical has no real backing
application, this document states that honestly rather than fabricating one.

## 0. Real-vs-SPEC scorecard (brief's eight)

| Scenario | Backing |
|---|---|
| Logistics Company | **Real** — `applications/port_erp` (AIS/GPS/geofence) + `applications/port_enterprise` (warehouse_distribution, multimodal_logistics incl. real rail, container_management) + real `dashboards/logistics.py` |
| IT Company | **Real** — the platform's own real reference org (`EDC_ORG_DEMO`, "ADOS Platform" project, `DAILY_OPERATIONS_MODEL.md` §0) already models exactly this company |
| Crypto Exchange | **Real** — `applications/crypto_enterprise` (market_microstructure, risk_management, market_intelligence, technical_analysis, strategy_engine) + `DIGITAL_ASSET_TREASURY.md` (Sprint 18.4) |
| Professional Services | **Real, narrow** — `applications/legal_enterprise` (document_intelligence, case_management, ai_legal_assistant, judicial_intelligence, compliance) covers the legal slice; real `EngineRoleCode.LAWYER` already exists. Accounting/consulting slices of "Professional Services" have no real vertical |
| Construction Company | **SPEC** — real anchors only: `LocationAssignmentKind: "construction_site"`, `MovementKind: "construction_to_supplier"` (both genuinely real, CQ-16/CQ-17), plus a generic, uniform capability-seed scaffold (`business_capabilities/capabilities/construction.py`) confirmed this sprint to carry no differentiated business logic |
| Medical Clinic | **SPEC** — real anchor: `SpatialDistrictKind: "medical"` (district-level only, CQ-16); same generic scaffold pattern (`healthcare.py`), no real clinic vertical |
| Manufacturing Plant | **SPEC** — real anchor: `SpatialDistrictKind: "industrial"`; generic scaffold (`manufacturing.py`); production is only real as generic `workflow_executed` events, no output/units model |
| Retail Network | **SPEC** — real anchor: `SpatialDistrictKind: "marketplace"`; no real retail vertical, no scaffold beyond the generic pattern |

## 1. Logistics Company — a day, real mechanisms only

Morning: citizens `citizen_starts_work` at the real Logistics District building. Real `port_erp`
AIS/GPS feed reports vehicle positions; a real `LifeVehicle` is `assign()`ed for a delivery run
(`vehicle_assigned` → `MovementKind: "warehouse_to_client"`). Midday: a real `CalendarEvent` of
`event_type: "delivery"` fires its `remind_before` reminder (`OPERATIONAL_NOTIFICATIONS.md`). A partner
carrier's `business_visit` is logged via `businessInteractions.record()`. Evening: `lifeEngine.arrive()`
resolves the vehicle to `"arrived"`, closing the loop; `citizen_finishes_work`.

## 2. IT Company — the platform's own reference scenario

This is the one scenario this engagement can point to a real, live demo of: `EDC_CITIZEN_OWNER`/
`EDC_CITIZEN_DEV` at `EDC_ORG_DEMO`, working `proj_platform` ("ADOS Platform") via real
`projectParticipation`. Daily rhythm: `citizen_enters_office` at Hub/Developer/AI Studio real
buildings, real `meeting_created`/`meeting_started` for standups, real `workflow_executed` for CI/build
automation (bridged from `AUTOMATION_ENGINE.md`'s Sprint 28.9 engine), `document_signed` for contract/
NDA flow. No SPEC required — every mechanism already runs in the seed data today.

## 3. Crypto Exchange — real trading + real treasury, deliberately not fused

`applications/crypto_enterprise`'s real `strategy_engine`/`risk_management`/`market_microstructure`
handle trading logic; `DIGITAL_ASSET_TREASURY.md`'s (Sprint 18.4) real wallets/blockchain registries
handle custody. Daily City-life mechanism: `workflow_executed` events for automated strategies, real
`ComplianceRiskProfile` (CQ-10) checks gating large trades — but per `ENTERPRISE_HEALTH.md`'s (CQ-15)
established non-integration line, Treasury/trading data does **not** flow into Life Engine's
general-purpose event stream; a Crypto Exchange's "Daily City Life" is deliberately thinner than its
real backend, consistent with keeping financial systems-of-record separate from City visualization.

## 4. Professional Services (Legal slice) — real vertical, narrow scope stated honestly

`applications/legal_enterprise`'s real `case_management`/`document_intelligence` drive the day: a case
deadline is a real `CalendarEvent` (`event_type: "deadline"`), court dates use the real
`COURT_CALENDAR.md` extension, client meetings are real `LifeMeeting`s. The real `LAWYER`
`EngineRoleCode` (CQ-12) is the one brief-requested professional-services role that already exists
verbatim in the platform's role taxonomy. Accounting/consulting scenarios reuse the same mechanisms
with no legal-specific backing — stated as a thinner instance of the same pattern, not a separate design.

## 5. Construction Company — SPEC, built from two real anchors

Real `LocationAssignmentKind: "construction_site"` anchors the site in the territory hierarchy; real
`MovementKind: "construction_to_supplier"` models material delivery. A "project begins" moment is a real
`project_started` `LifeEvent` scoped to that construction-site assignment — reuses
`DAILY_OPERATIONS_MODEL.md` §2's construction-beginning mapping directly. No new entity is introduced;
this scenario is thinner than Logistics/IT/Crypto because the underlying vertical scaffold is generic.

## 6. Medical Clinic — SPEC, thinnest scenario in this library

Only real anchor: `SpatialDistrictKind: "medical"` places the clinic in the city. Patient visits would
reuse the same `businessInteractions` mechanism as a customer visit — which `DAILY_OPERATIONS_MODEL.md`
§1 already flagged as partial (works only for partner `BusinessProfile`s, not walk-in individuals). This
scenario inherits that gap directly and is not designed further here.

## 7. Manufacturing Plant — SPEC

Real anchor: `SpatialDistrictKind: "industrial"`. "Production" (brief §1) reuses generic
`workflow_executed`/`workflow_completed` events with domain-specific `payload` data (e.g. unit counts) —
no new event kind, per `DAILY_OPERATIONS_MODEL.md` §1's Production row.

## 8. Retail Network — SPEC, no real vertical

Real anchor: `SpatialDistrictKind: "marketplace"`. This scenario has the least real backing of the
eight — no dedicated retail vertical, no differentiated scaffold beyond the generic capability-seed
pattern found this sprint. Named honestly as the weakest-grounded scenario rather than padded.

## Non-goals

- No new vertical application code for Construction/Medical/Manufacturing/Retail — all four remain
  documented as thin, SPEC-anchored scenarios.
- No fusion of Crypto Exchange's real financial backend into the general Life Engine event stream.

## Related documents

`docs/DAILY_OPERATIONS_MODEL.md`/`docs/COMPANY_OPERATING_MODES.md`/`docs/OPERATIONAL_NOTIFICATIONS.md`/
`docs/BUSINESS_CALENDAR.md` (CQ-17 siblings, every mechanism this library composes),
`docs/REGIONAL_DIGITAL_TWIN.md` (CQ-16, `SpatialDistrictKind`), `docs/ENTERPRISE_HEALTH.md` (CQ-15, the
financial non-integration precedent), `docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md` (CQ-12, real
`LAWYER` role).
