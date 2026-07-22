# Predictive Maintenance

**Version:** `4.1.6-enterprise`  
**Sprint:** 13.6  
**Package:** `applications/auto_marketplace/automotive_erp/`  
**API:** `/api/automotive-erp/v1/maintenance`

Maintenance AI — failure probability, repair recommendations, maintenance cost forecast, vehicle health monitoring, and downtime prediction from VIN, mileage, and health signals.

## Endpoints

- `GET /maintenance` — status
- `POST /maintenance` — predict (`vin`, `mileage`, `health_score`, `recent_failures`)

Does **not** modify Platform Core, AI OS, or prior sprints.
