# Sprint 30.1 Result — Enterprise Authentication & Security Foundation

**Priority:** CRITICAL  
**Status:** Complete (production foundation)  
**Date:** 2026-08-01

## Delivered

### Authentication
- Google Sign-In (preferred Beta) with auto account creation
- Email + password register/login with salted hashes
- Password reset request flow
- Remember-me sessions
- Legacy demo password compatibility (no hash → any non-empty secret)

### MFA
- Optional per-user enable/disable
- Org `mfa_required` security policy
- Russian MFA Center wired to ISAM

### Roles & access
- Enterprise role catalog in ISAM + frontend `roleManager`
- `roleResolver` / `permissionResolver` / `accessMiddleware`

### Sessions
- Multi-session, trust device, terminate, terminate-all, last login

### API security (composed with Sprint 30.0)
- ISAM access + refresh token issue on Google login
- Token rotation via existing `token_manager`
- HTTP JWT validation, rate limiting, security headers (30.0 middleware)

### Audit & Owner Security Dashboard
- Auth/MFA/session audit actions
- `/identity/security` Owner dashboard (RU): sessions, failed logins, audit, API/token status

### Frontend (RU, no redesign)
- Google / Email chooser on login
- Register + forgot password routes
- i18n keys for auth flows

### Docs
- `AUTHENTICATION.md`, `GOOGLE_AUTH.md`, `SESSION_MANAGEMENT.md`, `ROLE_MODEL.md`
- Updated `SECURITY_MODEL.md`, `ARCHITECTURE_MAP.md`
- This result file

### Tests
- `tests/test_sprint_30_1_auth.py`

## Quality gates

Run:

```bash
pytest tests/test_sprint_30_1_auth.py -q
cd src/web && npm run lint && npm test && npm run build
```

## Non-goals (honored)

- No final UI styling / redesign
- No hardcoded production credentials
- Provider slots reserved for Microsoft, Apple, GitHub, Telegram
