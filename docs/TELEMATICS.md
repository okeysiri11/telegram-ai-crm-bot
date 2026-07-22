# Telematics

**Version:** `4.1.8-enterprise`  
**Sprint:** 13.7  
**Package:** `applications/auto_marketplace/connected_cars/`  
**API:** `/api/connected-cars/v1/telematics`

Live GPS tracking, trip history, route analytics, driving behavior, fuel and battery monitoring, engine diagnostics, remote OBD, and event recording.

## Endpoints

- `GET /telematics` — status
- `POST /telematics` — gps / start_trip / end_trip / fuel / battery / obd / event (`action`)

Does **not** modify Platform Core, AI OS, or prior sprints.
