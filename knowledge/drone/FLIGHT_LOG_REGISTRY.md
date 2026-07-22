---
title: Flight Log Registry
aliases:
  - Flight Log Registry
tags:
  - drone
  - flight-logs
  - registry
generated: 2026-07-22
sprint: "11.3"
---

# Flight Log Registry

## Overview
Supported flight log formats and analysis readiness.

## Architecture
Part of [[Drone Platform]] Sprint 11.3.

## Components
- `.bin` · `.tlog` · `.log` · `.dataflash`
- MAVLink / Mission Planner / QGroundControl / ArduPilot DataFlash
- PX4 ULog (architecture ready)
- Links: [[drone/TELEMETRY_REGISTRY]] [[drone/MAVLINK_REGISTRY]]

## Relationships
[[Drone Platform]] · [[INDEX]]

## Responsibilities
Catalog log parsers and AI analysis outputs.

## Interfaces
`docs/FLIGHT_LOG_ANALYSIS.md` · `/api/drone/v1/flight-logs`

## Events
flight_log_ingested

## Related pages
[[drone/DRONE_DASHBOARD]] · [[sprints/DRONE_PLATFORM]]
