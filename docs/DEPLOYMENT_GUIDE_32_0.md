# Deployment Guide — Sprint 32.0

Extends `DEPLOYMENT_GUIDE_30_7.md` with seven-ecosystem + EPD probes.

## Pre-deploy probes

```bash
# Platform Builder
curl -sf "$API/api/platform-builder/v1/health"

# Mission Control
curl -sf "$API/api/platform-builder/v1/mission-control/status"

# Production Readiness (EPD)
curl -sf "$API/api/enterprise-epd/v1/health"
curl -sf "$API/api/enterprise-epd/v1/dashboard"

# Pilot Readiness (EPR)
curl -sf "$API/api/enterprise-epr/v1/health"

# Observability
curl -sf "$API/api/enterprise-obs/v1/health"

# Seven ecosystems (primary health)
curl -sf "$API/api/auto/v1/health"
curl -sf "$API/api/enterprise-bos/v1/health"
curl -sf "$API/api/enterprise-cos/v1/health"
curl -sf "$API/api/agro/v1/health"
curl -sf "$API/api/legal-enterprise/v1/health"
curl -sf "$API/api/finance-da/v1/health"
curl -sf "$API/api/drone/v1/health"
```

## Required secrets / env

- `IAM_JWT_SECRET` (or vault ref)
- Database / Redis connection strings per existing deploy docs
- `VITE_API_BASE` for web build

## Post-deploy UI smoke

1. Login → `/pilot`
2. `/pilot/production` → Refresh probes → optional Run EPD gate
3. Mission Control → Refresh status
4. Spot-check one LiveWorkflow per ecosystem

## Versions

- Platform Builder **1.40.0** / sprint **32.0**
- Enterprise Web Platform **9.4.0** (unchanged hub web version)
