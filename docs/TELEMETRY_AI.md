# Telemetry AI — Sprint 11.3

**Module:** `applications/drone_platform/telemetry/`  
**Version:** Drone Platform `1.2.0-alpha`

## Overview

Telemetry AI provides live ingestion, recording, database query, replay, timelines, and subsystem analyzers for UAV flights.

## Engines & analyzers

- Live Telemetry Engine
- Telemetry Recorder / Database / Replay / Timeline
- Signal Quality Monitor
- Radio Link Analyzer
- GPS Quality Analyzer
- Battery Analyzer
- Power Consumption Analyzer
- Motor Performance Analyzer
- ESC Analyzer
- Sensor Health Monitor
- Failsafe Monitor

## API

- `GET /api/drone/v1/telemetry/ai`
- `POST /api/drone/v1/telemetry/analyze` `{ "session_id": "..." }`
- `POST /api/drone/v1/telemetry/record`
- `POST /api/drone/v1/telemetry/replay`

Sessions continue to use `/telemetry/sessions` and `/samples`.

## Related

[MAVLINK.md](MAVLINK.md) · [FLIGHT_LOG_ANALYSIS.md](FLIGHT_LOG_ANALYSIS.md) · [DRONE_DIAGNOSTICS.md](DRONE_DIAGNOSTICS.md)
