# Security Model — Sprint 30.0 + 30.1 + 30.9 + 32.4

**Status:** living · Enterprise Security & Governance + Authentication Foundation + Security Center  
**Related:** [`SECURITY_CENTER.md`](./SECURITY_CENTER.md) · [`ZERO_TRUST.md`](./ZERO_TRUST.md) · [`AUTHENTICATION.md`](./AUTHENTICATION.md) · [`GOOGLE_AUTH.md`](./GOOGLE_AUTH.md) · [`AUTHORIZATION.md`](./AUTHORIZATION.md) · [`ROLE_MODEL.md`](./ROLE_MODEL.md) · [`SESSION_MANAGEMENT.md`](./SESSION_MANAGEMENT.md) · [`TENANT_ISOLATION.md`](./TENANT_ISOLATION.md)

## Principles

1. **Single secret path** — IAM signing uses `platform_security.jwt_secrets.resolve_iam_signing_secret()` only.
2. **ConfigurationCenter boundary** — no direct `os.environ` in `platform_security` for secrets (TD-17 closed in code).
3. **Live identity preferred** — Bearer JWT / API key before header compatibility (TD-08).
4. **Tenant filters required by default** — `apply_tenant_filter(..., required=True)` (TD-58).
5. **Consent before likeness generation** — `platform_security.consent` gate (TD-46).
6. **Google preferred for Beta** — auto-provisioned identities via ISAM Google provider (Sprint 30.1).
7. **Zero Trust** — every request context verified via Security Center (`verify_request`) (Sprint 32.4).
8. **No vertical security SoR** — platform_security / ISAM / middleware only; verticals call adapters.

## Authentication surfaces

| Surface | Mechanism |
|---|---|
| Enterprise Web `/login` | Google Sign-In or email/password → ISAM `/api/enterprise-isam/v1` |
| `/management/*` | JWT Bearer or `X-API-Key` only (`platform_management.auth`) |
| Platform Builder `/api/enterprise-pb/*` | Live JWT/API key preferred; `X-Principal`/`X-Platform-Role` only if `ALLOW_HEADER_AUTH` |
| Telegram bot | `TenantMiddleware` + identity services |

## ISAM security layer (30.1)

| Capability | Module |
|---|---|
| Auth (Google + local) | `security/authentication.py` |
| Sessions | `security/session_manager.py` |
| MFA + org policy | `security/services.py` (`MFAService`) |
| Tokens (access/refresh/rotation) | `security/token_manager.py` |
| Audit | ISAM audit store + Owner Security Dashboard |
| Roles | `security/models.py` `ROLES` + `ENTERPRISE_ROLE_ALIASES` |

## Enterprise Security Center (32.4)

SoR: `platform_security.security_center.EnterpriseSecurityCenter` — Zero Trust, risk score, threat timeline, AI/anti-parsing/external-AI/API/knowledge policies, incident + audit centers. See [`SECURITY_CENTER.md`](./SECURITY_CENTER.md).

## HTTP security middleware

Registered on `api.server.create_app`:

- `request_id_middleware` → `X-Request-Id`
- `secure_headers_middleware` → nosniff / frame deny / CSP / referrer
- `rate_limit_middleware` → per-IP+path sliding window
- `csrf_middleware` → cookie sessions only (off by default)
- `audit_logging_middleware` → structured 4xx/5xx logs

## Secrets

| Env | Role |
|---|---|
| `IAM_JWT_SECRET` | Authoritative IAM HMAC secret |
| `JWT_SECRET` | Legacy alias; normalized to IAM when insecure |
| `API_JWT_SECRET` | Gateway API JWT |
| `SECURITY_MASTER_KEY` | SecretManager master key (required in production) |
| `ALLOW_HEADER_AUTH` | Header-compat auth (default off in production) |
| `GOOGLE_CLIENT_ID` | Google ID token audience (required in production for Google Sign-In) |
| `N8N_ENCRYPTION_KEY` | Required when n8n profile enabled (no placeholder default) |

Production validation refuses insecure JWT secrets and missing/default master keys. Production Google login refuses unverified tokens without `GOOGLE_CLIENT_ID`.

## AI input security (Sprint 30.9 + 32.4)

Prompt firewall on APH `invoke` / `assemble_prompt` and web `taskExecution.create`:

- Sanitize + deny-list injection/jailbreak patterns
- Token estimate / truncate
- Abuse burst detection
- Audit to vault / APH security store
- Security Center facade + External AI Guard for unknown runtimes

See [`AI_SECURITY.md`](./AI_SECURITY.md) · [`PROMPT_FIREWALL.md`](./PROMPT_FIREWALL.md).

## Migration notes

- Existing clients sending only `X-Platform-Role` continue to work in development.
- Production must set `ALLOW_HEADER_AUTH=false` (default) and use Bearer tokens.
- No API route paths removed or renamed this sprint.
- Demo identities without password hashes remain login-compatible; new local registrations store salted hashes.
- AI OS Experience sprint id 32.4 docs remain authoritative for Concierge chrome (collision with this Security track).
