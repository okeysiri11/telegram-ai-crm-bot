# Platform Event Store

**Sprint:** 34.2D · **Stabilized:** 35.0 · **Module:** `platform_state.event_store.PlatformEventStore`  
**Policy:** Durable log only — does **not** replace `PlatformEventBus`

---

## Role

Every business action becomes an immutable sequenced event:

`UserCreated`, `TaskCompleted`, `CalendarChanged`, `MessageSent`, `FileUploaded`,  
`WorkspaceChanged`, `ConversationUpdated`, `NotificationSent`, …

Stored permanently via **JSONL + in-memory indexes** (default).

Optional Postgres dual-write (Sprint 35.1): set `ADOS_EVENT_STORE_BACKEND=postgres`
(requires `platform_state_events` table from migration `h1b234567890`). Public API unchanged.

---

## Write path

```
Adapter / VersionEngine
    → SyncEngine.publish_change
    → EventStore.append  (durable)
    → PlatformEventBus.publish  (in-process)
    → RealtimeHub
```

---

## Replay

```python
from platform_state.replay import replay_engine

replay_engine.replay_all()
replay_engine.replay_entity("lead", id)
replay_engine.replay_workspace("crm")
replay_engine.time_travel(at_or_before="2026-08-02T12:00:00+00:00")
replay_engine.audit_replay(entity_type="lead", entity_id=id)
```

---

## Config

| Env | Effect |
|-----|--------|
| `ADOS_PLATFORM_EVENT_STORE` | JSONL file path (`.sqlite3` suffix auto-maps to `.jsonl`) |
| `ADOS_EVENT_STORE_MEMORY=1` | In-memory store |
| `ADOS_EVENT_STORE_DURABLE=1` | Force file store even under pytest |
| `ADOS_EVENT_STORE_BACKEND=postgres` | Dual-write to `platform_state_events` (optional HA) |
| `ADOS_VERSION_HEADS` | Optional VersionEngine heads checkpoint path |

Default file: `~/.ados/platform_event_store.jsonl`
