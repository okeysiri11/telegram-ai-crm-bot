# Owner God Mode

**Sprint:** 31.1 (web Visual Polish track)  
**Surfaces:** Owner Dashboard · Enterprise City Owner panel · `/platform-builder/god-mode`

## Purpose

Give the platform Owner a single visual ops view over health and capacity — without a second monitoring stack.

## Metrics (from `deriveGodModeMetrics`)

| Metric | Source |
|---|---|
| Platform Health | `derivePlatformHealth()` |
| AI Runtime | runtime status + active agents |
| Queues | job manager waiting/running |
| Workers | busy / total |
| Users / Organizations | Identity routes |
| Active Sessions | runtime metrics |
| Errors / Warnings | notification store |
| CPU / Memory | runtime snapshot |
| API / Database / Redis | health service tones |

## Entry points

1. **Owner Dashboard** (`/owner`) — full God Mode strip + role polish widgets  
2. **Enterprise City** — Owner panel when Owner view is active  
3. **Control Center** — `/platform-builder/god-mode` (existing PB Control Center)

## Rules

- Extend `platformHealth` / `runtimeEngine` / `jobManager` — never fork health
- Russian labels in nav: **Режим владельца**
- Deep-link chips go to existing module routes (`/health`, `/identity/*`, runtime)

## Related

- `OWNER_CITY_MODE.md`, `OWNER_DASHBOARD.md`
- `ENTERPRISE_CITY_UI.md`, `SPRINT_31_1_RESULT.md`
