# Dashboard Guide

## Top cards

| Card | Source |
|------|--------|
| System Status | `GET /status` → `systemStatus` |
| Runtime Status | `runtimeServer` |
| Kernel | `kernel` |
| Event Bus | `eventBus` |
| Service Mesh | `serviceMesh` |
| Workflow Engine | `workflowEngine` |
| Memory Usage | `GET /metrics` → heap / RSS |
| CPU Usage | process CPU delta |
| Uptime | `uptimeSec` / `startedAt` |

All cards refresh every **2s** and update immediately when WebSocket broadcasts `status`.

## READY acceptance

With `npm run ados` running, Dashboard should show:

- System Status: **READY**
- Runtime / Kernel / Event Bus / Service Mesh / Workflow Engine: **OK**
- Memory, CPU, Uptime: live numbers (not placeholders after first successful fetch)

If Runtime is down, cards show `…` / DOWN and the header WebSocket status reconnects every 2s.

## Other pages

- **Kernel** — version, init time, modules, health from `/kernel`
- **Services** — table + Restart / Stop / Details
- **Workflows** — Run / Pause / Resume / Cancel / History
- **AI Agents** — live `/agents` + future provider list (labels only)
- **Events** — filter, search, export
- **Logs** — level filter, search, download
- **Settings** — Runtime URLs and connection state
