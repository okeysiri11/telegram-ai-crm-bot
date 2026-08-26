# Authentication — Sprint 30.1

**Status:** production foundation · Enterprise Web Platform  
**Related:** [`GOOGLE_AUTH.md`](./GOOGLE_AUTH.md) · [`SESSION_MANAGEMENT.md`](./SESSION_MANAGEMENT.md) · [`ROLE_MODEL.md`](./ROLE_MODEL.md) · [`SECURITY_MODEL.md`](./SECURITY_MODEL.md)

## Purpose

ISAM (`applications/enterprise_hub/security`) is the authentication runtime for the Enterprise Web Platform. The web client (`src/web`) talks to `/api/enterprise-isam/v1`.

## Methods

| Method | Primary | Notes |
|---|---|---|
| Google Sign-In | **Yes (Beta preferred)** | Auto-creates account on first login |
| Email + password | Yes | Salted SHA-256; register + login |
| Password reset | Yes | Issues reset token (demo returns token for tests) |
| Email verification | Attribute `email_verified` on identity | Set true for Google |
| Remember me | Session TTL extended (30 days) | `remember_me` on session create |
| Future providers | Named stubs | microsoft, apple, github, telegram |

## API actions (`POST /auth`)

- `login` / provider local — email + password
- `google_login` — Google ID token → identity + access/refresh tokens + session
- `register` — local account creation
- `password_reset` — reset request
- `authorize` — RBAC check

## Frontend (Russian copy)

- `/login` — «Продолжить через Google», «Войти по Email»
- `/auth/register` — «Создать аккаунт»
- `/auth/forgot-password` — «Восстановить пароль»

## Client modules

- `src/web/src/auth/identityApi.ts` — `productionLogin`, `productionGoogleLogin`, `productionRegister`, `productionPasswordReset`
- `src/web/src/auth/authStore.ts` — session store
- `src/web/auth/pages/*` — auth screens (no redesign this sprint)

## Environment

| Variable | Role |
|---|---|
| `GOOGLE_CLIENT_ID` | Production Google token audience |
| `IAM_JWT_SECRET` / `JWT_SECRET` | Platform JWT mint (Sprint 30.0) |
| `VITE_DEMO_AUTH` | Local demo Owner login (`owner@ados.demo`, tenant `ados`). Default **on** in Vite DEV. **Ignored in production builds.** |
| `VITE_DEMO_OWNER_PASSWORD` | Optional local override of the existing DEV Owner password. Never used in production builds. |

## Compatibility

Legacy demo identities without `password_hash` still accept any non-empty password so existing demo flows keep working. New registrations always store a salted hash.

Canonical development Owner:

- `owner@ados.demo` · tenant `ados` · role OWNER / SUPER_ADMIN

Password comes from the existing DEV demo mechanism (`VITE_DEMO_OWNER_PASSWORD` or the built-in DEV default). Do not use production credentials.

Production login: in Vite DEV, `productionLogin` uses the in-process Demo Auth Provider and never calls ISAM on `:8080`. Production builds ignore `VITE_DEMO_AUTH=true` and use `POST /api/enterprise-demo-auth/v1/login` (platform JWT) then ISAM.
