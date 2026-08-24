# SPRINT AGRO 1.5 — ANALYTICS PLAN

## Goal

Turn Агро-разведка into an operational analytics desk: freshness, explicit data gaps, typed analysis runs, history, and morning/evening reports that use **current** normalized observations.

Do not invent prices, tonnes, weather series, or narratives for empty categories.

## Architecture

Extend `services/agro_ops` only. No second AGRO app. No new Alembic revision.

| Artifact | Storage |
|----------|---------|
| AnalysisRun | `agro_ops_records` via existing `report` bag, `record_type=analysis_run` |
| Specialist outputs | existing `analyst_output` |
| Morning/Evening reports | existing `record_type=report` with **versions** (never overwrite) |

Layering: Providers → RAW → Parser → Normalized observation → Specialists → Chief → stored AnalysisRun → Analytics UI → History.

## Analysis types

- Оперативный анализ (`operational`)
- Утренний анализ (`morning`)
- Вечерний анализ (`evening`)
- Недельный анализ (`weekly`)
- Стратегический прогноз 1–2 месяца (`outlook`)
- Пользовательский анализ (`custom`) — question + optional crop/country/region/period/source

## Honesty rules

- CONNECTED ≠ enough economic data. Catalog titles / HTML page signals are metadata; the chief must say so.
- Empty categories: «Недостаточно данных».
- Freshness is an age label (часы/дни), not a LIVE claim.
- Gaps are a first-class card, never hidden.
- Custom analysis uses only real Agro observations + internal ADOS facts.

## Report versioning

Same day, same kind: v1, v2, … New versions on `[Пересчитать]` / `force`. Latest marked **АКТУАЛЬНЫЙ**. Old empty 0-source reports stay in history.

`open_latest` must not silently serve a 0-source report when observations now exist (`offer_recalculate`).

## Integrations (existing subsystems)

- Notifications / alert_rule
- Tasks (`create_task_from_entity` + `analysis_id`)
- Calendar events
- Crop deep link `/workspace/agro?view=crops&crop=Пшеница` (no crop-profile redesign)

## Scheduler (unchanged keys, Europe/Kyiv)

07:30 providers → 08:00 morning analytics + review  
18:30 providers → 19:00 evening analytics + review  

Review jobs run specialists first, then the existing idempotent report sweep.

## Out of scope

AGRO 1.6+. Structured FAOSTAT/EU price series. Licensed weather/FX. Crop profile redesign.
