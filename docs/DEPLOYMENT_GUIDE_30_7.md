# Deployment Guide — Sprint 30.7

Extends [DEPLOYMENT_GUIDE_30_5.md](./DEPLOYMENT_GUIDE_30_5.md).

## Rollback checklist

1. Redeploy previous web `dist` (30.6)  
2. Confirm PB health still serves prior APIs (backward compatible)  
3. Disable browser telemetry if needed: `VITE_TELEMETRY_ENABLED=false`  
4. Do not delete EPR/OBS data  

## Environment validation

| Check | Expect |
|-------|--------|
| API proxy | `/api` + `/management` → hub |
| PB health | `1.32.0` / `30.7` / `Pilot Hardening` |
| EPR health | `/api/enterprise-epr/v1/health` ok |
| ELE health | `/api/enterprise-ele/v1/health` ok |
| OBS health | `/api/enterprise-obs/v1/health` ok |
| Auto health | `/api/auto/v1/health` ok |

## Configuration / secrets

| Var | Required for |
|-----|----------------|
| `IAM_JWT_SECRET` | Platform JWT |
| `IAM_LOGIN_SECRET` / `VITE_IAM_LOGIN_SECRET` | JWT mint from web |
| `VITE_OWNER_TELEGRAM_ID` | Owner JWT mapping |
| `VITE_TELEMETRY_ENABLED` | Browser OBS posts |

## Startup verification

1. `/login` succeeds (ISAM)  
2. `/pilot` loads metrics + journeys  
3. Submit one feedback item → trace id appears  
4. `/workspace/auto` run includes timeline + quality_gates  
5. Mission Control live panel refreshes  
