# Sprint Vanguard Recruiting 2.5 — recruiter API auth

**Date:** 2026-09-01  
**Status:** code complete; production lead visibility still requires a Render deploy + manual check

Vanguard remains a **project inside Recruiting**. HMAC ingest headers and signing were not changed.

## AUTH_FAILURE_ROOT_CAUSE

Production recruiter pages called same-origin `/api/recruiting-ops/v1/*` with `credentials: include` plus `X-Organization-Id` / `X-Tenant-Id` / `X-Role`, and **no** `Authorization: Bearer` session JWT.

`applications/platform_builder/api/middleware.py` is registered on the process-wide aiohttp app. In production `ALLOW_HEADER_AUTH` is false, so any request that carries `X-Role` (or `X-Platform-Role`) without a live Bearer/API key returned **HTTP 401 `header_auth_disabled`**.

Vanguard website HMAC ingest does not send `X-Role`, so it continued to return HTTP 200.

## AUTH_ARCHITECTURE

Browser (owner/recruiter session JWT in `authStore`)  
→ same-origin `/api/recruiting-ops/v1` via canonical `recruitingOpsGet` / `recruitingOpsPost` (`apiFetch`)  
→ Recruiting Ops auth middleware (`jwt_service.verify_access_token` / API key / opaque ISAM)  
→ Recruiting Ops service  

HMAC ingest remains: Vercel → `POST /api/recruiting-ops/v1/vanguard/leads` with `X-Vanguard-*` only.

Secrets stay server-side. No `NEXT_PUBLIC_*` JWT/HMAC values.

## Architectural decisions

- **Extend Recruiting Ops** with its own auth middleware rather than making the APIs public or disabling Platform Builder auth globally.
- **Skip Recruiting Ops paths in Platform Builder middleware** so `X-Role` (Recruiting RBAC) is not interpreted as Platform Builder header-auth.
- **Verify JWT cryptographically without `session_manager`**. Owner/demo login (`/api/enterprise-demo-auth/v1/login`) mints a platform JWT that includes `session_id` but does not create an in-process session record; requiring that record would 401 every recruiter GET on Render workers.
- **Header-only `X-Role` remains for development/tests** (`ALLOW_HEADER_AUTH`, default on when not production) so Phase 2.4 persistence tests stay green.

## Production env (names only)

Required on Render (already listed in `render.yaml`): `IAM_JWT_SECRET`, `JWT_SECRET`, `API_JWT_SECRET`, `SECURITY_MASTER_KEY`, `ENVIRONMENT=production`.

HMAC ingest: `VANGUARD_INGEST_SECRET` (server-only; unchanged).
