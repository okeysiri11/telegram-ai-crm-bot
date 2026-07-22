# Drone Platform — Foundation (Sprint 11.1)

**Version:** `1.3.0-alpha`  
**Status:** Vision Navigation Autonomy Alpha  
**API prefix:** `/api/drone/v1`

Engineering ERP + AI workspace for UAV development, manufacturing, configuration, testing, maintenance, and fleet management. Sprint **11.2** Firmware Intelligence. Sprint **11.3** MAVLink/Telemetry. Sprint **11.4** Computer Vision, Navigation AI, SLAM, Autonomous Flight, and Simulation.

See also: [DRONE_FIRMWARE.md](DRONE_FIRMWARE.md), [MAVLINK.md](MAVLINK.md), [TELEMETRY_AI.md](TELEMETRY_AI.md), [COMPUTER_VISION.md](COMPUTER_VISION.md), [NAVIGATION_AI.md](NAVIGATION_AI.md), [AUTONOMOUS_FLIGHT.md](AUTONOMOUS_FLIGHT.md), [SLAM_MAPPING.md](SLAM_MAPPING.md).

## Scope

This application lives under `applications/drone_platform/` only. It does **not** modify Platform Core, Ecosystem, Agro Marketplace, Port ERP, or Auto Marketplace.

## Package layout

```
applications/drone_platform/
  api/ models/ registry/ projects/ engineering/ firmware/
  mavlink/ missions/ mission_intelligence/ telemetry/ flight_logs/
  diagnostics/ gcs/ vision/ navigation/ mapping/ autonomy/
  visualization/ inventory/ warehouse/ manufacturing/
  simulation/ ai/ documentation/ integrations/ analytics/ shared/
```

## Capabilities

### Component registry

Catalogs UAVs and component types: frames, motors, ESC, flight controllers, GPS, compass, telemetry radios, ELRS, receivers, cameras, VTX, antennas, batteries, chargers, sensors, payloads, servos, power modules, airspeed sensors, rangefinders, companion computers.

### Engineering projects

Projects with versions, BOM, CAD/PCB references, wiring diagrams, assembly instructions, engineering documentation, revision history, and notes.

### Firmware workspace

Supports ArduPilot, PX4, INAV, and Betaflight projects with catalog/versions, parameter compare/backup/restore/templates, configuration import/export, firmware backup/restore, log organization, and firmware documentation.

### MAVLink / Telemetry / Flight logs (11.3)

MAVLink manager/router/parser/registries/protocols, Telemetry AI analyzers, flight log intelligence (including PX4 ULog architecture-ready), AI diagnostics, mission intelligence, GCS bridges, and visualization charts.

### Vision / Navigation / Autonomy (11.4)

Computer vision cameras/pipelines/detection/tracking, Navigation AI, SLAM/mapping, autonomous flight modes, AI flight assistant, SITL-ready simulation.

### Mission planning

Missions with waypoints, rally points, geofences, payload configuration, flight profiles, templates, and history.

### Inventory & warehouse

Warehouses, suppliers, purchasing, stock, reservations, serial numbers, batches, and component lifecycle.

### Documentation

Manuals, engineering wiki, assembly guides, maintenance procedures, wiring diagrams, firmware notes, and build history.

### AI engineering assistant

Agents for firmware analysis, configuration review, parameter explanation, log interpretation, hardware compatibility, troubleshooting, engineering documentation, build recommendations, and diagnostics.

Policy: engineering assistance only — not intended for misuse.

## REST API

| Area | Paths |
|------|--------|
| Health | `GET /api/drone/v1/health` |
| Registry | `/registry`, `/registry/types`, `/registry/components`, `/registry/uavs` |
| Projects | `/projects`, `/projects/{id}/versions` |
| Engineering | `/engineering/{project_id}` |
| Firmware | `/firmware`, `/firmware/projects`, `/firmware/parameters`, `/firmware/compare`, `/firmware/templates`, `/firmware/export`, `/firmware/import`, `/firmware/backup`, `/firmware/restore` |
| Missions | `/missions`, `/missions/{id}/waypoints` |
| Telemetry | `/telemetry/sessions`, `/telemetry/sessions/{id}/samples` |
| Inventory | `/inventory/warehouses`, `/suppliers`, `/stock`, `/reservations`, `/purchase-orders` |
| Documentation | `/documentation` |
| AI | `/ai`, `/ai/assist` |

## Bridges

- `integrations/platform_bridge.py` — optional Platform Core hooks (stub-safe)
- `integrations/ecosystem_bridge.py` — optional Ecosystem tenant hooks (stub-safe)

## Sprint 11.1 completion checklist

- Drone Platform Foundation Ready
- Engineering Ready
- Firmware Workspace Ready
- Mission Planning Ready
- Inventory Ready
- AI Engineering Assistant Ready
- Version `1.0.0-alpha`
