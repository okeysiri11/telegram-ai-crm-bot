# Enterprise Operations — Operational Notifications

**Sprint:** CQ-17 — Architecture Research. Documentation only, `src` not modified.

**Do not duplicate:** Three real notification vocabularies already exist. This document composes them
for the brief's operational categories; it does not add a fourth.

## 1. The three real, unreconciled notification vocabularies (new finding)

| Vocabulary | Real values | Where |
|---|---|---|
| Legacy per-vertical categories | `NOTIFICATION_CATEGORIES = {crypto_otc, agro_trading, law, drone, cafe_beauty, calendar, ai_assistant}`, `NOTIFICATION_PRIORITIES = (INFO, WARNING, CRITICAL)` | `database_legacy.py:5904-5914` |
| Unified enterprise comms | `docs/NOTIFICATION_CENTER.md` (real, `/api/enterprise-comms/v1/center` — "single publish entry... classified, routed, queued, delivered") + `docs/NOTIFICATION_CHANNELS.md` (real, Email/Telegram/SMS/Push/WebSocket/Webhook/Corporate Chat, critical priority fans out to four channels) | `services/notification_center.py:14-96` |
| Frontend delivery/display | `NotificationKind: in_app \| toast \| alert \| task \| ai \| workflow \| info \| warning \| success \| error \| system \| runtime \| mention \| job`; `NotificationBucket: unread \| mentions \| warnings \| errors \| success \| jobs \| all` | `src/web/src/notifications/notificationStore.ts:3-38` |

None of these three is a strict superset of the others, and **none of the brief's seven operational
categories exist as a named value in any of them** — this is a genuine gap, not a false-friend naming
collision like CQ-16's Digital Twin finding. The right fix is composition (each brief category maps to
an existing priority/kind, tagged with a business-domain label), not a fourth taxonomy.

## 2. Per-category mapping (brief's seven)

| Brief category | Composition |
|---|---|
| Critical Alerts | Real `NOTIFICATION_PRIORITIES.CRITICAL` (legacy) → real Channel fan-out (Telegram/SMS/Push/Email, `NOTIFICATION_CHANNELS.md`) — already fully real, no new mechanism |
| Business Opportunities | **New, SPEC** — sourced from the real Recommendation Engine (`RECOMMENDATION_PREDICTIVE_ENGINE.md`, CQ-14), delivered as frontend `NotificationKind: "ai"` at `INFO`/`WARNING` priority — a routing rule, not a new category enum value |
| Meeting Reminders | Real `CalendarEvent.remind_before`/`reminder_minutes` (`BUSINESS_CALENDAR.md`, this sprint) is already the real trigger source; delivered as `NotificationKind: "in_app"` or `"toast"` |
| Workflow Status | Real `NotificationKind: "workflow"` **already exists** — sourced from real `workflow_executed`/`workflow_completed` `LifeEvent`s (`DAILY_OPERATIONS_MODEL.md`) |
| Asset Changes | **New, SPEC** — sourced from real `assetRuntime` events (`DIGITAL_TWIN_STANDARDS.md`, CQ-16), delivered as `NotificationKind: "system"` |
| Partner Requests | Sourced from the real Partnership state machine (`EBN_PARTNERSHIP_SYSTEM.md`, CQ-10, request/accept/trust-tier transitions) — delivered as `NotificationKind: "alert"` at `WARNING` priority (a partner request awaiting response is exactly what `alert` already models) |
| Citizen Updates | Sourced from real `Membership`/presence changes (`CITIZEN_ORGANIZATION_MEMBERSHIP.md`, CQ-12) — delivered as `NotificationKind: "mention"` when the update names the viewing citizen, `"info"` otherwise |

## 3. Composition, not a fourth taxonomy (SPEC)

```ts
// SPEC — a business-domain tag layered on top of the real NotificationKind/priority pair,
// never a replacement for either.
interface OperationalNotificationTag {
  businessCategory:
    | "critical_alert" | "business_opportunity" | "meeting_reminder"
    | "workflow_status" | "asset_change" | "partner_request" | "citizen_update";
  kind: NotificationKind;        // real, frontend — unchanged
  priority?: "INFO" | "WARNING" | "CRITICAL"; // real, legacy backend — unchanged
}
```

## Non-goals

- No fourth notification taxonomy, delivery pipeline, or channel router — every category composes the
  three real systems in §1.
- No change to any real `NotificationKind`/`NOTIFICATION_CATEGORIES`/priority enum — `businessCategory`
  is an additive tag, not a replacement field.

## Related documents

`docs/NOTIFICATION_CENTER.md`/`docs/NOTIFICATION_CHANNELS.md`/`docs/NOTIFICATION_TEMPLATES.md` (real),
`docs/DAILY_OPERATIONS_MODEL.md`/`docs/BUSINESS_CALENDAR.md` (CQ-17 siblings, real event/reminder
sources), `docs/RECOMMENDATION_PREDICTIVE_ENGINE.md` (CQ-14), `docs/EBN_PARTNERSHIP_SYSTEM.md` (CQ-10),
`docs/CITIZEN_ORGANIZATION_MEMBERSHIP.md` (CQ-12), `docs/DIGITAL_TWIN_STANDARDS.md` (CQ-16, `assetRuntime`).
