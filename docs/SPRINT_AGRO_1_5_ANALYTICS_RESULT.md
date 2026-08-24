# SPRINT AGRO 1.5 — ANALYTICS RESULT

## STATUS

**COMPLETE.** Analytics desk is operational on the existing agro_ops pipeline.

PROVIDERS → NORMALIZED DATA → SPECIALISTS → CHIEF ANALYST → STORED AnalysisRun → ANALYTICS UI → HISTORY → REOPEN.

Morning/evening reports now read current normalized observations. An empty «Внешние источники не подключены» report is no longer reused when data exists. Reports are versioned (v1, v2, …); latest is **АКТУАЛЬНЫЙ**.

No second AGRO app. Crypto / Legal / Beauty / Cafe unchanged. Prices, tonnes, and weather series were not invented. **AGRO 1.6 was not started.**

## STOP CONDITION

| Step | Evidence |
|------|----------|
| Refresh providers | Live `POST /providers/refresh-all` org `org-agro-live-14` HTTP 200, ~66s |
| Real records | Customs 12 CONNECTED, Gosstat 11, World Bank 12, Eurostat 1, plus PARTIAL pages |
| ЗАПУСТИТЬ АНАЛИЗ | AnalysisRun **`0d461ea3-3f23-4198-963c-efc881469bdd`** |
| ≥3 specialists with data | ukraine, trade, price, weather, crop, global (+ chief) |
| Chief stored | NEUTRAL, confidence **78**, metadata-only disclaimer |
| UI blocks | Главное заключение, Что изменилось, Риски, Возможности, источники, пробелы |
| Показать источники | provider records on the analysis payload |
| Persist after restart | singleton reset + rehydrate: analysis yes, report yes, history yes |

## DONE

- СВЕЖЕСТЬ ДАННЫХ as age labels (часы/дни). CONNECTED ≠ LIVE if data is not sub-hour.
- ПРОБЕЛЫ ДАННЫХ card: licensed quotes, backup weather, logistics tariffs, blocked Minagro, metadata-only.
- Analysis types: operational / morning / evening / weekly / outlook / custom.
- СВОЙ ЗАПРОС + filters; AI uses real Agro observations only.
- ИСТОРИЯ АНАЛИЗОВ persisted (`record_type=analysis_run`).
- Detail layout in the specified visual order; empty categories: «Недостаточно данных».
- [Пересчитать] creates a **new** report version. Old 0-source reports stay in history.
- Scheduler: 07:30 providers / 08:00 morning analytics+review; 18:30 / 19:00 evening. Jobs not duplicated. Sweep runs specialists first, then idempotent report.
- Что изменилось only when a previous run exists (NEW / ⚠ / ★).
- [Создать уведомление] [Создать задачу] [Добавить в календарь] via existing Agro notifications/tasks/calendar.
- Crop deep link `/workspace/agro?view=crops&crop=Пшеница` (no profile redesign).
- UUIDs under «Техническая информация».

## ARCHITECTURAL DECISIONS

- Extend `services/agro_ops` (`analytics.py` mixin). No new table / Alembic revision.
- AnalysisRun lives in the existing JSONB `report` bag with `record_type=analysis_run` so `list_reports` stays clean.
- Catalog titles and HTML page signals are **metadata**, not economic series. Chief must say so. CONNECTED does not imply a price conclusion.
- Report versioning: `force`/`recalculate` inserts a new row; `is_latest` computed at list time.

## LIVE FIX FOR STALE MORNING REPORT

Previous 06:47-style empty copy is **not** the current latest.

New report **`3d23b714-da94-4521-8373-7d650c73b818`** `MORNING_ON_DEMAND` v5, 10 sources, 61 observations, generated **2026-08-17 14:43 Europe/Kyiv**. Text does **not** contain «Внешние источники не подключены».

Open: http://127.0.0.1:5180/workspace/agro?view=analytics  
Intel: http://127.0.0.1:5180/workspace/agro?view=intel

## AGRO ANALYTICS STATUS

Providers available:
11 (CONNECTED/PARTIAL/DEGRADED after refresh; licensed slots still REQUIRES_CONFIGURATION)

Normalized observations:
61

Analysis run:
ID `0d461ea3-3f23-4198-963c-efc881469bdd`

Specialists executed:
ukraine, trade, price, weather, crop, global, risk, chief

Chief conclusion:
NEUTRAL — источники отвечают, но нормализованный слой = метаданные каталогов/страниц; цены и тонны не выдумываются.

Confidence:
78

Risks:
0 (нет внутренних просрочек/договоров в этом org; категория честно пустая)

Opportunities:
0

Sources used:
amis, ec_agri, eurostat, fao, ua_customs_open_data, ua_hydromet, ua_ports, ua_stat, usda_wasde, world_bank

Data gaps:
- Рыночные биржевые котировки не подключены.
- Резервный погодный провайдер не настроен.
- Данных по логистическим тарифам недостаточно.
- Минагрополитики Украины: доступ запрещён (Cloudflare 403).
- Поступили только метаданные каталогов/страниц, а не рыночные ряды.

New report:
ID `3d23b714-da94-4521-8373-7d650c73b818`
date 2026-08-17 14:43 Europe/Kyiv
sources 10

History persistence:
PASS

Frontend:
PASS (25, `src/web` workspace/agro)

Backend:
PASS (37, agro 1.0–1.5)

## SCHEDULER (unchanged keys)

From 2026-08-17 ~11:43 UTC:

| Job | Kyiv | Next |
|-----|------|------|
| agro.providers.morning | 07:30 | 2026-08-18 07:30 |
| agro.review.morning | 08:00 | 2026-08-18 08:00 |
| agro.providers.evening | 18:30 | 2026-08-17 18:30 |
| agro.review.evening | 19:00 | 2026-08-17 19:00 |

## TESTS

- `tests/test_sprint_agro_1_5.py` — health, refresh, analysis run, history, versioning, honesty, notify/task/calendar, tenant isolation, partial outage
- `src/web/workspace/agro/sprint_agro_1_5.test.tsx` — freshness, gaps, ЗАПУСТИТЬ АНАЛИЗ, history, источники
- Prior agro suites remain green (sprint id **agro-1.5**)

## NOT STARTED

AGRO 1.6+. Structured FAOSTAT/EU price series, licensed weather/FX, crop-profile redesign.

**STOP AFTER SPRINT AGRO 1.5.**
