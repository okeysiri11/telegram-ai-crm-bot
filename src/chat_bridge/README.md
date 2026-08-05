# ChatGPT Integration Bridge (ADOS OS 4.0)

Middleware between ChatGPT and Cursor.

```
ChatGPT → Chat Bridge → Orchestrator → Provider Gateway → Cursor Provider
```

## Module

`src/chat_bridge/` — `@ados/chat-bridge`

## REST

| Method | Path |
|--------|------|
| POST | `/chat/task` |
| POST | `/chat/run` |
| GET | `/chat/history` |
| GET | `/chat/tasks` |
| GET | `/chat/session` |
| GET | `/chat/status` |

## Voice

Fulfilled by `@ados/voice` (ADOS OS 4.1). See `docs/ados_os/voice_module.md`.

