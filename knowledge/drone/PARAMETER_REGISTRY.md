---
title: Parameter Registry
aliases:
  - Parameter Registry
tags:
  - drone
  - parameters
generated: 2026-07-22
sprint: "11.2"
---

# Parameter Registry

## Overview
ArduPilot parameter database and configuration presets.

## Architecture
Part of [[Drone Platform]] firmware intelligence (Sprint 11.2).

## Components
- ArduPilot parameter definitions by vehicle
- Configuration manager presets
- Mission Planner parameter sync

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
