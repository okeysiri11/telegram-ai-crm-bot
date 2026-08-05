# Provider Gateway (ADOS OS 2.2)

Unified layer for external AI providers. Orchestrator selects providers by capability — never calls adapters directly.

```
User → AI Orchestrator → Provider Gateway → Cursor | OpenAI | Claude | GitHub | Local LLM
```

## Module

`src/providers/` — package `@ados/providers`

Kernel service id: `ados.provider_gateway`

## Provider contract

`connect` · `disconnect` · `health` · `execute` · `capabilities` · `configuration`

## Mock providers (no API keys)

Cursor · OpenAI · Claude · GitHub · Local LLM

## REST

| Method | Path |
|--------|------|
| GET | `/providers` |
| GET | `/providers/status` |
| GET | `/providers/capabilities` |
| POST | `/providers/connect` |
| POST | `/providers/disconnect` |
| POST | `/providers/execute` |

## WebSocket

`provider.connected` · `provider.disconnected` · `provider.health` · `provider.execution` · `provider.error`
