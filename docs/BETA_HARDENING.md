# Beta Hardening

**Sprint:** 30.9 — Enterprise Beta Hardening & AI Security (web/infra track)

## Goal

Closed Beta readiness: AI abuse controls, auth hardening, tenant checks, nginx/TLS templates, no default observability passwords.

## Delivered this sprint

1. Prompt firewall (web + APH)
2. Demo login credentials only when `VITE_DEMO_AUTH` / DEV
3. Nginx security headers, `limit_req`, SPA static root, TLS stub
4. `docker-compose.prod.yml` requires `POSTGRES_PASSWORD` + `GRAFANA_ADMIN_PASSWORD`
5. Bot healthcheck
6. Security / readiness docs pack

## Naming

Beauty Pilot Execution also uses **30.9**. Keep RESULT files distinct: this track → `SPRINT_30_9_RESULT.md` (Beta Hardening); Beauty → `SPRINT_REPORT_30_9.md` / `BEAUTY_PILOT_EXECUTION_30_9.md`.

## Checklist

See [`PRODUCTION_CHECKLIST.md`](./PRODUCTION_CHECKLIST.md) and [`SECURITY_TEST_REPORT.md`](./SECURITY_TEST_REPORT.md).
