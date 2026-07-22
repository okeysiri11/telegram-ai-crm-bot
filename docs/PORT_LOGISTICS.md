# Port ERP Multimodal Logistics — Sprint 9.5

Shipping lines, freight forwarders, and multimodal logistics for **Port ERP 1.4.0-alpha**.

| Field | Value |
|-------|-------|
| Application version | `1.4.0-alpha` |
| Logistics engine | `1.0` |
| Platform | AI Platform Core v3 (bridge only) |
| Ecosystem | AI Ecosystem v1.5 (bridge only) |

**Hard constraint:** Platform Core and Ecosystem are not modified. Everything lives under `applications/port_erp/`.

## Engines

| Engine | Module |
|--------|--------|
| Shipping Line Engine | `shipping_lines/engine.py` |
| Freight Forwarder Engine | `forwarders/engine.py` |
| Carrier Management Engine | `carriers/engine.py` |
| Multimodal Logistics Engine | `multimodal/engine.py` |
| Route Optimization Engine | `routes/engine.py` |
| Booking Engine | `booking/engine.py` |
| Transport Order Engine | `transport_orders/engine.py` |
| Fleet Coordination Engine | `fleet/coordination.py` |

Mode abstractions: `road/` · `rail/` · `air/` (+ sea via road helpers)

## Capabilities

Shipping schedules · Voyage planning · Carrier contracts · Transport booking · Multimodal / road / rail / sea / air · Cross-border · Door-to-door · Container routing · Freight consolidation

## Route planning hubs

Origin · Destination · Transit hubs · Ports · Rail terminals · Warehouses · Cross docks · Distribution centers · ETA / cost optimization

## Transport orders

Create → Assign → Dispatch → Track → Complete → Archive

## Booking workflow

Request → Quote → Reservation → Confirmation → Execution → Completion · Cancellation

## Events

`BookingCreated` · `BookingConfirmed` · `CarrierAssigned` · `TransportStarted` · `TransportDelayed` · `TransportCompleted` · `RouteOptimized` · `ShipmentTransferred`

## REST API

| Area | Prefix |
|------|--------|
| Shipping | `/api/port/v1/shipping` |
| Forwarders | `/api/port/v1/forwarders` |
| Carriers | `/api/port/v1/carriers` |
| Routes | `/api/port/v1/routes` |
| Bookings | `/api/port/v1/bookings` |
| Transport | `/api/port/v1/transport` |

## Developer guide

```python
from applications.port_erp import port_erp
from applications.port_erp.shared.models import ShippingLine
from applications.port_erp.multimodal.models import RouteHub, HubType, TransportBooking

line = port_erp.logistics.shipping.register_line(ShippingLine(name="OceanLine", scac="OCLN"))
origin = port_erp.logistics.routes.create_hub(RouteHub(name="Mombasa", hub_type=HubType.PORT, country="KE"))
booking = await port_erp.logistics.bookings.create(
    TransportBooking(origin="Mombasa", destination="Rotterdam", shipping_line_id=line.shipping_line_id)
)
```

## Related

- [PORT_ERP.md](PORT_ERP.md)
- [PORT_TRACKING.md](PORT_TRACKING.md)
- [PORT_TERMINAL.md](PORT_TERMINAL.md)
- [PORT_CUSTOMS.md](PORT_CUSTOMS.md)
