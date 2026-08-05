# ADOS Server Architecture (Sprint OS 1.5)

## Diagram

```text
┌─────────────────────────────────────────────┐
│              npm run ados (main.ts)         │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│                   Kernel                    │
│  Registry · Event Bus · Mesh · Workflow     │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│              Runtime Server                 │
│         HTTP :3000  ·  WebSocket /ws        │
└───────┬─────────┬─────────┬─────────┬───────┘
        │         │         │         │
   /health   /status  /services  /workflow
```

## Dependency direction

```text
runtime → Kernel / registry / workflow (via Kernel)
       ↛ CRM / ERP / Marketplace / AI Studio
```

## Graceful shutdown

1. SIGINT / SIGTERM received  
2. Close WebSocket clients  
3. Stop HTTP server  
4. `kernel.dispose()`  
5. `process.exit(0)`

## Remote-ready

HTTP and WebSocket are the first external I/O boundary. Future providers and UIs attach here — not inside Core.
