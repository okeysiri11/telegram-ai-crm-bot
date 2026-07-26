# Deployment Notes — Sprint 30.4

Builds on [DEPLOY_TOPOLOGY.md](./DEPLOY_TOPOLOGY.md).

## Web front-end

```bash
cd src/web
npm ci
npm run lint && npm run build && npm run test
```

Env:

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE` | API origin (default `/api`) |
| `VITE_SOCKET_URL` | Realtime (optional) |
| `VITE_TELEMETRY_ENABLED` | Set `false` to disable OBS posts from browser |

Serve `src/web/dist` behind the same reverse proxy that mounts `/api/*`.

## Backend

Platform Builder health must report:

- `application_version`: `1.29.0`  
- `sprint`: `30.4`  
- `release_status`: `Web Foundation`  

Observability routes must remain mounted:

- `POST/GET /api/enterprise-obs/v1/metrics`  
- `POST/GET /api/enterprise-obs/v1/logs`  
- `GET /api/enterprise-obs/v1/health`  

## Pilot staging checklist

1. Deploy hub + Platform Builder + OBS  
2. Deploy web build with telemetry **enabled**  
3. Login with demo owner account → Mission Control loads  
4. Open `/workspace/auto` and confirm shell + composition links  
5. Confirm OBS receives `page_view` / `session_start` events  
6. Confirm ErrorBoundary posts on forced client error (staging only)

## Rollback

- Revert web build; PB APIs remain backward compatible  
- Disable browser telemetry with `VITE_TELEMETRY_ENABLED=false` without touching OBS suite  
