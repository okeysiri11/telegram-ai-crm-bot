# Event Bus

**Canonical SoR:** `events.event_bus.PlatformEventBus` (`events/event_bus.py`)  
**Policy:** `events/event_bus_policy.py`  
**Related:** Sprint 32.3 consolidation · Sprint 34.2C platform-state events

---

## Policy (mandatory)

1. **One Event Bus SoR** — `PlatformEventBus`. Do not create a second bus for cross-module effects.
2. Modules must communicate via **publish / subscribe**, not by importing sibling packages for side effects.
3. Legacy buses are allowlisted only in `event_bus_policy.py` (adapters / local UI mirrors).
4. Handlers must be isolated and fail-safe (bus continues if a handler errors).

```python
from events.event_bus import PlatformEventBus, subscribe
from events.base_event import BaseEvent

await PlatformEventBus.publish(event, wait=False)
subscribe(MyEvent, handler, handler_id="my_handler")
```

---

## Topology

```
Producers (requests, workflows, identity, platform_state adapters, AI)
        ↓
  PlatformEventBus
        ↓
Consumers (notifications, SLA, metrics, audit, RealtimeHub, SyncEngine handlers)
```

Realtime bridge: `platform_realtime.event_dispatcher` + `platform_state.realtime_handler`.

---

## Sprint 34.2C — Platform state events

Typed events live in `platform_state/events.py`. They are **published on the same canonical bus** (no new SoR).

| Event | Slice | Typical action |
|-------|-------|----------------|
| `PlatformStateChangedEvent` | any | generic change |
| `TaskCreatedEvent` / `TaskCompletedEvent` | tasks | create / complete |
| `CalendarUpdatedEvent` | calendar | create/update |
| `NotificationCreatedEvent` | notifications | create |
| `ConversationUpdatedEvent` | conversations | message / bind |
| `MemoryUpdatedEvent` | memory | store |
| `CrmUpdatedEvent` | crm | lead/deal/contact |
| `FileUploadedEvent` | files | upload |
| `WorkspaceChangedEvent` | workspaces | switch / config |

### Cross-client flow

```
Telegram / Web / Desktop / Mobile / API / AI
        ↓
  PlatformState adapters
        ↓
  SyncEngine.publish_change
        ↓
  PlatformEventBus.publish
        ↓
  platform_state_realtime → RealtimeHub
        (channels: platform_state, system, slice channel)
```

Registration at boot (`events.handlers.register_platform_event_handlers`):

```python
from platform_state.realtime_handler import register_platform_state_handlers
register_platform_state_handlers()
```

### AI constraint

AI Agents must not read platform modules directly for side effects. Path:

```
Platform State → Sync Engine → Platform API / Event Bus
```

Use `platform_state.clients.ai_runtime` or `POST /management/v1/platform-state/mutate`.

---

## Sprint 36.1 — Enterprise Event Bus (control plane)

**Rejected:** `platform_core/event_bus/` (no physical `platform_core/` package).  
**Chosen:** `platform_enterprise_event_bus/` — enterprise ops façade that **wraps** `PlatformEventBus` (topics, filters, DLQ, retry, replay, signing, REST, WebSocket, UI).

```
Producers / Service Builder / Runtimes
        ↓
platform_enterprise_event_bus  (topics · validate · sign · store · route · DLQ)
        ↓
events.event_bus.PlatformEventBus   ← SoR (unchanged)
        ↓
RealtimeHub channel `event_bus` + domain subscribers
```

### Components

| Component | Role |
|-----------|------|
| `EnterpriseEventBus` | Control-plane engine |
| `EventPublisher` / `EventSubscriber` | Publish & subscribe API |
| `EventDispatcher` / `EventRouter` / `EventBroker` | Delivery routing |
| `EventStore` | In-memory durable log (ORM tables for persistence) |
| `EventReplayEngine` | Single / batch / topic / filtered / time-range replay |
| `DeadLetterQueue` + `RetryManager` | Failure handling |
| `TopicManager` | Default + custom topics |
| `EventFilter` / `EventValidator` / Serializer | Filters, signing, serde |
| `EnterpriseEventBusService` | Facades REST/UI |

### Default topics

`system` · `security` · `workflow` · `crm` · `erp` · `knowledge` · `notifications` · `ai` · `agents` · `voice` · `marketplace` · `billing` · `analytics` · `creative` · `platform`

### Event model

`event_id`, `event_type`, `category`, `source_service`, `target_service`, `timestamp`, `correlation_id`, `causation_id`, `priority` (LOW→SYSTEM), `payload`, `metadata`, `security_context`, `tenant_id`, `user_id`, `trace_id`, `signature`, `version`

### REST

Primary: `/api/event-bus`  
Also: `/management/v1/event-bus`  
WebSocket: `/api/event-bus/ws`

Endpoints: topics, events, publish, subscribe, unsubscribe, replay, statistics, dead-letter, retry, traffic, subscribers.

### UI

`/platform-builder/event-bus` — Live Events, Topics, Subscribers, DLQ, Replay, Statistics, Traffic Monitor, Event Inspector.

### Examples

```python
from platform_enterprise_event_bus import enterprise_event_bus

enterprise_event_bus.subscribe(
    subscriber_id="workflow_runtime",
    topic="workflow",
    wildcard="workflow.*",
    handler=on_workflow,
)
await enterprise_event_bus.publish({
    "event_type": "workflow.started",
    "category": "workflow",
    "topic": "workflow",
    "source_service": "svc_workflow_runtime",
    "payload": {"workflow_id": "wf_1"},
})
```

### Tests

```bash
.venv/bin/python -m pytest tests/test_event_bus_36_1.py -vv
```

---

## See also

- [UNIFIED_PLATFORM_STATE_34_2C.md](./UNIFIED_PLATFORM_STATE_34_2C.md)
- [ENTERPRISE_RUNTIME_34_2D.md](./ENTERPRISE_RUNTIME_34_2D.md)
- [VERSION_ENGINE.md](./VERSION_ENGINE.md)
- [EVENT_STORE.md](./EVENT_STORE.md)
- [SYNC_ENGINE.md](./SYNC_ENGINE.md)
- [CROSS_CLIENT_RUNTIME.md](./CROSS_CLIENT_RUNTIME.md)
- [PLATFORM_CORE.md](./PLATFORM_CORE.md)
- [SERVICE_BUILDER.md](./SERVICE_BUILDER.md)
- [SPRINT_36_1_RESULT.md](./SPRINT_36_1_RESULT.md)
- [SPRINT_32_3_RESULT.md](./SPRINT_32_3_RESULT.md)
