# n8n Architecture

**Sprint:** 31.2 (Integration Hub deepen track)  
**Constraint:** Platform Runtime = system of record. **No business logic in n8n.**

## Role

n8n is an **external workflow orchestrator**:

- Triggers (webhook / schedule / manual)
- Fan-out to platform APIs
- Callbacks into `n8n_bridge` / webhook manager

n8n must **not** own CRM state, billing, identity, or domain rules.

## Deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.n8n.yml --profile n8n up -d
```

- Compose file: `docker-compose.n8n.yml`
- UI default: `http://localhost:5678` (`VITE_N8N_URL`)
- Callback: `ADOS_CALLBACK_URL` → `/integrations/n8n/callback`

## Bridge

| Component | Path |
|---|---|
| Python | `platform_integrations/n8n_bridge.py` |
| Web | `src/web/src/enterprise-integrations/n8nBridge.ts` |
| Webhooks | `platform_integrations/webhook_manager.py` |
| Catalog card | Integration Hub → Developer → **n8n** |

Capabilities: workflow templates, OAuth client registration (secret refs only), execution history, versioning, HMAC callback verify, audit log, monitor snapshot.

## Execution flow

```
n8n trigger → HTTP call to platform API / webhook
           → platform applies business logic (Runtime / modules)
           → n8n receives callback status only
           → n8n_bridge records execution history
```

## Security

- Credentials in ESH vault (`vault://n8n/...`)
- Signed callbacks
- Rate limits via existing `platform_integrations.rate_limiter`
- Prompt Firewall remains on APH invoke path

## Related

`INTEGRATION_HUB.md`, `WORKFLOW_LIBRARY.md`, `SPRINT_31_2_RESULT.md`
