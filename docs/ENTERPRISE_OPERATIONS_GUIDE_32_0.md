# Enterprise Operations Guide — Sprint 32.0

## Daily ops

1. Open **Mission Control** → refresh live status (MC + OBS + seven ecosystem health).
2. Open **Pilot Dashboard** → sessions, workflow completion, feedback triage.
3. Open **Production Readiness** (`/pilot/production`) → EPD/EPR probes + checklist.

## Alerts & telemetry

- OBS: `/api/enterprise-obs/v1/health|metrics|logs`
- Pilot feedback → EPR → EOC → EPI (Critical/High open OBS incidents)
- Telemetry helpers: `telemetry.audit`, `telemetry.userActivity`, `telemetry.apiCall`

## Cross-ecosystem overview

All seven live workflows share Concierge, AI Team, notifications, Mission Control, and OBS. Domain APIs remain under existing prefixes (`/api/auto/v1`, BOS, Cafe OS, agro, legal-*, finance-da, `/api/drone/v1`).

## Incident path

1. Confirm OBS health
2. Check failing ecosystem health probe on MC / Production page
3. Review Pilot feedback severity + trace id
4. Do **not** stand up parallel monitoring stacks
