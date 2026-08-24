# SPRINT AGRO 2.0 UX / WEATHER RESULT

## STATUS

**COMPLETE. STOP after AGRO 2.0.**

Weather map, regional narratives, crop impact, business-language desk, risk/opportunity cards, 24h change block, reorganized Agro settings, and diagnostics moved off the intelligence home screen. Existing desk (`services/agro_ops`, `/api/agro-ops/v1`, `src/web/workspace/agro`) was extended. No second AGRO app.

Live org: `org-agro-live-14`. Health: **`agro-2.0`**. Pipeline remains **`AGRO_1_9`**. UX version: **`AGRO_2_0`**.

UI: http://127.0.0.1:5180/workspace/agro?view=weather  
Settings: http://127.0.0.1:5180/workspace/agro?view=settings

No Alembic revision. Crypto / Legal / Beauty / Cafe unchanged.

---

## WHAT SHIPPED

### Dead buttons / history / sources

- Analytics **История анализов → Открыть** loads `/analytics/{id}` (`data-testid=agro-analytics-open-{id}`).
- Intel history **Открыть** sets the stored report immediately and refreshes from `/reports/{id}`.
- Source actions remain live: **Проверить**, **Последние данные**, **Открыть источник**, **Настройки**.

### Technical UI moved

- Main intel/analytics screens use business copy: «Получены свежие данные по погоде, валюте, торговле и рынкам.»
- HTTP 403/521, JSON 404, timeout, metadata_only, pipeline_version are not shown on the intelligence home table.
- Coverage, health counts, quality, anomalies stay under **Подробнее** (testids preserved).
- Full HTTP/probe diagnostics: **Настройки → ДИАГНОСТИКА**.

### Weather map

- Nav: **Погода**.
- Schematic Ukraine SVG with oblast points from Open-Meteo lat/lon (`odesa` 46.48,30.73; `lviv` 49.84,24.03).
- Click oblast → drawer: temperature, rain, 7-day forecast, monthly outlook, risk, crop impact.
- Missing data is explicit. Climate comparison never invented: **«Недостаточно данных для сравнения с климатической нормой.»**

### Regions and crop impact

- Macro narratives: Юг / Центр / Запад / Север / Восток.
- Crop-weather for Пшеница, Кукуруза, Подсолнечник, Ячмень, Рапс, Соя.
- Risk matrix: Region × Wheat/Corn/Sunflower/Barley/Soy. Cell click explains the level.
- Linked from **Культуры**.

### Business desk

- **РИСКИ СЕГОДНЯ**, **ВОЗМОЖНОСТИ** («Потенциальная возможность», never guaranteed profit), **ЧТО ИЗМЕНИЛОСЬ ЗА 24 ЧАСА**.
- Morning/evening reports add compact 10-section `business_sections` + **Подробнее**. Original `sections` kept.

### Settings IA

Tabs: ОБЩИЕ, ИСТОЧНИКИ, АГРОРАЗВЕДКА, АНАЛИТИКА, ПОГОДА, РАСПИСАНИЕ, УВЕДОМЛЕНИЯ, ДИАГНОСТИКА.

- Intel: refresh frequency, regions, commodities, source priority, confidence, report length, morning/evening toggles.
- Analytics: Кратко / **Стандартно** / Подробно + specialist enable/disable.
- Weather: primary/backup provider, horizon, crop impact, source status.
- Schedule: human times (05:45 Обновление данных, …). Cron under **Расширенные настройки**.

### Large screens

Weather map `w-full` / `min-h` grows at xl/2xl. Intelligence and settings use `overflow-x-hidden` / `max-w-[1920px]`. Source tables scroll inside settings diagnostics only.

---

## ARCHITECTURAL DECISIONS

- **Extend `services/agro_ops`**, not a new `platform_*` package. Mixins: `AgroOpsWeatherMixin`, `AgroOpsDeskSettingsMixin`.
- **Do not bump pipeline.** `pipeline_version` stays `AGRO_1_9` so 1.9 rebuild/report contracts hold. Health sprint is `agro-2.0`; `ux_version` is `AGRO_2_0`.
- **Climate normals are never invented.** Open-Meteo 7-day forecast is not a 30-year normal. History UI always states the missing-normal sentence unless a real prior-period baseline exists.
- **Regional weather is live Open-Meteo per oblast**, stored as `weather_observation` with `oblast_id` / `series_id=open-meteo-{oblast}-tmax|precip`. Existing Kyiv provider series unchanged.
- Rejected: fake static oblast temperatures; showing cron as the primary schedule UI; putting HTTP errors on the intel home table.

---

## TESTS

Backend (1.0–1.9 + 2.0): **65 passed**  
Frontend (`src/web` workspace/agro): **45 passed**

New: `tests/test_sprint_agro_2_0.py`, `src/web/workspace/agro/sprint_agro_2_0.test.tsx`.

---

## CHECKLIST

- dead buttons fixed
- history actions fixed
- source actions fixed
- technical UI moved
- weather map implemented
- regions supported
- weather provider used (Open-Meteo)
- crop impact implemented
- risk cards implemented
- settings reorganized
- tests passed
