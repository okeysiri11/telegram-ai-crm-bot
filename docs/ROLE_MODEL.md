# Role Model — Sprint 30.1

## Enterprise roles

| Role | ISAM id | Typical groups |
|---|---|---|
| Owner | `owner` | administration, api_access, finance, crm, erp |
| Administrator | `administrator` | administration, api_access, crm, erp |
| Manager | `manager` | crm, analytics, ai_agents |
| Employee | `employee` | crm |
| Client | `client` | marketplace |
| Dealer | `dealer` | crm, marketplace |
| Partner | `partner` | marketplace, analytics |
| Accountant | `accountant` | finance |
| Lawyer | `lawyer` | administration |
| Production | `production` | erp, analytics |
| Viewer | `viewer` | analytics |

Legacy ISAM roles (`super_admin`, `platform_admin`, `company_owner`, …) remain valid. `ENTERPRISE_ROLE_ALIASES` maps product names to canonical ids.

## Resolvers

| Layer | Module |
|---|---|
| Backend RBAC | ISAM `authorization` + `platform_security.permission_engine` |
| Frontend roles | `src/web/auth/managers/roleManager.ts` |
| Frontend access | `roleResolver` / `permissionResolver` / `accessMiddleware` in `enterpriseAccess.ts` |
| UI guard | existing `PermissionGuard` |

## Access middleware

`accessMiddleware(ctx, permission)` evaluates explicit permissions, then elevated roles (`owner`, `administrator`, `platform_owner`), then local `permissionManager`.
