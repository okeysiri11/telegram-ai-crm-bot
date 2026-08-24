# SPRINT AGRO 1.9 RESULT

## STATUS

**COMPLETE. STOP after AGRO 1.9.** AGRO 1.10 was not started.

Provider health summary, operational numeric counts, first-class manual CONFIRMED/UNCONFIRMED data, quality checker, anomaly labels, ordered pipeline, Kyiv scheduler wiring, rebuild with `pipeline_version: AGRO_1_9`, and one-metric charts are live in the existing Agro desk (`services/agro_ops`, `/api/agro-ops/v1`, `src/web/workspace/agro`).

Live org: `org-agro-live-14`. Health: **`agro-1.9`**. UI: http://127.0.0.1:5180/workspace/agro?view=intel

No second AGRO app. Crypto / Legal / Beauty / Cafe unchanged. No new Alembic revision.

---

## WHAT SHIPPED

### 33. Provider health page

Summary card **ЗДОРОВЬЕ ИСТОЧНИКОВ**:

| Field | Mapping |
| Healthy | `CONNECTED` |
| Partial | `PARTIAL`, `STALE`, `METADATA_ONLY`, `DEGRADED` |
| Needs key | `NEEDS_KEY`, `NEEDS_LICENSE` |
| Optional | `OPTIONAL_NOT_CONFIGURED`, unprobed `REQUIRES_CONFIGURATION` / `NOT_CONFIGURED` |
| Failed | `BLOCKED`, `FAILED` |
| Last full refresh | timestamp |
| Refresh duration | seconds |

`manual_import` is excluded from these counts.

### 34. Operational data counts

Numeric-only (metadata never mixed in):

Числовых наблюдений · Свежих &lt;24ч · За 7 дней · Исторических · Ценовых · Погодных · Торговых · Логистических

Logistics includes trips with a real rate plus `market_price` with `price_kind=freight`.

### 35. Manual data first-class

Operator data (carrier quote, warehouse stock, counterparty/farmer offer, buyer demand, contract rate) is not auto-downgraded.

Trust: **CONFIRMED** (default for operator-entered `market_price` / `trip`) or **UNCONFIRMED** (flagged, never deleted). CONFIRMED manual is included in production observations even if the URL class is UNKNOWN.

### 36. Data quality checker

Before analytics: duplicate detection, unit consistency, date sanity, future-date, outlier, stale, missing dimensions, negative impossible values.

Flags only (`kept: True`). Nothing is silently deleted.

### 37. Anomaly detection

Label **ANOMALY** only when ≥3 comparable points exist on the same series (same unit). Price/FX move above configured % (default 8%), weather HIGH, large production revision.

### 38. Scheduler

Kyiv slots unchanged: 05:45 refresh, 06:00 morning, 12:00 light, 17:30 full, 18:00 evening, Sunday weekly, 1st monthly outlook.

Jobs now call the pipeline in order: **refresh → normalize → quality validation → analysis → report generation**. AGRO 1.4 job keys remain.

### 39. Pipeline

`FETCH → RAW STORE → NORMALIZE → VALIDATE → DEDUPLICATE → CLASSIFY FRESHNESS → CLASSIFY MARKET USABILITY → SPECIALIST ANALYSTS → CHIEF ANALYST → REPORT → NOTIFICATIONS`

Reports are not generated from `provider_raw` / `provider_snapshot`. Catalog HTML may still appear as `metadata_only` bullets (1.4 trade DATA). Economic `sources_count` stays numeric-only.

### 40. Automatic rebuild after fix

`POST /api/agro-ops/v1/pipeline/rebuild`: **Обновить все** then **Пересчитать анализ**, then Morning / Evening / Weekly / 1–2 month outlook with `pipeline_version: AGRO_1_9`.

### 41–42. Acceptance / charts

Health `agro-1.9 ok`. Full refresh, source counts, weather/price/FX/WB/Eurostat/FAO, logistics tables, manual freight quote visible to logistics analytics, recalculate, `source_count > 0`, confidence computed, no mixed-unit sawtooth charts, old reports **УСТАРЕЛ**, latest **АКТУАЛЬНЫЙ**.

Every chart: dates ordered, no duplicated dates, one metric / majority unit.

---

## ARCHITECTURAL DECISIONS

- Extend `services/agro_ops` (`quality.py` + existing mixins). No new `platform_*` package.
- Persist last full refresh on a settings row (`refresh_meta`). Generic JSONB `agro_ops_records`. No migration.
- Additive APIs only (`/pipeline/rebuild`, dashboard fields). Frozen `/api/v1` untouched.
- CONFIRMED manual is first-class; UNCONFIRMED is flagged and excluded from high-confidence numeric input.
- Rejected: silently deleting bad rows; mixing tmax and precipitation on one sparkline; treating operator freight as inferior to official series.

---

## TESTS

Backend: `tests/test_sprint_agro_1_9.py` plus 1.0–1.8 health bump to `agro-1.9`. **56 passed** (production 1.0 … 1.9).

Frontend: `src/web/workspace/agro/sprint_agro_1_9.test.tsx` plus prior agro files. **39 passed**.

---

## STOP

AGRO 1.9 is complete. Do not start AGRO 1.10 in this session.
