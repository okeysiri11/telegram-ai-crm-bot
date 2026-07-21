# Port ERP Tracking — Sprint 9.2

Live vessel, container, and fleet tracking for **Port ERP 1.1.0-alpha**.

| Field | Value |
|-------|-------|
| Application version | `1.1.0-alpha` |
| Tracking engine | `1.0` |
| Platform | AI Platform Core v3 (bridge only) |
| Ecosystem | AI Ecosystem v1.5 (bridge only) |

**Hard constraint:** Platform Core and Ecosystem are not modified. Tracking lives entirely under `applications/port_erp/`.

## Engines

| Engine | Module | Role |
|--------|--------|------|
| AIS Tracking Engine | `ais/engine.py` | Live vessel positions (AIS-style) |
| Container Tracking Engine | `containers/tracking.py` | Lifecycle + container positions |
| Truck GPS Engine | `gps/engine.py` | Truck GPS updates |
| Fleet Tracking Engine | `fleet/engine.py` | Unified fleet + rail abstraction |
| Route Monitoring Engine | `tracking/live.py` | Speed, heading, route history |
| Live Position Engine | `tracking/live.py` | Current positions for all assets |
| Timeline Engine | `timeline/engine.py` | Chronological asset events |
| Geofence Engine | `geofence/engine.py` | Enter / exit zone detection |
| ETA Engine | `tracking/live.py` | ETA / ETD / arrival prediction |
| Live Tracking Engine | `tracking/engine.py` | Facade over all engines |
| Maps Service | `maps/service.py` | Map viewport + layers |
| Live Port Operations | `operations/live.py` | Ops dashboard over tracking |

## Supported capabilities

- Live vessel position (speed, heading, destination, last checkpoint)
- Container lifecycle + history
- Truck GPS tracking
- Rail tracking abstraction
- Port arrival prediction
- ETA / ETD calculation
- Route history
- Geofence enter / exit

## Container statuses

`created` → `booked` → `loaded` → `at_port` → `on_vessel` → `in_transit` → `transshipment` → `customs` → `arrived` → `warehouse` → `out_for_delivery` → `delivered` → `completed`

## Vessel statuses

`scheduled` · `approaching` · `anchored` · `docked` · `loading` · `unloading` · `waiting` · `departed` · `completed`

## Geofence types

`port` · `terminal` · `berth` · `warehouse` · `container_yard` · `gate` · `rail_terminal`

## Events

`VesselPositionUpdated` · `ContainerPositionUpdated` · `TruckPositionUpdated` · `EnteredGeofence` · `ExitedGeofence` · `ETAChanged` · `ETDChanged` · `ArrivalPredicted` · `DelayDetected`

## REST API

| Area | Prefix |
|------|--------|
| Tracking | `/api/port/v1/tracking` |
| Vessels (AIS) | `/api/port/v1/vessels/.../position` |
| Containers | `/api/port/v1/containers/.../position`, `/lifecycle`, `/history` |
| GPS | `/api/port/v1/gps` |
| Maps | `/api/port/v1/maps` |
| Timeline | `/api/port/v1/timeline` |

### Key endpoints

```
GET  /api/port/v1/tracking
GET  /api/port/v1/tracking/live
GET  /api/port/v1/tracking/fleet
POST /api/port/v1/tracking/eta
POST /api/port/v1/vessels/{id}/position
POST /api/port/v1/containers/{id}/lifecycle
POST /api/port/v1/gps/trucks
POST /api/port/v1/gps/trucks/{id}/position
GET  /api/port/v1/maps
POST /api/port/v1/maps/geofences
GET  /api/port/v1/timeline
```

## Developer guide

```python
from applications.port_erp import port_erp
from applications.port_erp.shared.models import Vessel
from applications.port_erp.tracking.models import Geofence, TruckTrack

vessel = port_erp.core.vessels.register(Vessel(name="Pacific Star", imo="9123456"))
await port_erp.tracking.ais.update_vessel_position(
    vessel.vessel_id,
    latitude=-4.05,
    longitude=39.68,
    speed_knots=14.0,
    heading_deg=90.0,
    destination="Mombasa",
)
pred = await port_erp.tracking.eta.predict_arrival(
    asset_type="vessel",
    asset_id=vessel.vessel_id,
    dest_lat=-4.06,
    dest_lon=39.67,
    destination="Mombasa CT1",
)
```

## Related

- [PORT_ERP.md](PORT_ERP.md) — Port ERP overview
- [architecture.md](architecture.md) — system architecture
