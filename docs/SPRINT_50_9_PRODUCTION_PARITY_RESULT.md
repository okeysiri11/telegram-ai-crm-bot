# Sprint 50.9 RESULT — Production parity (EURUSD native chart not on Render)

**Status:** INVESTIGATION COMPLETE  
**Date:** 2026-09-03  
**Do not commit. Do not push.**

---

## Root cause (CASE A)

EURUSD native chart + Yahoo quote live **only in the uncommitted working tree**.

Render `ados-web` deploys **`develop` @ `306e638e`**, which matches local HEAD and production `/liveness`. That commit still:

- quotes EURUSD via `NbuCrossEurUsdProvider` → `"НБУ (кросс EUR/USD)"`
- renders EURUSD with `TradingViewEmbed` (`FX:EURUSD`) → `"График TradingView временно недоступен. Проверьте сеть."`

DXY native chart **is** in that commit (Sprint 50.7), which is why production DXY works.

`EurUsdNativeChart.tsx` is **untracked** (`git ls-files` empty). Render cannot deploy it.

## Production vs local

| | Production / git HEAD | Working tree (not in git) |
|--|--|--|
| SHA | `306e638e` | same HEAD + dirty files |
| EURUSD quote | NBU cross | `yahoo_eurusd` |
| EURUSD chart | `TradingViewEmbed` | `EurUsdNativeChart` |
| DXY chart | native Lightweight Charts | same |

## Render

- Service: `ados-web` (`render.yaml`)
- Branch: `develop` (`BRANCH_MATCH=yes`)
- Image: `Dockerfile.web` → `npx vite build` → `python scripts/run_production_web.py`
- Auto-deploy: `checksPass` (GitHub production-gate must pass)

## Deployment action

Commit the EURUSD working-tree files, push `develop`, wait for production-gate, then Render deploys. No Render branch/config change required. No chart rewrite required.
