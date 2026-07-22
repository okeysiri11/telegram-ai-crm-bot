---
title: Drone Dashboard
aliases:
  - Drone Dashboard
tags:
  - drone
  - dashboard
generated: 2026-07-22
sprint: "11.3"
---

# Drone Dashboard

## Overview
Readiness dashboard for Drone Platform MAVLink / Telemetry / Diagnostics (Sprint 11.3).

## Architecture
Part of [[Drone Platform]].

## Components
- MAVLink Intelligence Ready
- Telemetry AI Ready
- Flight Log Analysis Ready
- Mission Intelligence Ready
- Ground Control Integration Ready
- Drone Diagnostics Ready
- Links: [[drone/MAVLINK_REGISTRY]] [[drone/TELEMETRY_REGISTRY]] [[drone/FLIGHT_LOG_REGISTRY]] [[drone/MISSION_REGISTRY]] [[drone/FIRMWARE_DASHBOARD]]

## Relationships
[[Drone Platform]] · [[ARCHITECTURE_DASHBOARD]] · [[INDEX]]

## Responsibilities
Surface 11.3 readiness in Obsidian knowledge.

## Interfaces
Docs: `docs/MAVLINK.md`, `docs/TELEMETRY_AI.md`, `docs/FLIGHT_LOG_ANALYSIS.md`, `docs/DRONE_DIAGNOSTICS.md`

## REST APIs
`/api/drone/v1/mavlink/*`, `/telemetry/*`, `/flight-logs`, `/diagnostics`, `/mission-intel/*`, `/gcs/*`, `/visualization/*`

## Events
drone_telemetry_intelligence_updated

## Related pages
[[INDEX]] · [[sprints/DRONE_PLATFORM]]
