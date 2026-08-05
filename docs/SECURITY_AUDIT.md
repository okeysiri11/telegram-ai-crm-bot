# Security Audit — Sprint 37.2

**Date:** 2026-07-29  
**Scope:** ADOS Enterprise Platform security layer (authn/z, JWT, secrets, middleware, isolation, AI Runtime)  
**Mode:** Hardening only — no features, no API contract changes, no schema changes

## Verdict

**Enterprise Security: READY** (with remaining P1–P3 debt documented below).

No **Critical (P0)** vulnerabilities remain in the audited control plane after Sprint 37.2 fixes.

## Objectives coverage (1–40)

| # | Objective | Status | Notes |
|---|-----------|--------|-------|
| 1 | Authentication | PASS | Management JWT/API-key; Telegram headers rejected |
| 2 | Authorization | PASS | `require_role` + Permission Engine |
| 3 | RBAC | PASS | See `RBAC_AUDIT.md` |
| 4 | Permission Engine | PASS | `platform_security.permission_engine` |
| 5 | Workspace isolation | PASS* | Registry + state scopes; deepen enforcement = P2 |
| 6 | Tenant isolation | PASS* | Helpers exist; not all repos wired = P1 |
| 7 | API permissions | PASS | Management + Hub gates |
| 8 | JWT | PASS | See `JWT_AUDIT.md` |
| 9 | Refresh tokens | PASS* | In-process revoke set = P1 for multi-node |
| 10 | Session management | PASS | IAM session TTL |
| 11 | CSRF | PASS | Cookie mutating paths; Bearer exempt |
| 12 | CORS | PASS | Kernel fail-closed in prod/staging |
| 13 | Rate limiting | PASS | Middleware + AI burst |
| 14 | API throttling | PASS | Per IP+path window |
| 15 | Request validation | PASS | Middleware + DTO validators |
| 16 | Secret management | PASS | Secret policy + ConfigurationCenter |
| 17 | Hardcoded secrets | PASS* | Dev defaults remain; prod fail-closed |
| 18 | .env loading | PASS | `env_source` + ConfigurationCenter |
| 19 | Production config | PASS | Staging shares fail-closed gates |
| 20 | Encryption | PASS* | At-rest via Postgres/TLS ops; app crypto limited = P2 |
| 21 | Password hashing | PASS | Sprint 30.1 auth paths |
| 22 | Audit logging | PASS | HTTP audit + vault hooks |
| 23 | Security middleware | PASS | RequestId / headers / rate / CSRF |
| 24 | File upload validation | PASS* | Module-specific; broaden = P2 |
| 25 | XSS | PASS | CSP + sanitizers |
| 26 | SQLi | PASS | SQLAlchemy params; raw SQL scan = P2 |
| 27 | Command injection | PASS* | Limited shell surfaces = P2 |
| 28 | SSRF | PASS* | Provider allowlists partial = P1 |
| 29 | Prompt injection | PASS | AI Runtime + APH firewall |
| 30 | AI Agent boundaries | PASS* | Security Center policies |
| 31 | Multi-Agent isolation | PASS* | Runtime sessions; harden = P1 |
| 32 | Context isolation | PASS | Runtime context manager |
| 33 | Memory access | PASS* | Scope fields; enforce all reads = P1 |
| 34 | Workflow permissions | PASS | Permission Engine + management roles |
| 35 | Admin-only endpoints | PASS | `ManagementRole.ADMINISTRATOR/OWNER` |
| 36–39 | Builder / Marketplace / Creative / Voice | PASS* | Route-level auth; deepen = P2 |
| 40 | Enterprise Command | PASS | Command palette + management auth |

\* = control present; residual gaps classified below.

## Fixes applied (safe)

1. Removed Skills SDK `or True` signature bypass; mismatch fails execution.
2. Staging included in production fail-closed secret/auth gates.
3. `ALLOW_HEADER_AUTH` is a **validation error** in production/staging.
4. ConfigurationCenter runs `validate_runtime_secrets`.
5. `TRUST_PROXY` gate for `X-Forwarded-For` (default off).
6. AI Runtime enforces APH prompt firewall via `AiSecurityCenter`.
7. CRM bootstrap no longer accepts `JWT_SECRET` as API key in prod/staging (`CRM_BOOTSTRAP_API_KEY`).
8. Management `require_role` resolves role from JWT/API principal.
9. Kernel CORS fail-closed in prod/staging unless `ADOS_CORS_ORIGIN` set.
10. Skills elevated permissions require plugin identity; signing secret via `SKILLS_SIGNING_SECRET`.

## Remaining findings

| ID | Pri | Issue | Effort |
|----|-----|-------|--------|
| R1 | P1 | `apply_tenant_filter` not used in all repositories | 3–5d |
| R2 | P1 | JWT revoke list is in-memory (not shared across workers) | 2–3d |
| R3 | P1 | OWNER telegram bootstrap on CRM auth still allowed | 0.5d |
| R4 | P1 | SSRF allowlist incomplete for some providers | 2d |
| R5 | P1 | Memory / multi-agent cross-tenant read audits | 3d |
| R6 | P2 | Pydantic JWT placeholder defaults in settings models | 0.5d |
| R7 | P2 | Historical raw `cursor.execute` in legacy services | 2–4d |
| R8 | P2 | File upload validators not centralized | 2d |
| R9 | P3 | Dependency CVE automation (pip-audit / npm audit in CI) | 1d |

## Tests

```bash
.venv/bin/python -m pytest tests/test_security_hardening_37_2.py \
  tests/test_sprint_30_security.py tests/test_management_security.py \
  tests/test_prompt_firewall_30_9.py tests/test_sprint_30_1_auth.py -q
```
