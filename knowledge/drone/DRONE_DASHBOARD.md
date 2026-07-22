---
title: Drone Dashboard
aliases:
  - Drone Dashboard
tags:
  - drone
  - dashboard
generated: 2026-07-22
sprint: "11.5"
---

# Drone Dashboard

## Overview
Readiness dashboard for Drone Platform through Sprint 11.5 (Engineering Suite).

## Architecture
Part of [[Drone Platform]].

## Components
- Computer Vision / Navigation / Autonomy Ready (11.4)
- Drone Engineering Ready
- Battery Engineering Ready
- PCB Engineering Ready
- CAD Integration Ready
- Engineering AI Ready
- Links: [[drone/ENGINEERING_REGISTRY]] [[drone/COMPONENTS_REGISTRY]] [[drone/BATTERY_REGISTRY]] [[drone/CAD_REGISTRY]] [[drone/PCB_REGISTRY]] [[drone/KNOWLEDGE_GRAPH]] [[drone/VISION_REGISTRY]] [[drone/MAVLINK_REGISTRY]] [[drone/FIRMWARE_DASHBOARD]]

## Relationships
[[Drone Platform]] · [[ARCHITECTURE_DASHBOARD]] · [[INDEX]] · [[Knowledge Graph]]

## Interfaces
Docs: `docs/ENGINEERING.md`, `docs/AIRFRAME.md`, `docs/POWER_SYSTEM.md`, `docs/BATTERY_ENGINEERING.md`, `docs/PCB_ENGINEERING.md`, `docs/CAD_INTEGRATION.md`

## REST APIs
`/api/drone/v1/engineering/*`

## Events
drone_engineering_suite_updated

## Related pages
[[INDEX]] · [[sprints/DRONE_PLATFORM]]
