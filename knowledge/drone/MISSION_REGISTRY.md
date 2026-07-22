---
title: Mission Registry
aliases:
  - Mission Registry
tags:
  - drone
  - missions
generated: 2026-07-22
sprint: "11.2"
---

# Mission Registry

## Overview
Mission library, templates, and Mission Planner bridge artifacts.

## Architecture
Part of [[Drone Platform]] firmware intelligence (Sprint 11.2).

## Components
- Mission service waypoints/geofences/rally
- ArduPilot mission library
- MP import/export

## Relationships
[[Drone Platform]] · [[applications/DRONE_PLATFORM]] · [[ARCHITECTURE_DASHBOARD]] · [[INDEX]]

## Responsibilities
Keep Obsidian knowledge synchronized with drone firmware capabilities.

## Interfaces
Docs: `docs/DRONE_FIRMWARE.md`, `docs/ARDUPILOT.md`, `docs/MISSION_PLANNER.md`

## REST APIs
`/api/drone/v1/firmware/*`, `/ardupilot/*`, `/mission-planner/*`

## Events
firmware_intelligence_updated

## Future roadmap
[[ROADMAP]] · Drone 11.3+ manufacturing/fleet depth

## References
Repository docs under `docs/`

## Related pages
[[DASHBOARD]] · [[sprints/DRONE_PLATFORM]]
