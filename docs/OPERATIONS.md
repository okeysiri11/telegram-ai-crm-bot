# Agro Marketplace Operations Guide

## Operator responsibilities

- Monitor `/api/agro/v1/ops/health` and `/ops/readiness`
- Review QA reports via `/ops/reports`
- Certify releases with `/ops/certify` after validation passes
- Manage partner connections and webhook subscriptions
- Escalate Platform/Ecosystem outages to platform owners (do not patch those repos from Agro)

## Health & readiness

| Check | Endpoint |
|-------|----------|
| Health | `GET /ops/health` |
| Version | `GET /ops/version` |
| Readiness | `POST /ops/readiness` |
| Validation | `POST /ops/validation` |

Ready when `ready=true`, `application_version=2.0.0`, and no readiness blockers.

## Support guide

| Issue | First response |
|-------|----------------|
| Login / portal | Verify portal user registration and notification inbox |
| Mobile auth | `POST /api/agro/mobile/v1/auth` then profile/home |
| Partner failure | Check `/partner/connections` and connector invoke result |
| AI empty reply | Check Ecosystem assistant bridge; fallbacks still return structured payloads |
| Export stuck | Inspect tracking timeline and customs declaration status |

## Disaster recovery guide

1. Confirm host process and route registration.
2. Call `/ops/health` — if Platform/Ecosystem degraded, wait for platform recovery.
3. Re-run `/ops/validation` and `/ops/deploy/verify`.
4. Recreate critical partners/webhooks from Administrator Portal / Partner API.
5. Document incident in release notes / support ticket.

## Security operations

- Internal API requires Ecosystem Identity token
- Administrator / Owner roles hold wildcard permissions
- Partner connect and AI alerts invoke governance checks

## Load testing hooks

Use `/ops/validation`, `/ops/readiness`, and domain analytics endpoints as harness targets. In-memory store is sized for commercial demo and staging loads; plan persistence before extreme scale.
