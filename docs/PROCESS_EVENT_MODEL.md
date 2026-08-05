# Enterprise Process Canon — Event Model

**Sprint:** CQ-19 — Architecture Research + Canonical Design. Documentation only, `src` not modified.

**Do not duplicate:** Real `LifeEventKind` (26 values, Sprint 29.2, `DAILY_OPERATIONS_MODEL.md` §0,
CQ-17) already publishes most of the execution-side events onto the real shared EventBus. This document
maps the brief's eight canonical events onto that real stream and names the two genuinely missing
bridges (Approval, Support) rather than proposing a second event bus.

## 1. Per-event mapping (brief's eight)

| Brief event | Real/SPEC mapping |
|---|---|
| ProcessCreated | **New, additive** — no real `LifeEventKind` fires when a `Deal`/`Lead` is first created today; recommend a new value, `"process_created"`, published at the same point `DealStageHistory`'s first row is written |
| StageChanged | Real `DealStageHistory` row creation (`ENTERPRISE_VALUE_CHAIN.md` §1, CQ-18) is the real audit primitive; recommend it also publish a `"stage_changed"` `LifeEvent` (additive, mirrors the existing `attachPlatformBridges()` pattern, `DAILY_OPERATIONS_MODEL.md` §3) |
| ApprovalRequested | **Missing bridge** — the real Approval Center (`EXECUTIVE_DECISION_CENTER.md` §2, CQ-15) does not currently publish to the Life Engine event stream at all. Same class of gap as the `assetRuntime`/`Membership.role` bridges `DAILY_OPERATIONS_MODEL.md` §3 already flagged |
| ApprovalGranted | Same missing bridge, the other outcome |
| ExecutionStarted | Real `project_started` (Sprint 29.2) / real `workflow_executed` (Sprint 28.9) — already real, no gap |
| ExecutionFinished | Real `project_completed`/`workflow_completed` — already real |
| SupportOpened | Real `ServiceOrderStatus.CREATED` (`automotive_service.py:32`) — real, but automotive-only, not bridged to the general Life Engine stream today |
| SupportClosed | Real `ServiceOrderStatus.CLOSED` (`automotive_service.py:38`) — same real-but-unbridged, same vertical scope |

## 2. Canonical event envelope (SPEC, mirrors the real `LifeEvent` shape exactly)

```ts
// SPEC — deliberately identical in shape to the real LifeEvent (lifeTypes.ts), so canonical
// events ride the same real bus rather than requiring a parallel subscriber model.
interface CanonicalProcessEvent {
  id: string;
  kind: "process_created" | "stage_changed" | "approval_requested" | "approval_granted"
      | "approval_rejected" | "execution_started" | "execution_finished"
      | "support_opened" | "support_closed";
  at: string;
  dealId?: string;         // real Deal.id
  projectId?: string;       // real/SPEC Project.id (PROJECT_LIFECYCLE.md, CQ-18)
  stage?: CanonicalStage;    // CANONICAL_PROCESS_MODEL.md §2
  payload: Record<string, unknown>;
}
```

Three of `kind`'s eight values (`process_created`, `stage_changed`, plus generalizing
`support_opened`/`support_closed` beyond automotive) are additive `LifeEventKind` growth, exactly like
`BUSINESS_CALENDAR.md`'s (CQ-17) recommended `"maintenance"`/`"inspection"` additions — non-breaking
enum extension, not a schema change.

## 3. Why this rides the real bus, not a new one

`lifeEventEngine.ts`'s real `publishLifeEvent()` already fans out to both `life_engine_update` and
`city_update` (`DAILY_OPERATIONS_MODEL.md` §0). Every canonical event in §2 is designed to call that
exact function — the "canonical event model" this brief asks for is a vocabulary discipline on top of
an already-real transport, not a new transport.

## Non-goals

- No second EventBus or subscriber model — every canonical event publishes through the real
  `publishLifeEvent()`.
- No generalization of `ServiceOrderStatus` performed in this pass — named as vertical-scoped, a
  future sprint's explicit decision.

## Related documents

`docs/DAILY_OPERATIONS_MODEL.md` §0/§3 (CQ-17, real `LifeEventKind`/EventBus bridge pattern),
`docs/ENTERPRISE_VALUE_CHAIN.md` §1 (CQ-18, real `DealStageHistory`), `docs/EXECUTIVE_DECISION_
CENTER.md` §2 (CQ-15, the Approval Center this bridges), `docs/CANONICAL_PROCESS_MODEL.md`/`docs/
ENTITY_RECONCILIATION.md` (CQ-19 siblings).
