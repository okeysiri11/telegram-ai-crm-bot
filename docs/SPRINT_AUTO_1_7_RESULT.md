# Sprint AUTO 1.7 — result

## What shipped

Logistics operating layer on Auto: assignment slots, optional suggested tasks on stage change, audit completeness, tenant/workspace filters, RBAC (including forwarder), logistics search + global Auto search, honest tracking provider settings, event source/confirmation, vehicle logistics history, and director logistics averages.

Primary surface:

- Mixin extensions in `services/auto_ops/logistics.py` + catalog `services/auto_ops/logistics_catalog.py`
- Tracking/providers/history mixin `services/auto_ops/logistics_ops.py`
- Additive `/api/auto-ops/v1/logistics/providers*`, `/logistics/shipments/{id}/tracking`, `/logistics/vehicles/{id}/history`
- Frontend: tracking actions, provider settings, history, global search, analytics averages

## Architectural decisions

| Decision | Why | Rejected |
|---|---|---|
| Extend `AutoOpsLogisticsMixin` + small ops mixin | Reuse 1.1 shipments/events | New `platform_*` logistics service |
| Manager-required policy **default off** | 1.1 create-without-manager must keep working | Hard-require manager on every active shipment |
| Suggested tasks create open todos only | Spec: optional, no irreversible auto-actions | Auto-clear customs / auto-deliver / auto-status |
| Provider check = env-name present | Honest; no fake live AIS | Calling invented third-party AIS |
| Secrets never leave the API | Only `api_key_env` name + configured flag | Returning API key values |
| Manager shipment scope only for a real principal | Frontend still sends role as `X-Principal`; 1.1 tests omit it | Filtering the desk to empty for every manager |
| `auto_forwarder` additive | Operational slot without finance | Replacing manager or inventing 20 sidebar items |
| Workspace default = organization_id | Existing org-bag records stay visible | Breaking 1.0–1.6 lists |

## Intentionally deferred / limitations

- No live AIS / live container polling. «Проверить» validates configuration (enabled + env var set).
- Suggested tasks never change vehicle, customs, or payment status.
- Manager company-wide profit remains hidden; assigned operational transport cost is policy-gated (`manager_see_assigned_transport_cost`, default on).
- Accountant still cannot change operational status unless `accountant_may_change_status` is enabled (default off) **and** they have write permission.
- Provider rows persist in the Auto ops bag (Postgres when the kind exists, otherwise memory fallback).

## Build / lint / tests

- Backend: **65 passed / 0 failed** (`test_auto_ops_1_0` … `1_7`; 1.7 adds 6 tests; 1.0–1.6 sprint sets accept `AUTO_1.7`).
- Frontend: **24 passed / 0 failed** (1.0×5 + 1.1×2 + 1.2×2 + 1.3×3 + 1.4×2 + 1.5×4 + 1.6×3 + 1.7×3).
- Frozen `/api/auto/v1` unchanged. Agro / Crypto / Beauty / Legal / Travel untouched.

## Follow-ups

AUTO 1.8 is out of scope for this sprint.
