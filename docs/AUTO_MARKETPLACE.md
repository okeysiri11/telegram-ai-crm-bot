# Auto Marketplace — Logistics (Sprint 10.6)

Vehicle transport, tracking, customs, and import/export for **Auto Marketplace 1.5.0-alpha**.

| Field | Value |
|-------|-------|
| Application name | Auto Marketplace |
| Application version | `1.5.0-alpha` |
| Transport engine | `1.0` |
| Tracking engine | `1.0` |
| Customs engine | `1.0` |
| Platform | AI Platform Core v3 (bridge only) |
| Ecosystem | AI Ecosystem v1.5 (bridge only) |
| API | `/api/auto/v1` |

**Hard constraint:** AI Platform Core, AI Ecosystem, Agro Marketplace, and Port ERP are not modified.

## Architecture

```mermaid
flowchart TB
    API["/api/auto/v1"]
    App[AutoMarketplaceApplication]
    Domains[Catalog Marketplace VIN AutoAI Transactions Service Logistics]
    Bridges[Platform + Ecosystem Bridges]
    Store[MarketplaceStore]
    API --> App --> Domains --> Store
    App --> Bridges
```

## Modules (10.6)

`transport/` · `vehicle_shipping/` · `carriers/` · `dispatch/` · `tracking/` · `customs/` · `import_export/` · `international/` · `route_optimizer/` · `delivery/` · `fleet_transport/` · `documents/`

## REST API

`/transport` · `/tracking` · `/import` · `/export` · `/customs` · `/carriers`

## Docs

- [AUTO_VIN.md](AUTO_VIN.md)
- [AUTO_AI.md](AUTO_AI.md)
- [AUTO_TRANSACTIONS.md](AUTO_TRANSACTIONS.md)
- [AUTO_SERVICE.md](AUTO_SERVICE.md)
- [AUTO_LOGISTICS.md](AUTO_LOGISTICS.md)

```python
from applications.auto_marketplace import auto_marketplace

health = auto_marketplace.health()
assert health["application_version"] == "1.5.0-alpha"
assert health["transport_engine"] == "1.0"
assert health["tracking_engine"] == "1.0"
assert health["customs_engine"] == "1.0"
```
