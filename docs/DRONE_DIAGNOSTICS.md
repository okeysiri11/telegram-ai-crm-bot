# Drone Diagnostics — Sprint 11.3

**Module:** `applications/drone_platform/diagnostics/` (+ mission intelligence, GCS, visualization)

## Automatic detections

GPS glitches · Compass problems · EKF errors · Vibration · Power failures · Motor imbalance · ESC failures · RC loss · Telemetry loss · Battery degradation · Sensor anomalies · Navigation problems · Mission failures · Landing/takeoff issues · Crash indicators

## Mission intelligence

Validator · Waypoint optimizer · Terrain analyzer · Flight risk estimator · Battery/range prediction · RTH simulator · Emergency landing suggestions · Mission replay/comparison/scoring

## Ground control

Mission Planner · QGroundControl · MAVProxy · APM Planner · Custom GCS Bridge

## Visualization

Flight/mission timelines · Parameter changes · Battery/GPS/altitude/speed/current/signal charts · Flight events timeline

## API

- `GET|POST /api/drone/v1/diagnostics`
- `POST /api/drone/v1/mission-intel/analyze|compare|rth`
- `GET|POST /api/drone/v1/gcs/bridges`
- `POST /api/drone/v1/visualization/bundle`

## Related

[MAVLINK.md](MAVLINK.md) · [TELEMETRY_AI.md](TELEMETRY_AI.md) · [FLIGHT_LOG_ANALYSIS.md](FLIGHT_LOG_ANALYSIS.md)
