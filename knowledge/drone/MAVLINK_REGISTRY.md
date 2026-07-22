---
title: MAVLink Registry
aliases:
  - MAVLink Registry
tags:
  - drone
  - mavlink
  - registry
generated: 2026-07-22
sprint: "11.3"
---

# MAVLink Registry

## Overview
Message/command registries and MAVLink intelligence components.

## Architecture
Part of [[Drone Platform]] Sprint 11.3.

## Components
- Manager · Router · Parser · Message/Command registries
- Heartbeat · Parameter/FTP/Mission protocols · Streams · Discovery · Connections
- Links: [[drone/TELEMETRY_REGISTRY]] [[drone/FLIGHT_LOG_REGISTRY]]

## Relationships
[[Drone Platform]] · [[INDEX]]

## Responsibilities
Keep MAVLink capability inventory synchronized.

## Interfaces
`docs/MAVLINK.md` · `/api/drone/v1/mavlink/*`

## Events
mavlink_intelligence_updated

## Related pages
[[drone/DRONE_DASHBOARD]]
