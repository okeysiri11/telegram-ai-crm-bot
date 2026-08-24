# AGRO 2.6 COMPLETE

**Sprint:** AGRO 2.6 — Fields / Crops / Sowing / Harvest / Machinery  
**Date:** 2026-08-21  
**Status:** COMPLETE — do not start AGRO 2.7 automatically.

Extends AGRO 2.3 production + AGRO 2.5 UX. Does not rebuild AGRO 2.0–2.5 modules. Harvest continues to use AGRO 2.2 warehouse receipt (`harvest_to_warehouse`).

---

## 1. What was implemented

| Area | Delivery |
|------|----------|
| **Поля** | Full field registry (code, area, region/district/locality, coords, cadastre, owner, ownership type, lease dates/cost, status, crops, responsible, notes). Create / edit / archive / Field 360. Actions: document, operation, go to sowing/harvest. |
| **Карта** | Map-provider abstraction (`AGRO_MAP_PROVIDER` / `AGRO_MAP_API_KEY` — no hardcoded secrets). Fallback SVG scheme when not configured. Compact card on click → Field 360. Geo markers when lat/lng present. |
| **Культуры** | Agronomic catalog (`agro_crop`): name, variety/hybrid, producer, season, yields, moisture, quality, notes. Create / edit / archive. Trading desk panel retained. |
| **Посевы** | Operational sowing workflow with statuses (План → … → Завершён / Отменён), costs, auto cost/ha + total. Persisted as `field_work` + season link. |
| **Техника** | Machinery registry: types, statuses, VIN, service dates, Machine 360, list/search/filter. |
| **Работы** | Work orders linking field + machinery + operator; lifecycle via existing status transitions; materials/fuel/cost. |
| **Урожай** | Harvest records with gross/net/moisture/quality/warehouse; yield/ha + estimated value; **На склад (2.2)** without duplicating warehouse logic. |
| **Экономика** | Field 360 financial summary from real `field_cost` + harvest records only (no fake KPIs). |
| **Command Center** | `kpis_26` / `production/kpis-26`: fields, hectares, active fields, sowing/harvest progress, machinery active/service, open works, season cost/harvest. |
| **Mobile** | Same modules in ops drawer: Поля, Культуры, Посевы, Техника, Работы, Урожай. Touch ≥44px, card layouts, sticky primary actions, no horizontal overflow. |
| **Search/filters** | q / status / field / crop / date / machinery / operation across list APIs. |

---

## 2. Backend tests

| Suite | Result |
|-------|--------|
| `tests/test_sprint_agro_2_6.py` | **PASSED** (5) |
| `tests/test_sprint_agro_2_3.py` | **PASSED** (updated health → `AGRO_2_6`) |

---

## 3. Frontend tests

| Suite | Result |
|-------|--------|
| `workspace/agro/sprint_agro_2_6.test.tsx` | **PASSED** |
| `workspace/agro/sprint_agro_2_3.test.tsx` | **PASSED** (nav labels updated) |
| `src/shell/mobile/mobileShell.test.tsx` | **PASSED** (Поля/Посевы/Урожай now ops drawer items) |

---

## 4. New / changed API routes

Prefix: `/api/agro-ops/v1`

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/fields/{id}` | Update field registry |
| POST | `/fields/{id}/archive` | Archive field |
| GET/POST | `/agro-crops` | Agronomic crop catalog |
| POST | `/agro-crops/{id}` | Update / archive crop |
| GET/POST | `/sowings` | List / create sowing |
| POST | `/sowings/{id}/status` | Sowing status |
| GET/POST | `/works` | List / create work orders |
| GET/POST | `/machines` | List / create machinery |
| GET | `/machines/{id}` | Machine 360 |
| POST | `/machines/{id}` | Update machine |
| GET/POST | `/harvests` | List / record harvest |
| GET | `/production/kpis-26` | Command Center KPIs |

Enhanced existing: `GET /fields/map` (+ `map_provider`, markers), `GET /fields/{id}` (+ economics, ownership), health `production_version=AGRO_2_6`.

---

## 5. Database / storage changes

- No SQL migration.
- New entity kind in memory/registry bag: `agro_crop`.
- Extended payloads on existing kinds: `agro_field`, `field_work` (sowing extras), `machine`, `harvest_actual`.
- Persistence: same agro_ops durable store as 2.3.

---

## 6. Desktop verification

- URL: `http://127.0.0.1:5180/workspace/agro`
- Nav: Поля / Культуры / Посевы / Техника / Работы / Урожай open real modules.
- Field 360: economics, RU tabs, archive, to sowing/harvest, harvest→warehouse.
- Health: `production_version=AGRO_2_6`, prior sprint markers intact.

