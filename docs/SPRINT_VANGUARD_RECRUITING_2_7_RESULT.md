# Sprint Vanguard Recruiting 2.7 — production Recruiting Ops connectivity

**Date:** 2026-09-01  
**Status:** code complete; needs Render deploy of this commit

Phase 2.6 (`e77ed37`) owner→`ados` mapping is **preserved**. HMAC ingest is unchanged. No seed/demo leads.

## ROOT_CAUSE

The UI string `Recruiting Ops API недоступен … backend (:8080)` is shown when `recruitingOpsGet` gets **status 0** (fetch abort/timeout/network), not when the browser actually calls localhost.

Live probes of `https://ados-web.onrender.com` after `e77ed37`:

- `GET /liveness` → 200 (revision `e77ed372`)
- `GET /api/recruiting-ops/v1/health` → 200
- `GET /api/recruiting-ops/v1/leads` (no JWT) → 401 `authentication_required`
- Recruiting routes are mounted on the **same** aiohttp Render service as the SPA (`ADOS_SERVE_WEB`, relative `/api/recruiting-ops/v1`)

So this was **not** a missing route and **not** a baked-in `localhost:8080` Recruiting client. Production JS already requested `/api/recruiting-ops/v1/leads`.

Two production defects made the page look “offline”:

1. **Hydrate stampede.** Owner reads now hydrate ingest aliases (`ados`, `default`). The Recruiting home fires health + 9 parallel GETs. Each miss raced `ensure_hydrated` (24 kinds × org) against a small Postgres pool until the 20s `apiFetch` abort → status 0 → `:8080` copy.
2. **CORS.** Production `Origin: https://ados-web.onrender.com` was not on the allow-list, and `X-Recruiting-Organization-Id` was not in `Access-Control-Allow-Headers`. Same-origin usually skips preflight; a blocked preflight would also surface as status 0.

## FIX

- Serialize org hydration with an asyncio lock; recover tracking without re-entering the lock.
- Allow same-origin Host/Origin CORS and `X-Recruiting-Organization-Id`; set `ADOS_CORS_ORIGINS=https://ados-web.onrender.com` in `render.yaml`.
- Production Recruiting prefix is forced to relative `/api/recruiting-ops/v1` (never localhost).
- Errors: 401/403/404/5xx/timeout/network — no `:8080` in production copy.

## Production verification after deploy

1. Hard-refresh Recruiting → Leads / Vacancies / Candidates / Vanguard.
2. Must not show `:8080`.
3. Authenticated owner should get HTTP 200 (empty list is OK if no lead row; 401 means session, not routing).
