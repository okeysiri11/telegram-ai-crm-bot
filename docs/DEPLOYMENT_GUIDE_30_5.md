# Deployment Guide — Sprint 30.5

Extends [DEPLOYMENT_NOTES_30_4.md](./DEPLOYMENT_NOTES_30_4.md) and [DEPLOY_TOPOLOGY.md](./DEPLOY_TOPOLOGY.md).

## Build

```bash
cd src/web && npm ci && npm run lint && npm run build && npm run test
.venv/bin/python -m pytest tests/test_*28_*.py tests/test_*29_*.py tests/test_*30_*.py -q
```

## Version gate

Platform Builder health must report `1.30.0` / `30.5` / `Web Core Integration`.

## Smoke after deploy

1. `/pilot` loads under auth  
2. `/platform-builder/mission-control` shows live panel  
3. `/workspace/auto` shell loads  
4. OBS health returns ok when suite is up  
5. `VITE_TELEMETRY_ENABLED` defaults on  

## Rollback

Revert web build; PB APIs remain compatible. Disable browser telemetry without disabling OBS suite.
