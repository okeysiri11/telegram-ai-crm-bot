# Service Center

**Version:** `4.1.6-enterprise`  
**Sprint:** 13.6  
**Package:** `applications/auto_marketplace/automotive_erp/`  
**API:** `/api/automotive-erp/v1/service`

Workshop operations — service orders, repair orders, mechanic management, work scheduler, workshop calendar, warranty repairs, quality control, and service history.

## Endpoints

- `GET /service` — status
- `POST /service` — service_order / mechanic / repair_order / schedule / qc (`action`)

Does **not** modify Platform Core, AI OS, or prior sprints.
