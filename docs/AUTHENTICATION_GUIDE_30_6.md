# Authentication Guide — Sprint 30.6

## What changed

Demo `jwt.*.demo` minting is **removed**. Login uses existing Enterprise ISAM and optionally Platform IAM JWT.

## Flow

1. **ISAM** (`/api/enterprise-isam/v1`)
   - Register identity  
   - Authenticate (local provider)  
   - Issue access + refresh tokens  
   - Create session  
   - Assign role + grant permissions + resolve  
   - Audit `login`  

2. **Platform JWT** (when `VITE_IAM_LOGIN_SECRET` is set)
   - `POST /management/identity/login` with `telegram_id` + `login_proof`  
   - Access/refresh JWTs become the Bearer token  
   - Refresh via `POST /management/identity/refresh`  

## Client

| Piece | Path |
|-------|------|
| API | `src/web/src/auth/identityApi.ts` |
| Store | `src/web/src/auth/authStore.ts` |
| Headers / 401 refresh | `src/web/src/integrations/apiClient.ts` |
| Proxy | Vite proxies `/api` and `/management` |

## Validated

| Concern | Mechanism |
|---------|-----------|
| JWT | Platform IAM when configured |
| Refresh tokens | IAM refresh or ISAM re-issue |
| Session validation | JWT `exp` check + refresh |
| Role resolution | ISAM roles + IAM principal.roles |
| Organization | tenantId / workspace company |
| Permission resolution | ISAM permissions.resolve |
| Audit logging | ISAM `/audit` + OBS telemetry.audit |

## Env

```
VITE_IAM_LOGIN_SECRET=<same as IAM_LOGIN_SECRET>
VITE_OWNER_TELEGRAM_ID=<owner telegram id>
IAM_JWT_SECRET=<production secret>
IAM_LOGIN_SECRET=<login proof>
```

Without `VITE_IAM_LOGIN_SECRET`, login still succeeds via **ISAM** (production-ready enterprise tokens; not demo). JWT badge appears when platform tokens are minted.
