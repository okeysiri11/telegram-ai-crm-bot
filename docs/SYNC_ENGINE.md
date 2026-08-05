# Sync Engine

**Sprint:** 34.2C  
**Module:** `platform_state.sync_engine.SyncEngine`

---

## Role

The Sync Engine is the cross-client synchronization layer on top of the canonical **PlatformEventBus**.

```
Client write
    → Domain Adapter
    → SyncEngine.publish_change
    → PlatformEventBus
    → RealtimeHub (+ in-process sync subscribers)
    → Web / Desktop / Mobile / AI / API
```

---

## Capabilities

| Capability | API |
|------------|-----|
| Publish change | `await sync_engine.publish_change(event)` |
| In-process subscribe | `sync_engine.subscribe_client(id, handler)` |
| Offline cursor | `register_cursor(client_id, last_revision=…)` |
| Delta catch-up | `delta_since(last_revision, slices=[…])` |
| Status | `sync_engine.status()` |

---

## Offline / reconnect

1. Client stores `revision` from last successful sync.
2. On reconnect, call `GET /management/v1/platform-state/delta?since=<revision>`.
3. Engine returns **only events after** that revision (recent window, maxlen 500).
4. Unknown cursor → safe catch-up of the recent window filtered by slices.

Same path for Telegram, Desktop, and Mobile.

---

## Live path

Every published `PlatformStateChangedEvent` (and typed aliases) is:

1. Appended to the recent delta log
2. Published on `PlatformEventBus`
3. Handled by `PlatformStateRealtimeHandler` → channels `platform_state`, `system`, plus slice-specific channel

No manual refresh required for subscribed realtime clients.

---

## Guarantees

- Does **not** replace domain SoR (tasks/calendar/CRM stay in existing services).
- Does **not** create a second event bus.
- Ordering within the process is FIFO on the recent deque; revision tokens are content hashes chained from prior revision.

---

## Example

```python
from platform_state.clients import telegram_runtime, web_runtime

task = await telegram_runtime.create_task(title="Call", creator_telegram_id=1)
delta = web_runtime.delta(None, slices=["tasks"])
assert any(e["entity_id"] == task["task_id"] for e in delta["events"])
```
