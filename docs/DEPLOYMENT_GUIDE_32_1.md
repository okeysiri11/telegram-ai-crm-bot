# Deployment Guide — Sprint 32.1

Extends `DEPLOYMENT_GUIDE_32_0.md`.

## Additional probes

```bash
curl -sf "$API/api/enterprise-tenancy/v1/health"
curl -sf "$API/api/enterprise-eon/v1/health"
curl -sf "$API/api/enterprise-esh/v1/health"
curl -sf "$API/api/enterprise-erl/v1/health"
curl -sf "$API/api/ecosystem/v1/health"
```

## UI smoke (external pilot)

1. Login → `/pilot/onboard` → Run full onboarding
2. `/pilot/invite` → register → create org → invite
3. `/invite/accept?token=…` → accept
4. `/pilot` → tenancy overview present
5. `/pilot/production` → score ≥ 90

## Versions

Platform Builder **1.41.0** / sprint **32.1**
