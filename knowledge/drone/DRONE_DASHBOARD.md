---
title: Drone Dashboard
aliases:
  - Drone Dashboard
tags:
  - drone
  - dashboard
generated: 2026-07-22
sprint: "11.4"
---

# Drone Dashboard

## Overview
Readiness dashboard for Drone Platform through Sprint 11.4 (Vision / Navigation / Autonomy).

## Architecture
Part of [[Drone Platform]].

## Components
- MAVLink Intelligence Ready
- Telemetry AI Ready
- Flight Log Analysis Ready
- Mission Intelligence Ready
- Ground Control Integration Ready
- Drone Diagnostics Ready
- Computer Vision Ready
- Navigation AI Ready
- Autonomous Flight Ready
- SLAM Ready
- Simulation Ready
- Links: [[drone/MAVLINK_REGISTRY]] [[drone/TELEMETRY_REGISTRY]] [[drone/FLIGHT_LOG_REGISTRY]] [[drone/MISSION_REGISTRY]] [[drone/VISION_REGISTRY]] [[drone/NAVIGATION_REGISTRY]] [[drone/MAPPING_REGISTRY]] [[drone/AUTONOMY_REGISTRY]] [[drone/FIRMWARE_DASHBOARD]]

## Relationships
[[Drone Platform]] · [[ARCHITECTURE_DASHBOARD]] · [[INDEX]]

## Responsibilities
Surface drone platform readiness in Obsidian knowledge.

## Interfaces
Docs: `docs/MAVLINK.md`, `docs/TELEMETRY_AI.md`, `docs/COMPUTER_VISION.md`, `docs/NAVIGATION_AI.md`, `docs/AUTONOMOUS_FLIGHT.md`, `docs/SLAM_MAPPING.md`

## REST APIs
`/api/drone/v1/mavlink/*`, `/telemetry/*`, `/vision/*`, `/navigation/*`, `/mapping/*`, `/autonomy/*`, `/simulation/*`

## Events
drone_vision_autonomy_updated

## Related pages
[[INDEX]] · [[sprints/DRONE_PLATFORM]]
