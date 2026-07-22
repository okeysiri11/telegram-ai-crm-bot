---
title: Mission Registry
aliases:
  - Mission Registry
tags:
  - drone
  - missions
generated: 2026-07-22
sprint: "11.3"
---

# Mission Registry

## Overview
Mission library, templates, Mission Planner bridge, and Mission Intelligence (11.3).

## Architecture
Part of [[Drone Platform]] (Sprints 11.2–11.3).

## Components
- Mission service waypoints/geofences/rally
- ArduPilot mission library
- MP import/export
- Mission Intelligence: validator, optimizer, terrain, risk, battery/range, RTH, emergency landing, replay, comparison, scoring
- Links: [[drone/TELEMETRY_REGISTRY]] [[drone/DRONE_DASHBOARD]]

## Relationships
[[Drone Platform]] · [[applications/DRONE_PLATFORM]] · [[ARCHITECTURE_DASHBOARD]] · [[INDEX]]

## Responsibilities
Keep mission planning and intelligence knowledge synchronized.

## Interfaces
Docs: `docs/MISSION_PLANNER.md`, `docs/DRONE_DIAGNOSTICS.md`

## REST APIs
`/api/drone/v1/missions/*`, `/mission-planner/*`, `/mission-intel/*`

## Events
mission_intelligence_updated

## Future roadmap
[[ROADMAP]]

## References
Repository docs under `docs/`

## Related pages
[[DASHBOARD]] · [[sprints/DRONE_PLATFORM]] · [[drone/DRONE_DASHBOARD]]
