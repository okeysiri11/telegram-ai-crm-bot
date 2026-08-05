# Sprint 32.6A Result — First Local Launch Recovery

**Track:** Local Launch Recovery  
**Date:** 2026-08-02  
**Status:** Complete

## Naming collision

**Sprint 32.6** = AI Team Collaboration (`AI_TEAM_COLLABORATION_32_6.md`).  
This RESULT is **32.6A Local Launch** only — Intelligence/Collab docs untouched.

## Delivered

1. Backend inventory for frontend documented in `LOCAL_RUN.md`
2. One-command `npm run dev:all` → `scripts/dev_all.mjs`
3. API-only starter `scripts/run_api_local.py` (no Telegram bot)
4. Docker optional — continues with local Postgres; Redis optional
5. Vite proxy: graceful `api_unavailable` JSON (no ECONNREFUSED crash)
6. `src/web/.env.development` with demo auth + proxy
7. `FIRST_LOCAL_RUN_REPORT.md` with ports / gaps / launch command

## Success path

```bash
npm run dev:all
# → http://127.0.0.1:5180/login (owner@demo.corp / demo)
# → /owner · /city · /platform-builder/runtime
# → http://127.0.0.1:8080/liveness
```

## Quality note

Local API `/liveness` verified **200** with Postgres up and Redis down. Full `/health` may be 503 until Redis + schema readiness improve — acceptable for first Owner demo with demo auth.
