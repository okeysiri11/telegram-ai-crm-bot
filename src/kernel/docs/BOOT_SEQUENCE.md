# ADOS Boot Sequence (Sprint OS 1.5)

## Sequence

```text
1. Create Kernel
2. Initialize Service Registry (via BootLoader)
3. Start Event Bus
4. Start Service Mesh
5. Start Workflow Engine (constructed with Kernel)
6. Register core infrastructure services
7. Start Runtime Server (HTTP + WebSocket)
8. Print boot banner
9. Publish BootCompleted (during Kernel.start)
10. System Status: READY
```

## Banner (READY)

```text
=================================
ADOS Enterprise Operating System
Version 1.1.0

Kernel ............... OK
Event Bus ............ OK
Service Mesh ......... OK
Workflow Engine ...... OK
Runtime Server ....... OK

HTTP:
http://localhost:3000

System Status:
READY
=================================
```

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `ADOS_PORT` | `3000` | HTTP listen port |
| `ADOS_HOST` | `0.0.0.0` | Bind address |

## Fail-fast

If a critical infrastructure service is unhealthy, Kernel boot throws and Runtime Server never starts.
