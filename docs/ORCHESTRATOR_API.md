# Orchestrator API

**Prefix:** `/api/enterprise-orchestrator/v1`  
**Sprint:** 29.8

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service + platform health summary |
| GET | `/inventory` | Endpoint catalog |
| GET | `/runtimes` | Registered runtime descriptors |
| GET | `/graph` | Dependency order + edges |
| GET | `/queue` | Scheduler queue |
| GET | `/events` | Routed EventBus events |

## Client

```ts
import { enterpriseOrchestrator } from "@/runtime/orchestrator";

enterpriseOrchestrator.startup();
enterpriseOrchestrator.platformHealth();
enterpriseOrchestrator.dependencyOrder();
enterpriseOrchestrator.schedule("refresh", "intelligence");
```
