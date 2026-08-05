# API Security

**Sprint:** 30.9 Beta Hardening + **32.4** API Gateway policy facade

## Verified surfaces

| Control | Implementation |
|---------|----------------|
| JWT validation | `platform_security/jwt_secrets.py`, ISAM `token_manager`, `identityApi` |
| Google OAuth | ISAM `security/providers/google.py` + web Google login |
| Session expiration | ISAM `session_manager` + web Sessions page |
| Refresh tokens | `identityApi` refresh + token rotation |
| API authorization | Management JWT/API key; PB live auth; `enterpriseAccess` |
| Role / permission | RBAC in ISAM + `PermissionGuard` / `accessMiddleware` + `authorization_center` |
| Tenant validation | `apply_tenant_filter`, `X-Tenant-Id` via `apiClient`, `tenantGuard.ts` |
| Request validation | `validate_input_string`, prompt firewall, Zod login schemas, `ApiGatewayPolicy` |
| Response sanitization | `sanitizeErrorMessage` / `sanitizeApiErrorMessage` |
| Rate limiting | `middleware/security_middleware` (+ anti-parsing adaptive limits) |
| IP allow/deny | `ApiGatewayPolicy` (32.4) |
| Security headers | `secure_headers_middleware` |
| Request signing / replay | `ExternalAiGuard` + `ApiGatewayPolicy` nonce checks (32.4) |

## Client helpers (30.9)

`src/web/src/security/tenantGuard.ts` — `validateTenantContext`, `assertSameTenant`, error redaction.

## Related

[`SECURITY_MODEL.md`](./SECURITY_MODEL.md) · [`SECURITY_CENTER.md`](./SECURITY_CENTER.md) · [`AUTHENTICATION.md`](./AUTHENTICATION.md) · [`AI_SECURITY.md`](./AI_SECURITY.md) · [`ANTI_PARSING.md`](./ANTI_PARSING.md)
