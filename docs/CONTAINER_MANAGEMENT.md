# Container Management

**Version:** `4.5.2-enterprise`  
**Sprint:** 15.2  
**Foundation:** Enterprise Platform v4.5.1-enterprise  
**Package:** `applications/port_enterprise/container_management/`  
**API:** `/api/port-containers/v1`

## Capabilities

- Container registry with ISO types, ownership, status, history
- Inspection and maintenance
- Gate in/out, loading, unloading, transshipment, transfer, reservation

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/containers` | Register / status / inspect / maintain |
| GET/POST | `/operations` | Gate / load / unload / transfer / reserve |

## Readiness

Container Platform Ready
