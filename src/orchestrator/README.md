# AI Orchestrator (ADOS OS 2.1)

Central brain of the platform. All AI agents communicate **only** through the Orchestrator.

```
User → AI Orchestrator → Developer | Business | Marketing | Research | CRM | Finance | Production
```

## Location

`src/orchestrator/` — package `@ados/orchestrator`

Registered at Kernel boot as service `ados.orchestrator` via `BootLoader.extraServices` (Kernel class stays free of agent logic).

## Agent contract

Every agent implements:

- `execute(input)`
- `health()`
- `capabilities()`
- `status()` → Idle | Running | Busy | Offline | Error

## REST (Runtime)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/agents` | Agent snapshots + orchestrator summary |
| GET | `/agents/status` | Live orchestrator + agents |
| GET | `/agents/logs` | Agent execution history |
| GET | `/agents/metrics` | Aggregate + per-agent metrics |
| POST | `/agents/run` | Run task on a specific agent |
| POST | `/orchestrator/task` | Route task by type/capability |

WebSocket events: `agent.status`, `agent.task` (plus existing `status` every 2s).

## Auto-registration

On `OrchestratorService.start()`, builtin agents register:

- Developer (`cursor`)
- Business (`openai`)
- Marketing (`claude`)
- Research (`openai`)
- CRM (`local`)
- Finance (`local`)
- Production (`github`)

## Control Center

Dashboard shows **AI Orchestrator** card. **AI Agents** page shows status, queue, provider, response time, health, metrics, and Agent Logs.
