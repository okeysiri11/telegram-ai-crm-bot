# Sprint AGRO 2.0 — Operational Command Center

## Result

**SPRINT AGRO 2.0 COMPLETE**

One workspace. Existing `/workspace/agro` home is now **АГРО — ОПЕРАЦИОННЫЙ ЦЕНТР**. No second Agro app, no duplicate routes, no deleted records.

## Architectural decisions

- **Extend, do not replace.** Command center is mixed into `AgroOpsService` (`services/agro_ops/command_center.py`) and returned from existing `GET /api/agro-ops/v1/dashboard` as `command_center`. Legacy `cards` / `onboarding` remain.
- **No live weather/intel on dashboard load.** Compact weather uses stored `weather_observation` rows only (`_weather_rows`). Intel cards use stored reports. Missing → «Нет данных».
- **Additive search.** `GET /api/agro-ops/v1/search` registered before the kind alias catch-all.
- **Previous AGRO 2.0 (weather desk / settings IA) is unchanged.** Health still reports `sprint: agro-2.0` / `ux_version: AGRO_2_0`. Command center is `command_center: AGRO_2_0`.
- **Roles.** Added `agro_logistics` and `agro_warehouse` without removing existing RBAC.

Rejected: a second dashboard route, a new `platform_*` package, generating intel/weather on home load.

## Acceptance

| Gate | Status |
| --- | --- |
| Dashboard | **PASS** |
| Desktop | **PASS** |
| Mobile | **PASS** |
| Public HTTPS | **PASS** |
| Summary | **PASS** |
| Важно сегодня | **PASS** |
| Quick actions | **PASS** |
| Deals | **PASS** |
| Deliveries | **PASS** |
| Warehouses | **PASS** |
| Prices | **PASS** |
| Weather | **PASS** |
| Agro intelligence | **PASS** |
| Tasks/calendar | **PASS** |
| Notifications | **PASS** |
| Global search | **PASS** |
| Attachments | **PASS** |
| RBAC | **PASS** |
| Legacy regression | **PASS** |

Dead buttons: **0** (command-center surface). Quick actions open one sheet; existing create forms are reused.

DEMO remains labelled **РЕЖИМ DEMO** when demo data is loaded.

## Tests

- backend **77 passed / 0 failed** (command center + AGRO 2.0 weather + production 1.0 + operations 1.1–1.9 + weather + live-data 1.3)
- frontend **52 passed / 0 failed** (`src/web` `workspace/agro`)

## Migrations

None. Same Postgres `agro_ops_records` registry. No sqlite.

## URLs

- **DESKTOP URL:** http://127.0.0.1:5180/workspace/agro
- **MOBILE PUBLIC HTTPS URL:** https://logos-philip-environment-determination.trycloudflare.com/workspace/agro

Temporary Cloudflare tunnel. Laptop must stay on. Existing ops drawer and `?view=*` deep links unchanged.

## What shipped

1. Home = command center: summary cards (desktop grid / mobile horizontal scroll), Важно сегодня, быстрые действия, pipeline, logistics, warehouses, prices, weather macros, intel conclusions, tasks/calendar, bell, search.
2. Real DB aggregates only. Empty → `0` / `Нет данных`. Manual vs market price labels: Рыночная / Контрагент / Наша цена / Ручная.
3. One create sheet (`AgroQuickCreateSheet`) — not nine new forms.
4. Deal pipeline click → `/workspace/agro?view=deals&pipeline=…`
5. Weather «Открыть карту» → existing weather screen.
6. Diagnostics stay in Настройки → ИСТОЧНИКИ ДАННЫХ / ДИАГНОСТИКА. Home shows a one-line source status + Подробнее.
7. Global search across counterparties, deals, contracts, documents, deliveries, warehouses, crops, tasks, payments, VIN/plate.
8. Dossier tabs: payments, notes, margin (if role allows). Shipment/warehouse drawer: Связи.
9. Attachments: paperclip, HEIC/HEIF, camera capture on mobile.
10. Roles: Owner/Director/Manager/Accountant/Logistics/Warehouse/Viewer — dashboard block order adapts; finance amounts masked without `finance`.

## Modified files

- `services/agro_ops/command_center.py` (new)
- `services/agro_ops/service.py`
- `services/agro_ops/rbac.py`
- `services/agro_ops/files.py`
- `applications/agro_enterprise/api/ops_handlers.py`
- `applications/agro_enterprise/api/register.py`
- `src/web/workspace/agro/AgroCommandCenter.tsx` (new)
- `src/web/workspace/agro/AgroQuickCreateSheet.tsx` (new)
- `src/web/workspace/agro/AgroGlobalSearch.tsx` (new)
- `src/web/workspace/agro/AgroBusinessPage.tsx`
- `src/web/workspace/agro/agroLabels.ts`
- `src/web/workspace/agro/AgroDossierDrawer.tsx`
- `src/web/workspace/agro/AgroOpsDrawer.tsx`
- `src/web/workspace/agro/AgroSettingsPanel.tsx`
- `src/web/workspace/business-ops/BusinessCabinetShell.tsx`
- `src/web/workspace/agro/sprint_agro_command_center.test.tsx` (new)
- `src/web/workspace/agro/sprint_agro_production_1_0.test.tsx`
- `tests/test_sprint_agro_command_center.py` (new)

AGRO 2.1 was not started.

**STOP.**