---

## 7. Mobile verification

- Public HTTPS: `https://logos-philip-environment-determination.trycloudflare.com/workspace/agro` (HTTP 200)
- Drawer includes 2.6 modules; workspace drawer still works.
- Same API-backed workflows as desktop.

---

## 8. Dead buttons count

**0 intentional decorative dead buttons** in AGRO 2.6 surfaces (create/save/status/archive/to-warehouse/nav all wired).

---

## 9. Remaining issues

- External map tiles require env (`AGRO_MAP_PROVIDER` + key where needed); fallback SVG is active by default.
- Postgres greenlet warnings in local tests when async patch persist races — in-memory bag still holds truth for ops (same class of noise as prior agro sprints).
- Auto field-cost lines from sowing/works require finance permission + `source`/`source_id` (enforced).

---

## 10. Current desktop URL

`http://127.0.0.1:5180/workspace/agro`

---

## 11. CURRENT WORKING MOBILE HTTPS URL

`https://logos-philip-environment-determination.trycloudflare.com/workspace/agro`

---

## 12. Changed files

- `services/agro_ops/production_26.py` (new)
- `services/agro_ops/service.py` (mixin MRO, kind `agro_crop`, catalogs, CC KPIs)
- `applications/agro_enterprise/api/ops_handlers.py`
- `applications/agro_enterprise/api/register.py`
- `src/web/workspace/agro/agroOpsNav.ts`
- `src/web/workspace/agro/AgroOps26Modules.tsx` (new)
- `src/web/workspace/agro/AgroBusinessPage.tsx`
- `src/web/workspace/agro/AgroProductionPage.tsx`
- `src/web/workspace/agro/AgroCommandCenter.tsx`
- `src/web/workspace/agro/sprint_agro_2_3.test.tsx`
- `src/web/workspace/agro/sprint_agro_2_6.test.tsx` (new)
- `src/web/src/shell/mobile/mobileShell.test.tsx`
- `tests/test_sprint_agro_2_3.py`
- `tests/test_sprint_agro_2_6.py` (new)
- `docs/SPRINT_AGRO_2_6_RESULT.md` (this file)

---

## 13. Recommended scope for AGRO 2.7

- GPS polygon import / real OSM-Leaflet layer when provider configured
- Seasonal planning board (Gantt) across fields
- Machinery utilization vs planned hours dashboard
- Deeper CRM deal ↔ field season economics rollup
- Offline-capable mobile queue for field photos / work status

**STOP.** Do not start AGRO 2.7 in this sprint.

---

## Architectural decisions

1. **Extend `AgroOpsProductionMixin` via `production_26.py`**, not a new platform package — preserves 2.3 kinds and 2.2 warehouse path.
2. **Mixin MRO:** `AgroOpsProduction26Mixin` listed before `AgroOpsProductionMixin` so overrides (field registry, harvest enrich, map meta) win.
3. **Sowing stored as `field_work` with `work_type=sowing`** — avoids a disconnected entity while exposing dedicated sowing API/UI.
4. **Agronomic `agro_crop` separate from trading `crop` directory** — desk trading and field planning stay compatible without merging domains.
5. **Ops nav labels renamed to Поля/Техника/…** — domain catalog A leftovers (Товары, Полив, ИИ-помощник) remain excluded from the mobile drawer.
