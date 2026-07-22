# Port ERP — Network (Sprint 9.8)

Global port partner network for **Port ERP 2.0.0** (`global_network = 1.0`).

| Field | Value |
|-------|-------|
| Application version | `2.0.0` |
| Global network | `1.0` |
| API | `/api/port/v1/network` · `/api/port/v1/global` |

**Hard constraint:** AI Platform Core and AI Ecosystem are not modified.

## Partner Network

Ports · Shipping Lines · Forwarders · Railways · Truck Fleets · Customs · Banks · Insurance · Government · Inspection Labs · Warehouses · Terminal Operators

## Network Services

- Partner discovery
- Route discovery
- Carrier recommendation
- Price comparison
- Capacity comparison
- ETA optimization
- Risk analysis
- Trade recommendations

## Global Registry

Companies · Partners · Routes · Trade Lanes · Ports · Terminals · Warehouses · Customers · Suppliers · Assets · Containers

## Digital Exchange

Publish and match capacity/price offers across partners.

## Executive Dashboard

Global / Port / Financial / Operational / Live Tracking KPIs, forecasts, and risk dashboard via `/api/port/v1/global/dashboard`.

## Modules

`network/` · `partners/` · `global_registry/` · `digital_exchange/` · `analytics_global/`

```python
from applications.port_erp import port_erp

assert port_erp.config.global_network == "1.0"
partner = port_erp.enterprise.partners.register(
    __import__("applications.port_erp.enterprise.models", fromlist=["NetworkPartner"]).NetworkPartner(
        name="Mombasa Hub", partner_type=__import__("applications.port_erp.enterprise.models", fromlist=["PartnerType"]).PartnerType.PORT
    )
)
```
