# Enterprise Value Chain & City Visualization

**Sprint:** CQ-18 — Architecture Research + Business Process Modeling. Documentation only, `src` not
modified.

**Do not duplicate:** This document's central finding is that the *sales half* of the brief's Value
Chain (Opportunity → Lead → Proposal → Contract) already has a real, mature, tenant-configurable
pipeline engine — `database/models/deal_pipeline_engine.py` ("Deal Pipeline Engine v2 — stages,
history, tasks, comments, SLA") plus the generic `database/models/deals.py`'s `Deal` model. The
*post-sale half* (Support → Maintenance → Renewal) has only a vertical-specific real precedent
(`automotive_service.py`), not a generalized one. This document maps the brief onto both honestly
rather than inventing a parallel generic pipeline.

## 1. What is real today

| Real symbol | Shape | File |
|---|---|---|
| `Deal` | Generic, tenant/module-scoped: `module`, `deal_type`, `status` (`NEW`/…), `owner_id`/`manager_id`/`customer_id`/`partner_user_id`, `amount`/`currency`/`profit`/`commission` | `deals.py:23-60` |
| Per-vertical `Deal*Ext` | `DealAgroExt`/`DealAutoExt`/`DealLegalExt`/`DealDroneExt`/`DealFinanceExt`/`DealLogisticsExt` — the same generic-entity-plus-vertical-extension pattern `BUSINESS_CALENDAR.md`'s `CalendarEvent.module` (CQ-17) already established | `deals.py:95-169` |
| `DealPipelineStageCode` | `NEW_LEAD → CONTACTED → QUALIFIED → VIEWING → NEGOTIATION → RESERVED → DOCUMENTS → PAYMENT → DELIVERED`, plus terminal `LOST` | `deal_pipeline_engine.py:33-44` |
| `DealStage` | **Real, tenant/company-configurable** state machine — `sort_order`, `sla_hours`, `is_terminal`, `allowed_next_stages: JSONB` | `deal_pipeline_engine.py:146-179` |
| `DealStageHistory` | Real audit trail — `from_stage`/`to_stage`, `validation_passed`, `changed_by` | `deal_pipeline_engine.py:182-208` |
| `DealTask`/`DealComment` | Real per-deal task/comment tracking | `deal_pipeline_engine.py:211+` |
| `Lead` (automotive-specific) | A **second**, narrower, vertical-scoped pipeline: `SalesPipelineStage` (`NEW_LEAD/CONTACTED/TEST_DRIVE/NEGOTIATION/RESERVED/CONTRACT_SIGNED/PAID/DELIVERED`), `LeadSource`, `budget` | `automotive_sales.py:29-97` |
| `ServiceOrder`/`WarrantyRecord`/`ServiceHistory` | Real post-sale support/maintenance/warranty tracking — **automotive-only**, no generalized equivalent | `automotive_service.py:31-70,222` |

## 2. The largest pipeline collision found in this engagement — at least six real systems

This sprint's research surfaced more independent "deal/pipeline" implementations than any prior
duplication finding (exceeding CQ-15's four Command Centers and CQ-16's four Digital Twins):

| Real system | Stage/status vocabulary | Flavor |
|---|---|---|
| `deals.py`'s `Deal` | `status: str`, free-text, default `"NEW"` | Generic, module+vertical-extension pattern |
| `deal.py`'s `DealEngineDeal` | `DealStatus`: `NEW/ASSIGNED/KYC_PENDING/FUNDS_EXPECTED/FUNDS_RECEIVED/PROCESSING/COMPLETED/CANCELLED/DISPUTE` | Exchange/OTC-flavored |
| `deal_engine_v1.py`'s `DealEngineV1Deal` | `NEW/IN_PROGRESS/PAYMENT_PENDING/PAYMENT_RECEIVED/COMPLETED/CANCELLED` | Generic v1, superseded |
| `deal_pipeline_engine.py`'s `PipelineDeal` | `DealPipelineStageCode`: `NEW_LEAD/CONTACTED/QUALIFIED/VIEWING/NEGOTIATION/RESERVED/DOCUMENTS/PAYMENT/DELIVERED/LOST` | **Generic v2, tenant-configurable, richest** (real SLA/history/tasks) |
| `lead_engine.py`'s `LeadEngineLead` | `LeadEngineStatus`: `NEW/CONTACTED/QUALIFIED/NEGOTIATION/PAYMENT_PENDING/WON/LOST` | Closest to a textbook `new/qualified/negotiation/won/lost` funnel |
| `automotive_sales.py`'s `Lead` | `SalesPipelineStage`: `NEW_LEAD/CONTACTED/TEST_DRIVE/NEGOTIATION/RESERVED/CONTRACT_SIGNED/PAID/DELIVERED` | Automotive-vertical-specific |
| `crm_pipeline_boards_v1.py` | `CrmPipelineBoardStage`/`CrmPipelineBoardTransition` | Generic, tenant-configurable board + transition log |

Six-to-seven independently-evolved real systems model the same underlying concept (a staged sales
funnel with SLA/history), none unified. This is the same shape of finding as CQ-10's verification-tier
collision and CQ-16's Digital Twin collision, just larger. **Recommendation, not a resolution**: new
value-chain work should build against `deal_pipeline_engine.py`'s `DealPipelineStageCode`/`DealStage`
(the most mature: real tenant-configurable `allowed_next_stages`, real SLA, real audit history),
treating the other five as legacy/vertical-scoped predecessors — mirroring exactly how
`platform_enterprise_digital_twin` was recommended over legacy EDT (CQ-16 §3). No dedicated
`Opportunity`, `Proposal`, or `Contract` entity exists in any of the six systems — those brief terms are
synthesis labels over real `DealPipelineStageCode` stages (§3), not separate entities to build.

## 3. Value Chain — brief's eleven stages mapped

| Brief stage | Real/SPEC mapping |
|---|---|
| Opportunity | Real `DealPipelineStageCode.NEW_LEAD`/`CONTACTED` — pre-qualification |
| Lead | Real `Deal` + `DealPipelineStageCode.QUALIFIED` |
| Proposal | Real `DealPipelineStageCode.VIEWING` is the closest existing stage (automotive-flavored "viewing the product"); a non-automotive `Deal.module` would use a differently-labeled but structurally identical `DealStage` row — the real `allowed_next_stages` JSONB already supports this without schema change |
| Contract | Real `DealPipelineStageCode.DOCUMENTS` |
| Project | **The real gap** — `Deal`'s pipeline ends at `DELIVERED`/`LOST`; there is no real field linking a won `Deal` to a `ProjectParticipant`/project record (`DAILY_OPERATIONS_MODEL.md`, Sprint 29.2). SPEC: an additive `Deal.project_id` (nullable FK), populated when a deal reaches `DELIVERED` and execution begins — see `PROJECT_LIFECYCLE.md` (this sprint) for the project side |
| Execution | Real `ProjectParticipant`/`projectParticipation` (Sprint 29.2) — thin (no budget/status fields), detailed in `PROJECT_LIFECYCLE.md` |
| Delivery | Real `DealPipelineStageCode.DELIVERED` + real `MovementKind`/`vehicle_assigned` (`DAILY_OPERATIONS_MODEL.md`) for physical delivery |
| Support | Real, but **vertical-scoped only** — `ServiceOrder` (automotive). No generalized cross-vertical Support entity exists |
| Maintenance | Real, vertical-scoped — `ServiceOperation`/`ServicePart` (automotive) |
| Renewal | **Real, vertical-scoped only** — `docs/CPL_LOYALTY_CALENDAR.md`'s real Membership Center already models "remaining visits, expiry, renewal recommendations" (cafe/beauty vertical). Same shape as Support/Maintenance: real, but not generalized beyond one vertical |
| Long-term Relationship | Real `BusinessProfile.trust_level`/`CompanyTimelineEvent` (Sprint 29.0) already accumulate exactly this signal over time — reused, not reinvented |

## 4. City Visualization (brief §8) — the same real mechanism, once more

Every example in the brief's §8 is the real Life Engine → `city_update` mechanism
(`DAILY_OPERATIONS_MODEL.md` §3, Sprint 29.2), triggered by value-chain events rather than daily-ops
events — this section states the trigger mapping, not a new visualization system:

| Brief example | Real trigger |
|---|---|
| New construction | `Deal` reaching `DELIVERED` for a `module: "construction"` deal → `project_started` `LifeEvent` at the linked `construction_site` (`REGIONAL_DIGITAL_TWIN.md`, CQ-16) |
| Deliveries | Real `vehicle_assigned`/`DealPipelineStageCode.DELIVERED` |
| Completed projects | `project_completed` `LifeEvent` |
| Growing headquarters | Real `BusinessTier` visual-prominence mechanism (`CITY_LIVING_ECONOMY.md` §1.3, CQ-10), driven by accumulated won `Deal`s |
| Warehouse activity | Real `MovementKind: "warehouse_to_client"` |
| Service visits | **New trigger** — a `ServiceOrder` status change publishing `business_visit` (extends `DAILY_OPERATIONS_MODEL.md`'s existing bridge pattern, additive) |
| Infrastructure improvements | SPEC — ties to `SMART_INFRASTRUCTURE.md`'s (CQ-16) still-mostly-absent Utilities/Airports/Energy categories; not designed further here |

## Non-goals

- No new generic sales-pipeline engine — `DealPipelineStageCode`/`DealStage` is real and sufficient;
  this document only recommends it over the legacy `Lead.pipeline_stage`.
- No generalization of `ServiceOrder`/`WarrantyRecord` performed in this pass — named as
  vertical-scoped, left for a future sprint's explicit decision.
- No new City visualization pipeline — every trigger in §4 reuses the real Life Engine bridge.

## Related documents

`docs/PROJECT_LIFECYCLE.md`, `docs/CUSTOMER_JOURNEY.md`, `docs/BUSINESS_VALUE_METRICS.md` (CQ-18
siblings), `docs/DAILY_OPERATIONS_MODEL.md` (CQ-17, real Life Engine bridge), `docs/CITY_LIVING_
ECONOMY.md` §1.3 (CQ-10, `BusinessTier`), `docs/REGIONAL_DIGITAL_TWIN.md` (CQ-16, `construction_site`),
`docs/BUSINESS_CALENDAR.md` (CQ-17, the generic-entity-plus-module-extension pattern this document's
`Deal` finding mirrors).
