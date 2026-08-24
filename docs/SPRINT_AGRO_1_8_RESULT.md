# SPRINT AGRO 1.8 RESULT

## STATUS

**COMPLETE. STOP after AGRO 1.8.** AGRO 1.9 was not started.

Health colors, gap severity, specialist analysts, logistics / opportunity / risk engines, source lineage, safe custom URLs, Kyiv scheduler, and distinct refresh vs recalculate are live in the existing Agro desk (`services/agro_ops`, `/api/agro-ops/v1`, `src/web/workspace/agro`).

Live org: `org-agro-live-14`. Health: **`agro-1.8`**. UI: http://127.0.0.1:5180/workspace/agro?view=intel

No second AGRO app. Crypto / Legal / Beauty / Cafe unchanged. No new Alembic revision.

---

## WHAT SHIPPED

### 19. Provider health colors

| State | Color |
| CONNECTED | green |
| PARTIAL / STALE | yellow |
| NEEDS_KEY / NEEDS_LICENSE | orange |
| BLOCKED / FAILED | red |
| METADATA_ONLY / OPTIONAL_NOT_CONFIGURED | gray |

`health_color` is returned on every provider row. Licensed empty quotes → **NEEDS_LICENSE**. Backup weather → **OPTIONAL_NOT_CONFIGURED**. Catalog HTML/CKAN with zero numeric series → **METADATA_ONLY** (probe_result can remain PARTIAL).

### 20. Gap severity

Gaps are `CRITICAL` / `IMPORTANT` / `OPTIONAL`. Coverage `unresolved_gaps` counts only CRITICAL + IMPORTANT so six optional catalog holes do not look like a broken system.

Examples: primary weather missing → CRITICAL; all prices missing → CRITICAL; logistics rates absent → IMPORTANT; secondary weather not configured → OPTIONAL; Minagro blocked but World Bank / Eurostat production exists → OPTIONAL.

### 21. Analyst agents

Specialists: Ukraine, Market, Price, Weather, Harvest (`crop`), Trade, Logistics, Ports, Risk, Opportunity, Global — then **Chief Agro Analyst**.

Chief receives: normalized real observations, specialist conclusions, freshness, source quality, structured data gaps, logistics status, opportunities, risks. UNKNOWN / LOW-trust sources are excluded from high-confidence numeric input.

### 22. Logistics Agent

Inputs: stored observations (Eurostat freight if present), internal ADOS trips / rate book, ports metadata. Output: current status, rate change, route pressure, cheapest / expensive known routes, risk, recommended checks.

**Never invents market freight.** If no quote: **«Нет актуальной коммерческой ставки»**.

### 23. Opportunity engine

When two official prices share commodity / unit / currency, the engine computes a **Potential opportunity** (buy market, sell market, price difference, estimated logistics, FX, gross spread, data confidence). Logistics is subtracted only from a real internal rate. **Not labelled as guaranteed profit.** If dimensions are incompatible, a structured empty-state explains why — the list is not left blank.

### 24. Risk engine

Risks from weather, price volatility, FX, ports, route/internal overdue, contract deadlines, inventory, data deterioration. Levels: LOW / MEDIUM / HIGH / CRITICAL + reason.

### 25. Source lineage

Claims carry `sources[]`: provider, observation, date, value, URL. UI: **[Источники]** opens that drawer. Mandatory on chief / risks / opportunities / report bullets.

### 26. Add external URL safely

`POST /api/agro-ops/v1/providers/custom` — admin URL. Classification: OFFICIAL_API / PUBLIC_DATA / RSS / MANUAL_SOURCE / UNKNOWN. Trust: HIGH / MEDIUM / LOW. **UNKNOWN does not become `market_usable` and is excluded from high-confidence analysis.**

### 27. Scheduler (Europe/Kyiv)

Suggested (configurable via `GET/PUT /api/agro-ops/v1/scheduler`):

| Kyiv | Job |
| 05:45 | weather / FX / ops (`agro.providers.dawn`) |
| 06:00 | morning analysis |
| 12:00 | light refresh |
| 17:30 | full refresh |
| 18:00 | evening analysis |
| Sunday 09:00 | weekly |
| 1st 08:00 | 1–2 month outlook |

AGRO 1.4 job keys (`agro.providers.morning` etc.) remain. New keys are additive.

### 28. Manual refresh

| Button | Meaning |
| **Обновить все** | fetch new source data (`POST /providers/refresh-all`) |
| **Пересчитать анализ** | run analysis on stored data, no forced network fetch (`POST /analytics/run`) |

---

## ARCHITECTURAL DECISIONS

- Extend `services/agro_ops` (engines + analysts + providers). No new `platform_*` package.
- Generic JSONB `agro_ops_records` for custom sources and scheduler settings. No migration.
- Additive APIs only. Frozen `/api/v1` untouched.
- `probe_result` stays PARTIAL for catalogs; `health_state` is METADATA_ONLY when `numeric_count == 0`.
- Rejected: inventing freight or labelling spreads as profit.

---

## TESTS

Backend: `tests/test_sprint_agro_1_8.py` plus 1.0–1.7 health bump to `agro-1.8`. **49 passed** (production 1.0 … 1.8).

Frontend: `src/web/workspace/agro/sprint_agro_1_8.test.tsx` plus prior agro files. **35 passed**.

---

## STOP

AGRO 1.8 is complete. Do not start AGRO 1.9 in this session.
