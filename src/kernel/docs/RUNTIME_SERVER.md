# ADOS Runtime Server (Sprint OS 1.5)

## Purpose

Transform ADOS from a one-shot console boot into a **long-running runtime service** with HTTP and WebSocket surfaces.

## Location

`src/kernel/runtime/`

| File | Role |
|------|------|
| `RuntimeServer.ts` | HTTP + WebSocket server, graceful shutdown |
| `types.ts` | API response contracts |
| `index.ts` | Public exports |

## Endpoints

| Method | Path | Response |
|--------|------|----------|
| GET | `/health` | `{ "status": "ok" }` |
| GET | `/status` | version + component OK + services count |
| GET | `/services` | registered kernel services |
| GET | `/workflow` | registered workflow definitions |
| WS | `/ws` | welcome + ping/pong |

## Startup

```bash
# from repository root
npm install
npm run build
npm run ados
```

Or from `src/kernel`:

```bash
npm run ados
```

## Architecture rules

Runtime Server depends **only** on:

- Kernel
- Event Bus
- Service Registry
- Workflow Engine
- Service Mesh (via Kernel)

**No business modules** (CRM, ERP, Marketplace, …).

## Related

- [[SERVER_ARCHITECTURE]]
- [[BOOT_SEQUENCE]]
