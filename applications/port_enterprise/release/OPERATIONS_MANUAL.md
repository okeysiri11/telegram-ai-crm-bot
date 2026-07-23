# Operations Manual — Port Enterprise Suite v4.6.0-enterprise

## Daily

- Check `/api/port-enterprise-certification/v1/health`
- Review AI Port Director executive briefing
- Confirm freight marketplace and customs queues are healthy

## Weekly

- Re-run certification bootstrap
- Review performance and security dashboards
- Validate warehouse and multimodal capacity forecasts

## Incident

1. Capture failing health endpoint and certification gate
2. Isolate module by API prefix
3. Reset in-memory store only in non-production diagnostics
4. Re-run QA regression tests for the affected sprint package
