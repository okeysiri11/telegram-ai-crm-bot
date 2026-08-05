# Production Checklist — Closed Beta

**Sprint:** 30.9 Beta Hardening

## Secrets

- [ ] `IAM_JWT_SECRET` strong, not in insecure set
- [ ] `SECURITY_MASTER_KEY` set
- [ ] `POSTGRES_PASSWORD` set (compose fails without it)
- [ ] `GRAFANA_ADMIN_PASSWORD` set
- [ ] `GOOGLE_CLIENT_ID` for production Google Sign-In
- [ ] `VITE_DEMO_AUTH=false` in production builds

## Auth flows

- [ ] Email registration
- [ ] Google login
- [ ] Organization invitation
- [ ] First login wizard (`/onboarding/first-entry`)
- [ ] MFA optional (TOTP)
- [ ] Password reset
- [ ] Session list / revoke

## Runtime

- [ ] Docker / Compose up healthy (postgres, redis, bot, nginx)
- [ ] Migrations applied
- [ ] `/health` 200
- [ ] Prometheus scrape OK
- [ ] Grafana login with non-default admin password

## Security

- [ ] Prompt firewall blocks injection samples
- [ ] Cross-tenant UI ops denied for non-elevated roles
- [ ] No demo password prefill in production UI
- [ ] Nginx CSP / HSTS plan documented

## Quality gates

```bash
cd src/web && npm run lint && npm test && npm run build
.venv/bin/python -m pytest tests/test_prompt_firewall_30_9.py -q
```
