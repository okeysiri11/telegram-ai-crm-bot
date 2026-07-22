---
title: Mission Registry
aliases:
  - Mission Registry
tags:
  - drone
  - missions
generated: 2026-07-22
sprint: "11.8"
---

# Mission Registry

## Overview
Mission library, templates, Mission Planner bridge, Mission Intelligence (11.3), Mission Operations Center (11.7), and cloud remote mission control (11.8).

## Architecture
Part of [[Drone Platform]] (Sprints 11.2–11.8).

## Components
- Mission service waypoints/geofences/rally
- ArduPilot mission library / MP import/export
- Mission Intelligence + Mission Center (ops missions, scheduler, archive, reports)
- Cloud remote mission upload / Global Command mission map
- Links: [[drone/MISSION_OPS_REGISTRY]] [[drone/CLOUD_REGISTRY]] [[drone/MISSION_OPS_DASHBOARD]] [[drone/CLOUD_DASHBOARD]] [[drone/TELEMETRY_REGISTRY]] [[drone/DRONE_DASHBOARD]]

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
