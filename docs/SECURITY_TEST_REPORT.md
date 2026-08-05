# Security Test Report — Sprint 30.9

**Date:** 2026-08-01  
**Scope:** Closed Beta hardening (AI prompt firewall, auth demo gate, infra defaults, tenant helpers)

## Summary

| Area | Result | Notes |
|------|--------|-------|
| Prompt injection | Mitigated | Client + APH deny-list + sanitize |
| XSS (prompt/HTML) | Mitigated | Script strip in sanitizer; CSP header |
| CSRF | Existing | Cookie CSRF middleware (opt-in) |
| SSRF | N/A this sprint | No new URL fetch surfaces |
| SQL injection | Existing | `validate_input_string` + ORM filters |
| Command injection | N/A | No new shell invocation |
| Broken access control | Existing + tests | AI task org isolation; tenantGuard |
| Sensitive data exposure | Improved | Error redaction helpers; Grafana default removed |
| Auth bypass (demo) | Hardened | Prefill only when demo auth enabled |
| Default credentials | Fixed (prod compose) | Postgres/Grafana require env |

## Automated tests

- Vitest: `aiRuntime.test.ts` (prompt block), `betaHardening.test.ts`
- Pytest: `tests/test_prompt_firewall_30_9.py`
- Prior: `tests/test_sprint_30_security.py`, `test_sprint_30_1_auth.py`, `test_management_security.py`

## Residual risks (non-critical for internal Beta)

1. Heuristic prompt firewall — not an LLM classifier; tune patterns over time.
2. Tenant audit script findings remain heuristic (`TENANT_ISOLATION_AUDIT.md`) — triage ongoing.
3. TLS must be enabled by operators (stub in nginx).
4. Legacy unhashed demo identities outside demo mode — keep `VITE_DEMO_AUTH` off in prod.

## Critical issues

**Zero critical open issues introduced this sprint.** Default Grafana/Postgres passwords removed from prod compose.
