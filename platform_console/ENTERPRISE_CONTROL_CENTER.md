# Enterprise Control Center

ADOS OS visual operating system UI.

## Role

```
Browser → Enterprise Control Center (React) → Runtime API → Kernel → Event Bus → Service Mesh → Workflow Engine
```

The Control Center never imports Kernel internals. It talks only to Runtime over REST and WebSocket.

## Location

`platform_console/` — Vite + React + TypeScript + Tailwind.

## Run

```bash
# Terminal 1 — Runtime + Kernel
npm run ados

# Terminal 2 — Control Center
npm run console
```

Open http://localhost:5173

## Runtime endpoints used

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/status` | Component READY map |
| GET | `/metrics` | Memory / CPU / uptime |
| GET | `/kernel` | Kernel info |
| GET | `/services` | Service table |
| POST | `/services/:id/stop` | Stop service |
| POST | `/services/:id/restart` | Restart service |
| GET | `/workflow` | Definitions + instances |
| POST | `/workflow/:id/run` | Start workflow |
| POST | `/workflow/instances/:id/pause` | Pause |
| POST | `/workflow/instances/:id/resume` | Resume |
| POST | `/workflow/instances/:id/cancel` | Cancel |
| GET | `/workflow/instances/:id/history` | History |
| GET | `/events` | Event Bus buffer |
| GET | `/logs` | Runtime logs |
| GET | `/agents` | Registered agents |
| WS | `/ws` | Live status + events |

Auto-refresh: **2 seconds**. WebSocket invalidates React Query on `status` / `event` messages.

## Configuration

| Env | Default |
|-----|---------|
| `VITE_RUNTIME_URL` | `http://localhost:3000` |
| `VITE_RUNTIME_WS` | `ws://localhost:3000/ws` |

Vite also proxies API paths to Runtime during `npm run console`.

## Navigation

Dashboard · Kernel · Services · Workflows · AI Agents · Knowledge · Logs · Events · Marketplace · Settings

Knowledge and Marketplace are reserved shells (no mock data) for future Enterprise modules.

## Design

Dark enterprise theme, glass cards, live status dots. Inspired by Datadog / Grafana / Azure Portal density without copying branding.

## Architecture constraints

- No business logic (CRM/ERP) in Kernel or Control Center core.
- Future modules register as Kernel services; Control Center discovers them via Runtime.
- Do not break Kernel contracts when adding UI pages.
