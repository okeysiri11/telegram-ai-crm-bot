# Sprint 30.0 — Enterprise Security & Governance Hardening

**Phase:** Enterprise Platform v9  
**Priority:** CRITICAL  
**Mode:** Implementation (no new business features / no UI redesign / no breaking API changes)

## Executive summary

Hardened platform authentication, JWT secret resolution, tenant isolation defaults, HTTP security middleware, unified Permission Engine facade, and AI likeness consent gate. Platform Builder now prefers live JWT/API-key identity while retaining header auth only when `ALLOW_HEADER_AUTH` is enabled (default off in production).

## Deliverables

### Code

| Area | Change |
|---|---|
| JWT | `platform_security/jwt_secrets.py` — single resolver; ConfigurationCenter normalizes IAM/JWT secrets |
| Startup | `startup.py` — `validate(fail_fast=is_production)` (TD-57) |
| Models | Restored missing `SecurityPrincipal` / roles / audit types in `platform_security/models.py` |
| Auth | Platform Builder middleware — live identity first, header compat gated |
| Tenant | `repositories/tenant_scope.py` — `TenantIsolationError`, required filters by default |
| Permissions | `platform_security/permission_engine/` — Context/Resolver/Policy/Role/Cache |
| Consent | `platform_security/consent.py` — TD-46 gate before avatar/voice providers |
| HTTP | `middleware/security_middleware.py` wired into `api.server.create_app` |
| Hub fix | Data Contracts vs Digital Citizen `edc_api` import shadow fixed (architecture gate) |
| Audits | `scripts/audit_tenant_isolation.py`, `scripts/security_marker_audit.py` |

### Documentation

- `docs/SECURITY_MODEL.md`
- `docs/AUTHORIZATION.md`
- `docs/TENANT_ISOLATION.md`
- `docs/TENANT_ISOLATION_AUDIT.md`
- `docs/SECURITY_MARKER_AUDIT.md`
- `docs/SPRINT_30_RESULT.md` (this file)
- `docs/TECH_DEBT.md` updates (TD-08/46/57/58)
- `.env.example` security vars

### Tests

- `tests/test_sprint_30_security.py`
- Updated configuration / management JWT validation tests

## Migration notes

1. Production must set `IAM_JWT_SECRET` (and preferably `SECURITY_MASTER_KEY`).
2. Set `ALLOW_HEADER_AUTH=false` in production (default) — Platform Builder clients should send Bearer tokens.
3. Development continues to accept `X-Platform-Role` headers for existing PB tests/tools.
4. No route paths removed; response shapes for unauthenticated PB calls unchanged when headers absent.
5. Authoritative Alembic path remains `migrations/` per `alembic.ini` (TD-31 confirmed, not changed).

## Remaining technical debt

| Item | Status |
|---|---|
| TD-58 residual repository findings | Heuristic list in `TENANT_ISOLATION_AUDIT.md` — triage next |
| Vertical apps still using header-only middleware | Extend same live-auth pattern beyond Platform Builder |
| TD-52 permission-scope vocabularies | Docs-only remaining (Sprint 31) |
| Full secret-scan / pip-audit in CI | Recommend adding as CI job |
| Marker audit 3800+ hits | Documented; do not mass-delete |

## Quality gates

| Gate | Result |
|---|---|
| `tests/test_sprint_30_security.py` + management/config security | **Pass** |
| Platform Builder API smoke (`test_api_platform_builder`) | **Pass** |
| `scripts/security_scan_30.py` | **OK** |
| `scripts/audit_tenant_isolation.py` | Report written |
| `scripts/security_marker_audit.py` | Report written |
| `create_app()` smoke | **OK** (6324 routes) |
| Unrelated PB manifest assert (`33.6`) | Pre-existing failure — not introduced this sprint |

## Architecture Map

Updated to Sprint **30.0** with pointer to security model docs.
