# Multi-Agent Runtime — Sprint 36.7

## Architecture decision

**Canonical SoR:** `platform_orchestrator` (existing multi-agent execution layer).  
**Rejected:** new `platform_multi_agent` / `platform_core/` package.

Sprint 36.7 productizes an **Enterprise Multi-Agent Runtime** *inside* `platform_orchestrator/`:

| Layer | Module |
|-------|--------|
| Existing SoR | `orchestrator.py`, `agent_registry.py`, `message_bus.py` |
| Runtime models | `runtime_models.py` |
| Engine | `multi_agent_engine.py` |
| Facade | `multi_agent_service.py` |
| HTTP | `multi_agent_router.py` |

```
Goal / Voice / Workflow / AI Runtime
                ↓
      MultiAgentRuntimeService
                ↓
   plan → orchestrate (mode) → task queue → agents
                ↓
   shared context/memory · message bus · Event Bus
                ↓
         result aggregator / supervisor
```

---

## Agent Registry

Register agents with capabilities, skills, permissions, availability, and health monitoring. Seeds builtin vertical agents plus planner/supervisor/worker specialists.

## Orchestrator

- Task decomposition (planner)
- Coordinator (collaboration modes)
- Supervisor (hierarchical / supervisor-worker)
- Result aggregator

## Communication

- Direct messaging
- Publish/subscribe topics
- Shared session context & memory
- Event-driven via AgentMessageBus + Enterprise Event Bus

## Collaboration Modes

`sequential` · `parallel` · `hierarchical` · `swarm` · `supervisor_worker`

## Task Runtime

Queue · retries · checkpoints · cancellation · timeout · scheduling

## REST API

| Prefix | Purpose |
|--------|---------|
| `/api/agents/*` | Primary |
| `/api/multi-agent/*` | Alias |
| `/management/v1/agents/*` | Management dual-prefix |

## Database (Alembic `q0k123456789`)

`agent_registry` · `agent_tasks` · `agent_messages` · `agent_sessions` · `agent_plans` · `agent_execution` · `agent_statistics`

## UI

`/platform-builder/multi-agent`

Pages: Agent Dashboard · Live Execution · Task Graph · Planner · Communication · Statistics

## Integrations

AI Runtime · Project Memory · Context Engine · Workflow Runtime · Event Bus · Service Builder (`svc_multi_agent_runtime`) · Voice Command Center
