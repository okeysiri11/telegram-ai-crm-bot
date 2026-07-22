# MAVLink Intelligence — Sprint 11.3

**Module:** `applications/drone_platform/mavlink/`  
**Version:** Drone Platform `1.2.0-alpha`

## Overview

MAVLink intelligence layer for communication analysis, routing, registries, protocols, vehicle discovery, and telemetry streams. This is an engineering intelligence facade — not a replacement wire stack.

## Components

| Component | Role |
|-----------|------|
| MAVLink Manager | Unified facade |
| MAVLink Router | Message routing between connection profiles |
| MAVLink Parser | Text/JSON/line payload parsing |
| Message Registry | Common MAVLink message catalog |
| Command Registry | `MAV_CMD_*` catalog |
| Heartbeat Monitor | Alive / missed heartbeat tracking |
| Parameter Protocol | PARAM_REQUEST_LIST / PARAM_SET queueing |
| FTP Protocol | Onboard file list/download stubs |
| Mission Protocol | Mission upload/request queueing |
| Telemetry Stream Manager | Open stream + ingest parsed messages |
| Vehicle Discovery | Discover vehicles from heartbeats |
| Connection Profiles | UDP/serial/etc. connection metadata |

## API

Prefix: `/api/drone/v1/mavlink`

- `GET /` — status
- `GET /messages` · `GET /commands`
- `POST /parse`
- `GET|POST /connections`
- `POST /heartbeat`
- `GET|POST /streams`

## Related

[TELEMETRY_AI.md](TELEMETRY_AI.md) · [FLIGHT_LOG_ANALYSIS.md](FLIGHT_LOG_ANALYSIS.md) · [DRONE_DIAGNOSTICS.md](DRONE_DIAGNOSTICS.md)
