# Enterprise Process Canon — Entity Reconciliation

**Sprint:** CQ-19 — Architecture Research + Canonical Design. Documentation only, `src` not modified.

**Do not duplicate:** This document is the full reconciliation table `docs/CANONICAL_PROCESS_MODEL.md`
promised — every real entity this engagement has found since CG-7 that models some part of the value
chain, mapped explicitly onto the canonical stage vocabulary. No entity is renamed, merged, or migrated
by this document; every mapping is additive metadata.

## 1. Deals — six real systems (restated from `ENTERPRISE_VALUE_CHAIN.md` §2, CQ-18)

| Real system | Canonical mapping approach |
|---|---|
| `deal_pipeline_engine.py` (`PipelineDeal`/`DealPipelineStageCode`) | **Recommended canonical source** — its `DealStage.allowed_next_stages` becomes the reference transition table `CanonicalStage` validates against |
| `deals.py` (`Deal`, generic + `Deal*Ext`) | `Deal.status` (free string) maps via a lookup table, not a rename |
| `deal.py` (`DealEngineDeal`/`DealStatus`) | OTC-flavored statuses (`KYC_PENDING`, `FUNDS_EXPECTED`) map onto `contract`/`execution` canonical stages — the least clean mapping of the six, flagged for careful review before any consolidation |
| `deal_engine_v1.py` | Confirmed superseded by `deal_pipeline_engine.py` (v2) — no new mapping needed, historical only |
| `lead_engine.py` (`LeadEngineLead`) | Closest 1:1 mapping — `NEW/CONTACTED/QUALIFIED/NEGOTIATION/PAYMENT_PENDING/WON/LOST` aligns almost directly with `lead/qualification/negotiation/contract` |
| `automotive_sales.py` (`Lead`/`SalesPipelineStage`) | Automotive-only, maps the same as `deal_pipeline_engine.py`'s stages with vertical-specific labels (`TEST_DRIVE` → `proposal`) |

## 2. Tasks — a new collision found this sprint: at least three independent real task concepts

| Real system | Shape | Canonical mapping |
|---|---|---|
| `database/models/tasks.py`'s `Task` | Generic, `module` field, real FK to `calendar_events.id`, **untyped, non-FK `project_id` column** (no relationship defined) — status/priority are plain strings, no enum | The intended generic task entity, per its own `module` field's apparent purpose — but currently disconnected from `Deal` entirely (no `deal_id`) and only loosely connected to a project (`project_id` isn't even a real foreign key) |
| `deal_pipeline_engine.py`'s `DealTask` | Separate table, separate `DealTaskStatus` enum, hard FK to `deal_pipeline_engine_v2_deals.id`, assignee as raw Telegram `BigInteger` (not `users.id`) | Maps to `execution`/`negotiation` canonical stages, scoped strictly to its own deal |
| Frontend `ProjectParticipant.assignments` | `string[]` — plain text labels, no structured task entity at all (`lifeTypes.ts`, Sprint 29.2) | Maps to `execution`, but is not a real task record — just free text on a participation row |

**This is a genuine new finding, not previously catalogued**: `tasks.py`'s `Task` looks exactly like
the generic entity the platform needs, but is unused by both the deal pipeline and the project/
participation model. Recommendation: **do not build a fourth task concept.** A future implementation
sprint should either (a) wire `Task.project_id` into a real FK once `Project` exists
(`PROJECT_LIFECYCLE.md`, CQ-18), and have `DealTask` become a thin deal-scoped view over `tasks.Task`,
or (b) explicitly decide to keep them separate and document why — this document does not decide for
them, per this engagement's established discipline of flagging rather than silently merging.

## 3. Workflows — seven real systems, not six: a frontend/backend split newly confirmed this sprint

`docs/ARCHITECTURE_MAP.md` §13 already catalogued six backend workflow engines
(`platform_workflow`, `platform_workflows`, `platform_ai/workflows`, `platform_workflow_intelligence`,
`src/kernel/workflow`, `applications/enterprise_hub/workflow`). This sprint confirms a **seventh,
architecturally disconnected system**: the frontend `src/web/src/runtime/workflowRuntime/` — a real,
substantial node-graph executor (`WorkflowNodeKind`: sequential/parallel/condition/loop/delay/
wait_event/ai_action/approval/http/webhook/script; `WorkflowStatus`: idle/running/paused/waiting/
completed/failed/cancelled) that composes only `commandRuntime`/`enterpriseEventBus` — **no call into
any of the six backend engines**. This is the same "real-shaped data, simulated/disconnected execution"
pattern this engagement has found repeatedly (CG-9's `cityPath` finding, CQ-14's predictive-intelligence
findings) — the frontend workflow runtime is real and runs, but is not actually the backend's workflow
engine wearing a UI.

Also confirmed this sprint: **none of the six backend engines has a tenant-configurable transition
table** — `DealStage.allowed_next_stages` (deal pipeline) is architecturally unique in the whole
platform. Recommendation: if the canonical process model needs configurable per-tenant stage
transitions (it does, per `CANONICAL_PROCESS_MODEL.md` §2), `DealStage`'s shape — not any workflow
engine's — is the pattern to generalize.

## 4. The remaining brief items (Service Orders, Maintenance, Contracts, Automation Jobs)

| Brief item | Real entity | Canonical mapping |
|---|---|---|
| Service Orders | Real `ServiceOrder` (`automotive_service.py`, automotive-only) | `support` canonical stage |
| Maintenance | Real `ServiceOperation`/`ServicePart` (same file) | `maintenance` canonical stage |
| Contracts | **No dedicated entity** (confirmed CQ-18) — closest real precedent is `DealPipelineStageCode.DOCUMENTS` plus `legal_enterprise`'s `document_intelligence` | `contract` canonical stage |
| Automation Jobs | Real `automationEngine` (Sprint 28.9) — sits atop, not inside, the six workflow engines | `execution` canonical stage, `automation` stage kind (`CANONICAL_PROCESS_MODEL.md` §3) |

## 5. Reconciliation is metadata, not migration

```ts
// SPEC — a lookup row per real system, never a rename of the real column it describes.
interface CanonicalStageMapping {
  realSystem: string;          // e.g. "deal_pipeline_engine.DealPipelineStageCode"
  realValue: string;           // e.g. "VIEWING"
  canonicalStage: CanonicalStage; // CANONICAL_PROCESS_MODEL.md §2
}
```

## Non-goals

- No merge of `tasks.Task`/`DealTask`/`ProjectParticipant.assignments` performed in this pass —
  flagged as a real decision for a future sprint, per §2.
- No bridging of the frontend `workflowRuntime` into any backend engine — named as a real
  disconnection, not solved here.
- No new tenant-configurable transition engine — `DealStage`'s real shape is recommended for reuse,
  not reimplemented.

## Related documents

`docs/ENTERPRISE_VALUE_CHAIN.md` §2 (CQ-18, the six-way deal collision), `docs/PROJECT_LIFECYCLE.md`
(CQ-18, the `Project` entity `tasks.Task.project_id` should eventually FK to), `docs/ARCHITECTURE_MAP.md`
§13 (the six backend workflow engines, now extended with the frontend seventh), `docs/CANONICAL_
PROCESS_MODEL.md`/`docs/PROCESS_STATE_MACHINE.md` (CQ-19 siblings).
