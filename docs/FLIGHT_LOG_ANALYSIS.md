# Flight Log Analysis — Sprint 11.3

**Module:** `applications/drone_platform/flight_logs/`  
**Version:** Drone Platform `1.2.0-alpha`

## Supported formats

| Type | Status |
|------|--------|
| `.bin` | Parsed (text/structured lines) |
| `.tlog` | Parsed via MAVLink line/JSON parser |
| `.log` | Parsed |
| `.dataflash` / ArduPilot DataFlash | PARM/MSG line parse |
| MAVLink logs | Parsed |
| Mission Planner logs | Parsed |
| QGroundControl logs / WPL | Parsed |
| PX4 ULog | Architecture ready (binary decode deferred) |

## Flow

1. Ingest log content + filename/type
2. Detect type
3. Parse messages / parameters / events
4. AI analysis findings + severity

## API

- `GET|POST /api/drone/v1/flight-logs`

## Related

[MAVLINK.md](MAVLINK.md) · [TELEMETRY_AI.md](TELEMETRY_AI.md) · [DRONE_DIAGNOSTICS.md](DRONE_DIAGNOSTICS.md)
