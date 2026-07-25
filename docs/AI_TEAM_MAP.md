# AI Team Map

Sprint **29.2** / Platform Builder **v1.9.0** / Team Map **1.0**

Live Organization Map for the complete AI Organization. Receives updates from the Visual Event Bus and displays current state of every organization object.

## Module

Platform Builder → AI Team Map (`/platform-builder/team-map`)

API: `/api/platform-builder/v1/team-map/*`

## Steps

1. Live Organization Map — Owner · Concierge · Departments · Teams · Specialists · Connections · Hierarchy
2. AI Cards — Avatar · Name · Role · Specialization · Department · Status · Task · Workload · Knowledge · Health
3. Live Status — Idle · Working · Thinking · Learning · Collaborating · Reviewing · Waiting · Offline · Completed
4. Workload Engine — Load · Queue · Response Time · Availability · Utilization · Balanced Work
5. Relationship Map — Department · Collaboration · Knowledge · Workflow · Task · Structure
6. Live Activity — Conversations · Knowledge · Tasks · Decisions · Workflow Progress
7. Visual Event Bus — AI · Workflow · Task · Knowledge · Organization · Registry events
8. Visual Objects — Logical ID · Visual ID · Position · Visual / Relationship / Animation state
9. AI City APIs — Movement · Animation · Position · Visual Object
10. Create — Register Organization Map · Relationship Engine · Workload Engine · Animation Layer

## UI

Animated Connections · Interactive Cards · Zoom · Pan · Search · Filters · Department Focus

## Layout

- Backend: `applications/platform_builder/team_map/`
- Frontend: `src/web/platform-builder/team-map/`
- Knowledge: `knowledge/operations/team_map/`
- Related: [LIVE_ORGANIZATION.md](./LIVE_ORGANIZATION.md)
- Tests: `tests/test_team_map_29_2.py`
