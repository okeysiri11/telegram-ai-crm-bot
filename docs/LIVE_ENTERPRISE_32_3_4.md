# Live Enterprise Activity & AI Operations — Sprint 32.3.4

## Purpose

Сделать платформу «живой»: Activity Feed, AI Operations, Mission Timeline, Enterprise Health и auto-refresh Dashboard / City — **без** новых AI Engine / Event Bus / Notification System.

## Client aggregator

`src/web/src/live-ops/`

- `fetchLiveEnterpriseSnapshot` — MC activity/timeline/panels, Ops activity, Intelligence recommendations, health probes, notifications, recentActivity
- `useLiveEnterprise` — shared poll (15s) + `liveUpdates` bridge + 2.5s fetch dedupe
- Panels: Activity Feed, AI Ops, Timeline, Health, Recommendations

## Surfaces

| Surface | Change |
|---------|--------|
| `/dashboard` | Live sections + KPI refresh from snapshot |
| `/enterprise-city` | Status from shared snapshot + pulse animations |
| `MissionControlStrip` | Subscribes to `liveUpdates` |

## Performance

- One shared in-flight refresh across Dashboard/City
- Poll 15s via existing `liveUpdates.publish("poll")`
- Lightweight presentational panels; no WebGL / heavy compute

## Extension

- Map more module events into `LiveActivityItem.moduleHint`
- Optional socket-only mode when `VITE_SOCKET_URL` set
- Role-filtered feed via RBAC later

Platform Builder **v1.46.0**.
