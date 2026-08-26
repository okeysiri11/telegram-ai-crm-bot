# Sprint Result — Local Owner Auth + Single Demo Account

**Date:** 2026-08-26  
**App:** `src/web` (Enterprise Web Platform)  
**Status:** Complete

## Goal

Guaranteed local Owner login (`owner@demo.corp` / `demo`) without ISAM on `localhost:8080`, without Google OAuth, and without MFA. Production authentication remains fail-closed.

## Root cause

`productionLogin` in `src/web/src/auth/identityApi.ts` probed Enterprise ISAM at `/api/enterprise-isam/v1` (Vite proxy → `127.0.0.1:8080`) whenever `isDemoAuthEnabled()` was false. Vite DEV without an explicit `VITE_DEMO_AUTH=true` (or a production-mode preview of `dist`) then threw:

`Authentication backend unavailable (ISAM proxy → localhost:8080)`

There was no `src/web/.env.development`, so local demo mode was not pinned. Login CTA «Открыть демо-пространство» previously opened a client demo (`travel@globefly.demo`) instead of Owner.

## Architectural decisions

- **Extend** the in-process Demo Auth Provider (`demoAuthProvider.ts`); do not add a new auth package.
- Demo bypass is **DEV/test only**: `import.meta.env.PROD` always disables it, even if `VITE_DEMO_AUTH=true`.
- Production builds strip `VITE_DEMO_AUTH` and never load `.env.development`.
- Canonical Owner is always tenant `demo-corp`, role `platform_owner`, full `OWNER_PERMISSIONS`.
- Production login still uses `POST /api/enterprise-demo-auth/v1/login` (platform JWT) then ISAM.

Canonical development Owner: `owner@ados.demo` · tenant `ados` · OWNER / SUPER_ADMIN.

## Quality gates

| Gate | Result |
|------|--------|
| Vitest demo Owner / demoAuth / multi-role | PASS (21) |
| Destination tests (owner skips first-entry) | PASS (2) |
| `npx vite build` | PASS |
| `npm run lint` (`tsc -b`) | FAIL — pre-existing errors in Odessa 3D / agro / crypto; **none in auth files** |
| Login HTTP `http://127.0.0.1:5180/login` | 200, no ISAM error in HTML |
| Vertical SPA routes HTTP | 200 (protected UI still requires session; Owner allowlist covered by tests) |

Backend on `:8080` is **not required** for demo Owner login.
