# Google Auth — Sprint 30.1

**Status:** preferred Beta authentication method  
**Provider module:** `applications/enterprise_hub/security/providers/google.py`

## Flow

1. Client obtains a Google ID token (production) or `google_demo_{json}` (local/dev).
2. `POST /api/enterprise-isam/v1/auth` with `action: "google_login"`.
3. ISAM verifies the token, **auto-creates** the identity on first login via `register_or_get`.
4. Issues access + refresh tokens and an active session.
5. Audit event `google_login` is recorded.

## Verification modes

| Mode | When |
|---|---|
| `demo` | Token prefix `google_demo_` (Vite plugin / local tests) |
| `google_tokeninfo` | `GOOGLE_CLIENT_ID` set — Google tokeninfo audience check |
| `dev_unverified` | Dev only, JWT payload decode without signature — **blocked in production** without client id |

## Auto account creation

First Google login creates:

- `subject` = verified email
- default role `employee` (overridable via `role` in request body)
- attributes: name, picture, `google_sub`, `auth_providers: ["google"]`, `email_verified: true`

Subsequent logins reuse the same identity and append `google` to `auth_providers` if missing.

## Frontend

- Login chooser: «Продолжить через Google»
- `authStore.loginWithGoogle` → `productionGoogleLogin`
- Demo path: Vite `demoAuthPlugin` `POST /api/enterprise-demo-auth/v1/google`

## Extensibility

`AUTH_METHODS` and provider registry already reserve: microsoft, apple, github, telegram. Add a provider module under `security/providers/` without changing business modules.
