# Operator Guide — Closed Beta

**Sprint:** 31.0

## Daily checks

| Check | How |
|-------|-----|
| Health | `GET /health` |
| Metrics | `GET /metrics` · Grafana |
| AI Runtime | `/platform-builder/runtime` · `/ai-agents` |
| Logs | `/command-runtime` |
| Platform status | `/owner` · `/health` |

## Owner operations

- Users / orgs: `/identity/users`, `/identity/organizations`
- Modules: sidebar + Marketplace `/marketplace`
- Agents: `/ai-agents`
- Monitoring: `/health`, Prometheus `:9090`, Grafana `:3000`

## Incidents

1. Confirm `/health` and bot container healthcheck  
2. Check Redis/Postgres health in compose  
3. Rotate compromised secrets via ConfigurationCenter / `.env.production`  
4. Review AI security blocks in audit vault / APH security store  

## Do not

- Ship with `VITE_DEMO_AUTH=true`
- Use default Grafana/Postgres passwords
- Disable tenant filters (`required=False`) without audit

## Related

[OPERATOR runbooks](./PRODUCTION_CHECKLIST.md) · [AI_SECURITY.md](./AI_SECURITY.md) · [DEPLOYMENT.md](./DEPLOYMENT.md)
