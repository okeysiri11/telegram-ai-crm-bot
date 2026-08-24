# Sprint AGRO 2.3 — Field production

## Result

**SPRINT AGRO 2.3 COMPLETE**

Do **not** start AGRO 2.4.

One Agro desk. Existing `/workspace/agro` + `/api/agro-ops/v1`. No second Agro subsystem. Harvest grain still goes through AGRO 2.2 truck → weighing → warehouse receipt → lot. No fake GPS / weighbridge / weather invention.

## Architectural decisions

- **Extend `services/agro_ops`, do not replace.** Mixin `AgroOpsProductionMixin` (`services/agro_ops/production.py`) on `AgroOpsService`. Storage remains generic `agro_ops_records`. New kinds (`agro_field`, `crop_season`, `field_work`, `machine`, `implement`, `material`, `material_movement`, `maintenance`, `harvest_plan`, `harvest_actual`, `field_cost`, `field_issue`) need **no SQL migration**.
- **Material ledger is movements only.** RECEIPT / ISSUE / TRANSFER / RETURN / ADJUSTMENT. Current stock = sum of movements. Direct quantity overwrite is not an API.
- **Harvest transport reuses 2.2.** `harvest_to_warehouse` creates operation + truck + weighing + `receive_operation`. It does not call 1.1 `warehouse_operation` and does not duplicate lot physical logic.
- **Costs need a source record.** `field_cost.source` + `source_id` required. Cost/ha and cost/t only when the denominator exists. Missing yield/cost/weather → `нет данных` / `null`.
- **Health stays AGRO 2.0.** `sprint: agro-2.0`, `ux_version: AGRO_2_0`, `command_center: AGRO_2_0`, `crm_version: AGRO_2_1`, `ops_version: AGRO_2_2`. Additive `production_version: AGRO_2_3`.
- **Tasks / calendar / notifications / files are existing kinds.** Field works write calendar events. Issues can call `create_task_from_entity`. Alerts emit in-app notifications. Photos use the shared file store with `capture="environment"`.
- **Nav labels avoid domain catalog A.** Operational items are «Земельный банк» and «Машины», not «Поля» / «Техника».
- **DEMO production is a separate button.** `POST /production/bootstrap` → «Загрузить демо AGRO Production». Rows labelled `[DEMO]`. Not mixed into the original «Загрузить демо AGRO» seed.

Rejected: a new `platform_fields` package, overwriting material stock, duplicating grain inventory, inventing yield/cost/weather, a parallel task system, random map colors.

## Numeric acceptance

Field 100 ha, seed receipt 20 000 kg, issue 19 800 kg → **198 kg/ha**.  
Harvest 620 t / 100 ha → **6.2 t/ha**.  
Cost 3 100 000 UAH → **31 000 UAH/ha**, **5 000 UAH/t**.

## Tests

- backend **104 passed / 0 failed** (AGRO 2.3 + 2.2 + 2.1 + 2.0 + command center + production 1.0 + operations 1.1–1.2 + 1.4–1.9 + live-data 1.3 + weather)
- frontend **65 passed / 0 failed** (`src/web` `workspace/agro`)

AUTO + CRYPTO sample (`test_auto_ops_1_8`, `test_crypto_enterprise_16_0`) green. BEAUTY `test_beauty_os_22_2` version assertions fail independently of this sprint (pre-existing).

## Migrations

None. Same `agro_ops_records`. No sqlite.

## New endpoints

Registered **before** `/{alias}` catch-all:

- `GET/POST /api/agro-ops/v1/fields`
- `GET /api/agro-ops/v1/fields/map`
- `GET /api/agro-ops/v1/fields/today`
- `GET /api/agro-ops/v1/fields/director`
- `GET /api/agro-ops/v1/fields/crop-structure`
- `GET /api/agro-ops/v1/fields/crop-costs`
- `GET /api/agro-ops/v1/fields/{id}`
- `POST /api/agro-ops/v1/fields/{id}/season`
- `POST /api/agro-ops/v1/fields/{id}/work`
- `POST /api/agro-ops/v1/fields/{id}/harvest`
- `POST /api/agro-ops/v1/fields/{id}/issue`
- `POST /api/agro-ops/v1/fields/works/{id}/status`
- `POST /api/agro-ops/v1/fields/costs`
- `POST /api/agro-ops/v1/machines`
- `POST /api/agro-ops/v1/implements`
- `POST /api/agro-ops/v1/materials`
- `POST /api/agro-ops/v1/materials/move`
- `POST /api/agro-ops/v1/materials/issue`
- `POST /api/agro-ops/v1/maintenance`
- `POST /api/agro-ops/v1/harvest/plan`
- `POST /api/agro-ops/v1/harvest/actual`
- `POST /api/agro-ops/v1/harvest/to-warehouse`
- `POST /api/agro-ops/v1/production/bootstrap`
- `POST /api/agro-ops/v1/production/alerts`

## URLs

- **DESKTOP URL:** http://127.0.0.1:5180/workspace/agro
- **MOBILE PUBLIC HTTPS URL:** https://logos-philip-environment-determination.trycloudflare.com/workspace/agro

Deep link: `/workspace/agro?view=fields&id=<uuid>`

Temporary Cloudflare tunnel to Vite `:5180` (API `:8080`). Laptop must stay on.

Live probe (this session): public page **200**, health `production_version=AGRO_2_3` / `ops_version=AGRO_2_2` / `sprint=agro-2.0`.

## Modified / new files

- `services/agro_ops/production.py` (new mixin)
- `services/agro_ops/service.py`, `rbac.py`, `command_center.py`, `desk.py`, `files.py`
- `applications/agro_enterprise/api/ops_handlers.py`, `register.py`
- `src/web/workspace/agro/AgroProductionPage.tsx` (new)
- `src/web/workspace/agro/AgroBusinessPage.tsx`, `AgroCommandCenter.tsx`, `AgroCalendarPanel.tsx`, `agroOpsNav.ts`, `agroLabels.ts`
- `src/web/src/shell/mobile/mobileShell.test.tsx`
- `tests/test_sprint_agro_2_3.py`, `src/web/workspace/agro/sprint_agro_2_3.test.tsx`
- `docs/SPRINT_AGRO_2_3_RESULT.md`

## Unresolved

- Map polygons default to layout rectangles unless a field supplies `polygon`. No GPS hardware.
- Weather risk on a field is «нет данных» until a matching `weather_observation` exists for the region.
- Plan vs actual fertilizer / СЗР / fuel / machine hours stay empty unless planned values are stored on the season.
- Material issue `cost_basis` posts `field_cost` only when the actor has `finance`.
- BEAUTY OS 22.2 version tests fail (pre-existing; this sprint did not change Beauty).
- Cloudflare quick tunnel is ephemeral.
