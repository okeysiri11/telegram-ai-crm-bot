# AUTO 1.5 COMPLETE

Director analytics and finance for Auto OS on existing `services/auto_ops` (mixin, not a new platform). Frozen `/api/auto/v1` unchanged. Agro, Legal, Crypto, Beauty, Travel untouched. AUTO 1.6 not started.

**Workspace:** Рабочее пространство → Авто → Аналитика / Финансы / Обзор (`/workspace/auto?view=analytics`, `view=finance`)  
**API:** `/api/auto-ops/v1` (private, org + workspace scoped; AUTO 1.0–1.4 contracts kept, analytics routes additive)

---

## Completion checklist

| Gate | Result |
|------|--------|
| Vehicle economics table + filters/sort | **PASS** |
| Profitability ranking (sold only; unsold = ПРОГНОЗ) | **PASS** |
| Forecast profit labeled ПРОГНОЗ | **PASS** |
| Finance summary cards + periods | **PASS** |
| Cash flow ACTUAL/EXPECTED | **PASS** |
| Cash gap only with known opening balance | **PASS** |
| Ledger accounts (no crypto custody) | **PASS** |
| Receivables | **PASS** |
| Sales / managers / logistics analytics | **PASS** |
| Customs / repair / documents / funnel | **PASS** |
| Lifecycle from status history | **PASS** |
| «На сегодня» from records | **PASS** |
| Optional AI explains supplied metrics | **PASS** |
| Telegram `/report` + analytics/risks/cashflow | **PASS** |
| Optional alerts via outbox | **PASS** |
| Completeness KNOWN/PARTIAL/UNKNOWN | **PASS** |
| Click-through + CSV export | **PASS** |
| Audit WEB/TELEGRAM/API | **PASS** |
| RBAC director/accountant/manager | **PASS** |
| Tenant isolation | **PASS** |
| DEMO fixtures `confirm_demo` | **PASS** |
| Tests | **69 passed / 0 failed** (backend 51 = AUTO 1.0 ×9 + 1.1 ×8 + 1.2 ×8 + 1.3 ×11 + 1.4 ×9 + 1.5 ×6; frontend 18 = 1.0 ×5 + 1.1 ×2 + 1.2 ×2 + 1.3 ×3 + 1.4 ×2 + 1.5 ×4) |

---

## Architectural decisions

1. **Mixin `AutoOpsAnalyticsMixin`, not a new `platform_*`.** Aggregations sit on `AutoOpsService` over existing vehicles, expenses, CRM, logistics, customs bags.

2. **No invented balances or realized profit.** Running cash balance and «кассовый разрыв» appear only when a finance account has a recorded `balance`. Unsold vehicles never enter strongest/weakest ranking; forecast is labeled ПРОГНОЗ.

3. **Completeness qualifies profit.** Missing broker/customs/repair notes produce PARTIAL/UNKNOWN and «Предварительная прибыль» vs «Финальная прибыль».

4. **Telegram reuses AUTO 1.4.** `/report` is richer; buttons bind `ao:` callbacks. Quiet hours were not in 1.4 — alerts reuse member `enabled` + outbox. No second bot.

5. **CSV only.** Project has no spreadsheet exporter in Python requirements; XLSX is not claimed.

Rejected: a new analytics engine; fake opening cash; ranking unsold as realized profit; crypto custody; starting AUTO 1.6.

---

## Routes (additive)

- `GET /analytics/director|economics|ranking|finance|cashflow|receivables|sales|managers|logistics|suppliers|customs|repair|documents|funnel|risks`
- `GET /analytics/export?kind=&format=csv`
- `POST /analytics/ai` `POST /analytics/demo` `POST /analytics/alerts`
- `GET|POST /finance/accounts`

---

## Limitations

- Local Alembic may still fail on older AUTO `%s` revisions; memory fallback remains valid.
- Logistics port/customs duration is UNKNOWN unless status history / shipment timestamps exist.
- AI is optional: backend calculates recommendations; LLM only explains the supplied JSON.

STOP AFTER AUTO 1.5. DO NOT START AUTO 1.6.
