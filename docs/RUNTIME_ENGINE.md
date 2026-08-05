# Runtime Engine — Enterprise Platform

**Sprint:** 28.1 · **Package:** `src/web/src/enterprise-runtime/`  
**Constraint:** Extend & integrate only — reuses Integration Hub EventBus, Desktop, Dashboard, Command Center, City, Production Studio.

## Purpose

One global **Runtime Engine** publishes continuous platform state so the Enterprise Platform behaves like a live OS instead of a set of independently polling pages.

## Architecture

```
Providers
  └─ IntegrationHubBridge
       └─ useIntegrationBoot()
            ├─ enterpriseEventBus.connectLiveBridge()
            ├─ sessionCoordinator.restoreAll()
            └─ runtimeEngine.start()
                 ├─ healthService.start()     ← ONE probe loop
                 ├─ jobManager.tick()
                 ├─ aiAgentRuntime.tick()
                 └─ publish runtime_update → enterpriseEventBus → liveUpdates
```

### Components

| Module | Role |
|--------|------|
| `runtimeEngine` | Tick loop, metrics snapshot, stream publish |
| `healthService` | Singleton health probes (`healthy` / `warning` / `critical` / `offline`) |
| `jobManager` | Central jobs: running · waiting · completed · failed · cancelled · retrying + progress/ETA |
| `aiAgentRuntime` | AI agents as runtime entities (status, task, queue, memory, workflow, health) |
| `useRuntimeHealth` | React subscribe to Health Service (no per-hook polling) |
| `useRuntimeEngine` | `useSyncExternalStore` over engine snapshot |
| `EnterpriseRuntimeMonitor` | Compact live strip for surfaces |

### Published metrics

Runtime status · Heartbeat · CPU · Memory · Workers · Jobs · Providers · GPU · Sessions · AI Agents

## Live event stream

Uses existing `enterpriseEventBus` (over `liveUpdates`). Surfaces **subscribe**; they do not run independent health pollers.

| Stream kind | Bus event type |
|-------------|----------------|
| runtime / heartbeat | `runtime_update` |
| notification | `notification` |
| ai | `ai_request` |
| production / queue | `job_update` |
| provider | `provider_update` |
| workflow | `workflow_update` |
| desktop | `desktop_update` |
| city | `city_update` |

Legacy UI hooks (`shell/enterprise/useRuntimeHealth`) re-export the singleton — Dock, StatusBar, Live Dashboard, Command Center, Platform Pulse all share one probe loop (`HEALTH_POLL_MS` = 45s).

## Performance rules

- One health timer (ref-counted).
- One runtime tick (`RUNTIME_TICK_MS` = 12s).
- Stable snapshot reference for `useSyncExternalStore` (avoid render storms).
- Modules subscribe to bus/hooks instead of duplicating `setInterval` health fetches.

## Consumers

- Desktop menubar — `EnterpriseRuntimeMonitorCompact`
- Dashboard / Mission Control — `EnterpriseRuntimeMonitor`
- Command Center metrics — live agent/job counts from engine
- Production Studio header — full monitor + job sync into Job Manager
- City glance — compact monitor + `city` stream publish

## Related docs

- [`INTEGRATION_HUB.md`](./INTEGRATION_HUB.md)
- [`SPRINT_28_1_RESULT.md`](./SPRINT_28_1_RESULT.md)
- [`SPRINT_28_2_RESULT.md`](./SPRINT_28_2_RESULT.md)
- [`ARCHITECTURE_MAP.md`](./ARCHITECTURE_MAP.md)

## Sprint 28.2 — Production Runtime

Production Center operations go through `productionRuntime` (facade over Job Manager):

- Queues: production · task · render · generation · publishing  
- Universal pipelines: 8 templates with agent chains  
- Workers + retry + analytics on the Runtime Engine tick  
- UI: Production Center → **Runtime** tab (`ProductionRuntimePanel`, lazy)  
- City Production district buildings consume queue depths for live occupancy  
