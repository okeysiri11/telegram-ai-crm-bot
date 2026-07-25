# ECE — Controller & Failure Injection

**Sprint:** 25.3 · **API:** `/api/enterprise-ece/v1`

## Scenario fields

Scenario ID · Name · Description · Target Service · Failure Type · Duration · Recovery Policy · Expected Result · Validation Rules

## Failure types

PostgreSQL / Redis / Event Bus / AI Provider / Object Storage offline · Scheduler / Auth failure · Network latency / packet loss · High CPU / memory exhaustion / disk full · API timeout · Service crash · Container restart

All injections are simulated — non-destructive, no data loss.
