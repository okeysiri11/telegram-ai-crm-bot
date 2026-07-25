# Enterprise AI Operating System

Sprint **27.1** / Platform **v9.2.0** — Enterprise Multi-Agent Operating System.

AI Executive Layer that directs, registers, orchestrates and collaborates across the platform agent fleet.

## Architecture

```
platform_ai_os/                              # Multi-Agent OS library
applications/enterprise_hub/enterprise_ai_os/ # Hub suite + API
applications/enterprise_hub/ai_os/enterprise_multi_agent.py  # bridge
src/web/ai-os/                               # Executive Dashboard UI
```

Legacy Autonomous AIOS (Sprint 20.4) remains at `/api/enterprise-aios/v1`.  
Platform AI OS kernel (`applications/ai_os`) remains at `/api/ai-os/v1` (health/kernel/processes/…).  
Sprint 27.1 Multi-Agent routes share `/api/ai-os/v1` without colliding:

## API

Base: **`/api/ai-os/v1`**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/maos/health` | MAOS readiness |
| POST | `/maos/bootstrap` | Bootstrap suite |
| GET | `/maos/inventory` | Architecture inventory |
| GET | `/maos/dashboard` | Executive dashboard |
| GET | `/exec-dashboard` | Executive dashboard alias |
| POST | `/executive` | AI Director: accept & execute goals |
| GET | `/agents` | Agent Registry 2.0 |
| GET/POST | `/agent-bus` | Communication bus |
| POST | `/tasks` | Task orchestrator (DAG) |
| GET/POST | `/memory-layers` | Layered memory manager |
| POST | `/collaborate` | Multi-agent collaboration |

## Capabilities

1. **Executive AI** — decompose, assign, control, merge  
2. **Agent Registry 2.0** — name, role, status, load, capabilities, cost, speed, memory, models  
3. **Communication Bus** — request/response/event/broadcast/stream + priority queue  
4. **Task Orchestrator** — parallel/sequential/conditional + retry/rollback/timeout  
5. **Memory Manager** — short/session/workspace/organization/knowledge/semantic  
6. **Collaboration** — discuss/vote/select_best/critique/merge  
7. **Executive Dashboard** — active agents, queues, load, cost, latency, errors, history  

## Frontend

Route: `/ai-os`
