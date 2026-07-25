# AI Operations Center

Sprint **29.1** / Platform Builder **v1.8.0** / Operations Center **1.0**

Real-time visual control room for the entire AI Organization.

**Does not execute business logic.** It visualizes the Logical Layer in real time.

## Module

Platform Builder → AI Operations Center (`/platform-builder/operations`)

API: `/api/platform-builder/v1/operations/*`

## Architecture

Every platform object exposes:

- Logical State
- Visual State
- Visual ID
- Status
- Relationships
- Lifecycle

## Steps

1. Operations Dashboard — Organizations · Departments · AI Teams · Specialists · Concierge · Workflows · Tasks · Documents · Knowledge · Live Sessions
2. Live Status Engine — Idle · Working · Thinking · Learning · Analyzing · Collaborating · Waiting · Completed · Offline
3. Realtime Activity — Tasks · Processes · Knowledge · Workflows · AI Communication · Organization Activity
4. Visual ID Support — Logical ID · Visual ID · Object Type · Current State
5. Wait Experience Engine — Informative waiting (never empty) without misrepresenting state
6. Team Overview — Departments · Teams · Members · Workload · Availability · Performance
7. System Health — Platform · Registry · AI · Module · Performance
8. Foundation for AI City — Visual Layer · Animated Objects · Future Positioning / Movement / Live Organization
9. Summary — Organization · AI · Performance · Health
10. Create — Register Operations Center · Visual Layer · Status Engine

## Layout

- Backend: `applications/platform_builder/operations_center/`
- Frontend: `src/web/platform-builder/operations/`
- Knowledge: `knowledge/operations/`
- Related: [VISUAL_LAYER.md](./VISUAL_LAYER.md)
- Tests: `tests/test_operations_center_29_1.py`
