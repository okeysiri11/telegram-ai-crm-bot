# Cross-Client Runtime

**Sprint:** 34.2C  
**Module:** `platform_state.clients` + `platform_state.service`

---

## One runtime

All clients operate on the **same** `PlatformStateService` instance (`platform_state`).

| Client | Adapter |
|--------|---------|
| Telegram | `telegram_runtime` |
| Web | `web_runtime` |
| Desktop | `desktop_runtime` |
| Mobile | `mobile_runtime` |
| API | `api_runtime` |
| AI Agents | `ai_runtime` |

Each adapter is a thin `ClientRuntimeAdapter(client_id)` that stamps `source_client` and delegates to the shared service.

---

## Shared entities

### Conversation

`ConversationEngine` holds one Conversation with:

- messages, attachments, participants
- context, memory_refs, active_agents
- status, history
- `client_bindings` (`telegram:chat_id`, `web:thread_id`, …)

Telegram chat and Web/AI Studio chat that bind to the same conversation continue the **same** thread.

### Memory

Scopes: `user` · `workspace` · `conversation`

Agents never keep isolated client memory. Telegram AI / Web AI / Desktop AI share the same store via PlatformState.

### Tasks / Calendar / CRM / Files / Notifications

Created on any client → SyncEngine event → visible in deltas and realtime on every other client.

---

## Identity

One login / one identity remains **platform_identity** (34.2A). Platform state references `user_id` + `telegram_id`; it does not fork auth.

Menus / roles / workspaces remain **platform_registry** (34.2B).

---

## Offline

```
Offline client → reconnect → register_cursor / delta(since=revision) → apply events
```

Conflict resolution uses `ConflictResolutionEngine` (`platform_state.conflict_engine`):

`version_reject` · `last_write_wins` · `field_merge` · `business_rule` · `manual_review`

`platform_state.conflict.ConflictResolver` remains a compatibility facade (reject_stale / accept_incoming).

---

## Audit

`platform_state_audit` records who / when / source_client / before / after. Realtime handler appends entries on each state event.

---

## Compatibility

| Surface | Behavior |
|---------|----------|
| Telegram handlers | keep working; prefer `telegram_runtime` for new writes |
| Web | keep working; prefer `web_runtime` / snapshot API |
| Existing routes | unchanged; additive `/platform-state*` |
| TaskService / CalendarService | still SoR; adapters wrap |

---

## Tests

`tests/test_platform_state_34_2c.py` covers:

- Telegram → Web tasks
- Web → Telegram notifications
- Desktop → Telegram calendar
- Mobile → Web CRM
- Conversation / memory / file / workspace sync
- Offline delta
- Conflict resolver
