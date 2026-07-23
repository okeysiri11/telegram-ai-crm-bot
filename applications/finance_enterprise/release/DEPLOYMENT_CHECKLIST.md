# Deployment Checklist

- [ ] Install application package `applications/finance_enterprise/`
- [ ] Apply `config.template.env` values
- [ ] Register finance routes in API server
- [ ] Verify `GET /api/finance-enterprise-certification/v1/health`
- [ ] Run `POST /api/finance-enterprise-certification/v1/bootstrap`
- [ ] Confirm readiness score ≥ 90 and status Production Ready
- [ ] Smoke-test prior module health endpoints (pay/bil/tr/da/rpt/cfo/int)
