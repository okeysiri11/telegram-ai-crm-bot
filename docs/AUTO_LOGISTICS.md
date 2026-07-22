# Auto Marketplace — Logistics, Transport, Export & Import (Sprint 10.6)

Vehicle logistics for **Auto Marketplace 2.0.0**.

| Field | Value |
|-------|-------|
| Application version | `2.0.0` |
| `transport_engine` | `1.0` |
| `tracking_engine` | `1.0` |
| `customs_engine` | `1.0` |

**Hard constraint:** AI Platform Core, AI Ecosystem, Agro Marketplace, and Port ERP are not modified.

## Domain facade

```python
from applications.auto_marketplace import auto_marketplace

assert auto_marketplace.config.transport_engine == "1.0"
metrics = auto_marketplace.logistics.metrics()
```

## Transport Engine

Pickup, delivery, door-to-door, terminal, dealer and fleet transfers.

```python
from applications.auto_marketplace.transport.models import VehicleShipment, ShipmentKind

shipment = auto_marketplace.logistics.transport.create(
    VehicleShipment(
        vehicle_id="v1",
        kind=ShipmentKind.DOOR_TO_DOOR,
        origin="Berlin",
        destination="Warsaw",
        origin_country="DE",
        destination_country="PL",
    )
)
booked = auto_marketplace.logistics.transport.book(shipment.shipment_id)
```

## Carrier Network

Companies, private carriers, tow, rail, sea, air — with drivers and ratings.

## Tracking

GPS updates, geofencing, ETA prediction, route history, live notifications.

## Route Optimization

AI multi-stop routing with fuel/cost, border, weather, and traffic factors.

## Import / Export & Customs

Duties/taxes, regulations, certificates; declarations, brokers, VIN validation, clearance.

## Fleet Transport

Dealer, auction, warehouse, port, and rail terminal movements with truck scheduling.

## AI Integration

Carrier recommendation · delivery prediction · delay forecasting · risk prediction · customs assistant · route optimizer

## REST API

| Prefix | Capability |
|--------|------------|
| `/api/auto/v1/transport` | Shipments, dispatch, optimize, AI, fleet |
| `/api/auto/v1/tracking` | GPS, ETA, timeline |
| `/api/auto/v1/import` | Vehicle import trades |
| `/api/auto/v1/export` | Vehicle export trades |
| `/api/auto/v1/customs` | Declarations & clearance |
| `/api/auto/v1/carriers` | Carrier network |

## Modules

`transport/` · `vehicle_shipping/` · `carriers/` · `dispatch/` · `tracking/` · `customs/` · `import_export/` · `international/` · `route_optimizer/` · `delivery/` · `fleet_transport/` · `documents/`
