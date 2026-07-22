---
title: Telemetry Registry
aliases:
  - Telemetry Registry
tags:
  - drone
  - telemetry
  - registry
generated: 2026-07-22
sprint: "11.3"
---

# Telemetry Registry

## Overview
Registry of Telemetry AI capabilities for live monitoring and analysis.

## Architecture
Part of [[Drone Platform]] Sprint 11.3.

## Components
- Live Telemetry Engine · Recorder · Database · Replay · Timeline
- Signal / Radio / GPS / Battery / Power / Motor / ESC / Sensor / Failsafe analyzers
- Links: [[drone/MAVLINK_REGISTRY]] [[drone/FLIGHT_LOG_REGISTRY]] [[drone/DRONE_DASHBOARD]]

## Relationships
[[Drone Platform]] · [[applications/DRONE_PLATFORM]] · [[INDEX]]

## Responsibilities
Track telemetry intelligence surfaces and analyzers.

## Interfaces
`docs/TELEMETRY_AI.md` · `/api/drone/v1/telemetry/*`

## Events
telemetry_ai_updated

## Related pages
[[DASHBOARD]] · [[sprints/DRONE_PLATFORM]]
