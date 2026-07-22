# Fleet Management

**Version:** `4.1.6-enterprise`  
**Sprint:** 13.6  
**Package:** `applications/auto_marketplace/automotive_erp/`  
**API:** `/api/automotive-erp/v1/fleet`

Corporate and logistics fleets — vehicle assignment, drivers, trip history, fuel consumption, maintenance schedules, fleet health, and utilization.

## Endpoints

- `GET /fleet` — status
- `GET /fleet?fleet_id=` — dashboard (vehicles, trips, fuel, health, utilization)
- `POST /fleet` — create fleet / vehicle / driver / assign / trip / maintenance (`action`)

Does **not** modify Platform Core, AI OS, or prior sprints.
