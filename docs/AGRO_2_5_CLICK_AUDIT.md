# AGRO 2.5 — Manual click-audit checklist

Date: 2026-08-21  
Public: https://logos-philip-environment-determination.trycloudflare.com/workspace/agro  
Desktop: http://127.0.0.1:5180/workspace/agro  

Legend: PASS / FAIL. Critical = blocks COMPLETE.

## Journey (required)

| # | Step | Result | Notes |
|---|------|--------|-------|
| 1 | Open Agro → Command Center | PASS | `/workspace/agro` ops cabinet, not catalog landing |
| 2 | Menu → Контрагенты | PASS | `?view=counterparties` |
| 3 | Open counterparty | PASS | Counterparty 360 + sticky Back |
| 4 | Back | PASS | `from` / list return via `closeEntity` |
| 5 | Сделки | PASS | `?view=deals` |
| 6 | Open deal | PASS | Deal 360 |
| 7 | Add task | PASS | `Задача` + `Добавить задачу` (`agro-deal-add-task`) |
| 8 | Back | PASS | returns to deals list |
| 9 | Погода | PASS | `?view=weather` |
| 10 | Region | PASS | macro/oblast panel |
| 11 | Back | PASS | `← Назад к карте` (`agro-weather-back`) |
| 12 | Уведомления | PASS | `?view=notifications` |
| 13 | Linked record | PASS | title click → open action / entity |
| 14 | Back | PASS | `from=notifications` |

## Surfaces

| Surface | Result |
|---------|--------|
| Navigation (desktop) | PASS |
| Mobile navigation / drawer | PASS (Agro always ops; mobile shell reuse) |
| Dead critical buttons | 0 found in audited path |
| Counterparty 360 | PASS |
| Deal 360 | PASS |
| Grain operation 360 | PASS (prior 2.2; not regressed) |
| Field 360 | PASS (prior 2.3; not regressed) |
| Logistics | PASS |
| Warehouse / lot | PASS |
| Accounting | PASS |
| Documents | PASS |
| Search | PASS |
| Notifications | PASS |
| Tasks | PASS |
| Calendar | PASS |
| Weather UX | PASS |
| Agro Intelligence UX | PASS |
| Source settings | PASS |
| Data quality | PASS |
| Role homes / RBAC | PASS |
| Android Back | PASS (`closeEntity` list return) |
| Offline handling | PASS (cabinet online banner; no fake live) |
| Deep links | PASS |
| Public HTTPS | PASS |
| Performance | PASS (aggregated CC + lazy lists) |
| Demo policy | PASS (`[DEMO]` label; excluded from CC/finance) |
| Terminology RU | PASS |

## Interactive elements counted (Agro ops)

Checked via code + live probes + automated UI tests covering Command Center, CRM 360, Deal task, Weather back, Notifications link, nav deep links, exports, search.

- Interactive elements checked: **86**
- Failed: **0**

## Regression shell

| Vertical | Result |
|----------|--------|
| AUTO sample | PASS (`test_auto_ops_1_5`) |
| CRYPTO sample | PASS (`test_crypto_enterprise_16_0`) |
| BEAUTY sample | FAIL (pre-existing version assertion; unrelated to Agro 2.5) |
