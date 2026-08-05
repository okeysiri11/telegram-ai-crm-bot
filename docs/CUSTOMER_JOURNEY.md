# Enterprise Value Chain — Customer Journey

**Sprint:** CQ-18 — Architecture Research + UX Research. Documentation only, `src` not modified.

**Do not duplicate:** `docs/ENTERPRISE_VALUE_CHAIN.md` (this sprint) already mapped the sales-side
stages onto the real `DealPipelineStageCode` engine. This document is the same journey viewed from the
customer's side, plus the two stages (Feedback, Loyalty) the sales pipeline doesn't cover at all.
`docs/EBN_COMMUNICATION.md` (CQ-10) and `docs/DAILY_OPERATIONS_MODEL.md` §1 (CQ-17) already found real
customer contact is thin for anyone without a `BusinessProfile` — restated, not re-derived.

## 1. Per-stage mapping (brief's nine)

| Brief stage | Real/SPEC mapping |
|---|---|
| Discovery | Real City search/discoverability via `Company Card` (`ENTERPRISE_BUSINESS_NETWORK.md` §2, CQ-10) for B2B; no real discovery path for a non-partner individual customer — same gap `DAILY_OPERATIONS_MODEL.md` §1 flagged for Customer Visits |
| Communication | Real `Deal.customer_id` (`ENTERPRISE_VALUE_CHAIN.md`, this sprint) links a deal to a real `User`; actual channel is real `NOTIFICATION_CHANNELS.md` (Email/Telegram/SMS/Push/WebSocket/Webhook/Corporate Chat) |
| Proposal | Real `DealPipelineStageCode.VIEWING` (`ENTERPRISE_VALUE_CHAIN.md` §3) |
| Negotiation | Real `DealPipelineStageCode.NEGOTIATION` |
| Agreement | Real `DealPipelineStageCode.DOCUMENTS`/`PAYMENT` |
| Delivery | Real `DealPipelineStageCode.DELIVERED` + real `vehicle_assigned`/`MovementKind` (`DAILY_OPERATIONS_MODEL.md`) |
| Feedback | **Absent** — confirmed this sprint by direct search: no real NPS/CSAT/satisfaction field exists anywhere in `database/models/` or `platform_predictive_intelligence`. Fully SPEC |
| Support | Real `ServiceOrder` (automotive-vertical-only, `ENTERPRISE_VALUE_CHAIN.md` §1) |
| Loyalty | Real, vertical-scoped — `docs/CPL_LOYALTY_CALENDAR.md`'s real Loyalty Center (bonus balance, accrual/spend history, loyalty level, personal offers) and Membership Center (renewal recommendations), cafe/beauty vertical only |

## 2. `CustomerFeedback` (SPEC) — the one new entity this document proposes

```ts
// SPEC — deliberately minimal. No sentiment-analysis engine implied; a plain rating + optional text,
// same discipline ETHICS_GOVERNANCE.md (CQ-14) applied to confidence labeling: don't imply more
// sophistication than a stored number provides.
interface CustomerFeedback {
  id: string;
  dealId?: string;                // real Deal.id, when feedback follows a specific transaction
  projectId?: string;              // real Project.id (PROJECT_LIFECYCLE.md), when following project delivery
  customerId: string;              // real Deal.customer_id / User.id
  rating: number;                  // 1-5, plain — no NPS/CSAT methodology implied unless a future
                                    // sprint deliberately adopts one
  comment?: string;
  submittedAt: string;
}
```

## 3. Loyalty generalization — a recommendation, not a redesign

`CPL_LOYALTY_CALENDAR.md`'s real Loyalty/Membership Center is the strongest real precedent for
cross-vertical loyalty; this document recommends generalizing its `module` scoping (mirroring
`Deal.module`/`CalendarEvent.module`'s established pattern) rather than building a second loyalty
concept for non-cafe/beauty verticals. Not designed further here — a future sprint's explicit choice.

## Non-goals

- No sentiment-analysis or NPS-methodology engine — `CustomerFeedback.rating` is a plain number.
- No second loyalty system — recommends generalizing the real CPL Loyalty Center, not replacing it.
- No new customer-discovery engine for non-partner individuals — the gap is named, not solved.

## Related documents

`docs/ENTERPRISE_VALUE_CHAIN.md`/`docs/PROJECT_LIFECYCLE.md` (CQ-18 siblings), `docs/EBN_
COMMUNICATION.md` (CQ-10), `docs/DAILY_OPERATIONS_MODEL.md` §1 (CQ-17, the non-partner customer gap),
`docs/CPL_LOYALTY_CALENDAR.md` (real), `docs/NOTIFICATION_CHANNELS.md` (real),
`docs/ETHICS_GOVERNANCE.md` (CQ-14, the honesty-in-scoring discipline reused in §2).
