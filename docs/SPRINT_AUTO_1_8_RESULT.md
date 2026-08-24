# Sprint AUTO 1.8 — result

## What shipped

Customs operating layer on Auto: Telegram `/customspay`, `/customsdoc`, `/customsstatus`; canonical 1.2 status IDs with spec aliases and a real transition guard; director/admin historical correction with reason + timestamp + audit; tenant/workspace filters; search by VIN/declaration/plate/client/broker/document; director customs averages from real records; landed-cost breakdown without double-counting; profit reused from AUTO 1.5 economics (sold vehicles only); customs expenses enter existing cash flow; CSV export kinds; printable «Сводка по растаможке».

Primary surface:

- Catalog `services/auto_ops/customs_catalog.py` — aliases, `transition_allowed`, charges
- Mixin extensions in `services/auto_ops/customs.py` + ops mixin `services/auto_ops/customs_ops.py`
- Additive `/api/auto-ops/v1/customs/cases/{id}/summary`, `/payments`, `/payments/{id}/confirm`
- Telegram commands in the existing bot (`telegram.py` + `telegram_auth.py`)
- Frontend: summary, correction, analytics averages, landed cost, CSV export

## Architectural decisions

| Decision | Why | Rejected |
|---|---|---|
| Keep 1.2 status IDs; map spec names as aliases | 1.2 tests skip `DOCUMENTS_PREP` → `PAYMENT_PENDING` | Replacing the 1.2 catalog |
| HTTP allows forward skips; Telegram only immediate next (+ hold/reject) | Desk speed vs. bot safety | Same skip rules on both channels |
| Backward jumps only with correction payload + director/admin | Spec: no `REGISTERED` → `DECLARATION_SUBMITTED` without audit | Silent historical edits |
| `/customspay` creates a **planned** expense; confirm is a second step | Spec: do not silently mark payment confirmed | Reusing `/pay` receipts (client money in) |
| Landed cost splits existing expense rows | No second ledger; no double-count | Adding calc snapshot on top of expenses |
| Cash flow = existing expense/receipt events | Spec: do not duplicate Payments/Expenses | Customs-only cash bag |
| CSV export via `analytics_export` | Reuse 1.5/1.6 infrastructure | Fake XLSX |

## Intentionally deferred / limitations

- No live Гостаможня / НБУ calculator. Rates remain organization-configured.
- CSV only (tabular / XLSX-friendly). No binary XLSX writer.
- Telegram status picker does not offer forward skips; the HTTP desk still can.
- Accountant cannot change operational status. Correction is director/admin with reason + timestamp.
- Duration averages require `cleared_at` or `registered_at`; open cases do not invent days from `updated_at`.

## Build / lint / tests

- Backend: **71 passed / 0 failed** (`test_auto_ops_1_0` … `1_8`; 1.8 adds 6 tests; 1.0–1.7 sprint sets accept `AUTO_1.8`).
- Frontend: **27 passed / 0 failed** (1.0×5 + 1.1×2 + 1.2×2 + 1.3×3 + 1.4×2 + 1.5×4 + 1.6×3 + 1.7×3 + 1.8×3).
- Frozen `/api/auto/v1` unchanged. Agro / Crypto / Beauty / Legal / Travel untouched.

## Follow-ups

AUTO 1.9 is out of scope for this sprint.
