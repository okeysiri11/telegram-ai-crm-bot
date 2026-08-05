# ADOS Enterprise Event Bus (Sprint OS 1.1)

## Purpose

Production **Enterprise Event Bus** — the communication backbone of ADOS.

```text
Kernel → Event Bus → Runtime → Agents → Business Modules
```

Business modules **never** communicate directly. Everything goes through events.

## Location

`src/kernel/event_bus/`

| File | Role |
|------|------|
| `EventBus.ts` | Facade: publish, subscribe, once, broadcast, replay |
| `Event.ts` | Immutable event value object |
| `EventSubscriber.ts` | Subscriptions, wildcards, priority |
| `EventPublisher.ts` | Publish / deliver pipeline |
| `EventRegistry.ts` | Event type catalog + sticky store |
| `EventHistory.ts` | Ring-buffer history (million-scale via capacity) |
| `EventDispatcher.ts` | Priority-ordered delivery |
| `EventFilter.ts` | Criteria + wildcard matching |
| `KernelEventBusAdapter.ts` | Bridges Kernel `IEventBus` |

## API

```ts
import { createEventBus, StandardEventTypes } from "@ados/kernel";

const bus = createEventBus({ history: { capacity: 100_000 } });

bus.subscribe(StandardEventTypes.TaskCreated, (e) => { /* … */ });
bus.subscribe("Task*", (e) => { /* wildcard */ }, { priority: 10 });

await bus.publish({
  type: StandardEventTypes.TaskCreated,
  payload: { id: "t1" },
  mode: "sync", // sync | async | delayed
  priority: 5,
  sticky: false,
});

await bus.broadcast({ type: "News", mode: "sync" });
await bus.replay({ filter: { types: ["TaskCreated"] } });
```

## Features

- Synchronous, asynchronous, and delayed delivery
- Priority subscribers (higher first)
- Sticky events (late subscribers receive last sticky)
- Wildcard subscriptions (`Task*`, `*`)
- Event history + replay
- Filtering (subscribe + history/replay criteria)
- Async mutex for concurrent publish safety
- DI-ready (`IEnterpriseEventBus`), plugin-ready (register types), provider-independent

## Standard events

`TaskCreated`, `TaskAssigned`, `TaskStarted`, `TaskCompleted`, `TaskFailed`,
`AgentStarted`, `AgentStopped`, `ProviderConnected`, `PluginLoaded`,
`KnowledgeUpdated`, `MemoryUpdated`, `WorkflowStarted`, `WorkflowFinished`,
`SecurityAlert`, `SystemShutdown`, `BootCompleted`

## Architecture rules

- No business-module imports
- No circular deps (event_bus ← kernel; not reverse into CRM/ERP)
- Kernel never depends on verticals; verticals publish/subscribe only

## Verify

```bash
cd src/kernel && npm test && npm run typecheck
```

See `docs/EVENT_BUS_ARCHITECTURE.md`.
