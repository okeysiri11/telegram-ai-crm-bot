# Drone Integration Guide — Sprint 31.4

## Principle

Do **not** invent a parallel Drone OS. `drone_platform` already provides projects, registry, manufacturing, ops, telemetry, ecosystem dashboards, and AI assist.

## API prefixes (existing)

| Prefix | Role |
|--------|------|
| `/api/drone/v1` | Projects, aircraft, fleet, production, warehouse, testing, missions, telemetry, analytics |
| `/api/precision-agriculture/v1` | Optional agro survey missions (`/drone`) |
| `/api/enterprise-isam/v1` | Auth/identity |
| `/api/platform-builder/v1` | Concierge, AI Team, Mission Control |

## Pitfalls

- Dual mission stores: prefer `/ops/missions` for Mission Control (`ops_mission_id`, `lat`/`lon`).
- Dual aircraft stores: `/registry/uavs` vs `/ops/fleet` IDs are not auto-linked.
- Create warehouse via `/inventory/warehouses` before manufacturing receive.
