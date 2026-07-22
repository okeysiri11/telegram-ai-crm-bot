# Predictive Maintenance

**Version:** `4.1.7-enterprise`  
**Sprint:** 13.7 (Connected Cars) · 13.6 (Automotive ERP)  
**APIs:** `/api/connected-cars/v1/predictive` · `/api/automotive-erp/v1/maintenance`

## Connected Cars Predictive AI

Failure probability, battery life, engine health, brake/tire wear, maintenance scheduling, and utilization analysis from telematics and IoT signals.

- `GET /predictive` — status  
- `POST /predictive` — predict (`connected_vehicle_id`, mileage, battery/engine/brake/tire signals)

## Automotive ERP Maintenance AI

Workshop-oriented forecasts via `applications/auto_marketplace/automotive_erp/` (service/fleet context).

Does **not** modify Platform Core, AI OS, or prior sprint packages.
