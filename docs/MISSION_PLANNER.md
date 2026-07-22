# Mission Planner Integration (Sprint 11.2)

**Bridge:** `applications/drone_platform/firmware/mission_planner/`  
**API prefix:** `/api/drone/v1/mission-planner/`

## Overview

Mission Planner bridge for engineering workflows: parameter sync, mission import/export, waypoint/geofence/rally editors, flight-mode and configuration profiles, and mission templates.

## Features

- Mission Planner Bridge
- Parameter Synchronizer
- Mission Import / Export
- Waypoint Editor
- GeoFence Editor (via mission service)
- Rally Point Manager
- Flight Mode Editor (profiles)
- Configuration Profiles
- Mission Templates

## REST

- `POST /mission-planner/import`
- `POST /mission-planner/export`
- `POST /mission-planner/missions/{mission_id}/waypoints`

## Related

- [DRONE_FIRMWARE.md](DRONE_FIRMWARE.md)
- [FIRMWARE_WORKFLOW.md](FIRMWARE_WORKFLOW.md)
