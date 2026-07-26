# Operations Guide — Sprint 32.1

## Daily

1. Mission Control → refresh (ecosystems + tenants)
2. Pilot Dashboard → tenancy overview + OBS/EPD/EPR
3. Production Readiness → secrets (ESH) + DR (ERL) probes

## Startup / shutdown

- Prefer existing process managers and health endpoints
- Startup validation: run `DEPLOYMENT_GUIDE_32_1.md` probe list
- Graceful shutdown: stop reverse proxy → app workers → DB (no new shutdown service)

## Alerting

OBS metrics/logs + Pilot feedback Critical/High → existing incident path. Do not stand up parallel alert stacks.
