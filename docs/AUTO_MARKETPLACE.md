# Auto Marketplace — first production application on AI Platform Core v3.0

> Sprint 6.1 — enterprise AI auto marketplace foundation

## Overview

The **Auto Marketplace** is the first production application built on **AI Platform Core v3.0**. It consumes platform services exclusively through integration bridges — **no Platform Core packages are modified**.

---

## Architecture

```mermaid
flowchart TB
    subgraph Application Layer
        AM[AutoMarketplaceApplication]
        API[REST / Internal / Webhooks]
        SVC[Domain Services]
    end

    subgraph Platform Core v3.0
        MEM[Memory Engine]
        WF[Workflow Engine]
        OR[Orchestrator]
        AI[Reasoning / Planning / Decision]
        LR[Learning / Collaboration]
        TOOLS[Tool Framework]
        SEC[Security Layer]
    end

    API --> AM --> SVC
    AM -.->|bridges| Platform Core v3.0
```

---

## Package Structure

```
applications/auto_marketplace/
├── catalog/          # CatalogService
├── crm/              # CRMService
├── dealers/          # DealerService
├── customers/        # CustomerService
├── inventory/        # InventoryService
├── pricing/          # PricingService, RecommendationService
├── search/           # SearchService
├── documents/        # DocumentService
├── payments/         # PaymentService
├── delivery/         # DeliveryService
├── analytics/        # AnalyticsService
├── notifications/    # NotificationService
├── dashboard/        # Dashboard overview
├── mobile/           # Mobile feed API
├── api/              # REST, internal, webhooks
├── integrations/     # Platform bridge
├── shared/           # Models, store, exceptions
└── application.py    # Application facade
```

---

## Domain Models

| Model | Description |
|-------|-------------|
| `Vehicle` | Listed automobile with specification, media, pricing |
| `VehicleSpecification` | Make, model, year, mileage, VIN |
| `VehiclePhoto` / `VehicleVideo` | Media assets |
| `Dealer` / `DealerBranch` | Seller organizations |
| `Customer` | Buyer profiles and preferences |
| `Lead` | Sales inquiry pipeline |
| `Deal` / `Offer` | Negotiation and closing |
| `Reservation` | Vehicle hold |
| `Inspection` / `TradeIn` / `Auction` | Inventory lifecycle |
| `Payment` / `Invoice` | Financial transactions |
| `Delivery` | Fulfillment tracking |
| `ServiceHistory` / `Warranty` | Post-sale records |

---

## Services

All services use an in-memory store for Sprint 6.1 foundation (production persistence added in later sprints).

```python
from applications.auto_marketplace import auto_marketplace

# Catalog
vehicle = auto_marketplace.catalog.create_vehicle(vehicle)

# Search
results = auto_marketplace.search.search_vehicles(make="Toyota", max_price=30000)

# CRM
lead = auto_marketplace.crm.create_lead(lead)

# AI recommendations
recs = auto_marketplace.recommendations.recommend_for_customer(customer_id)
```

---

## AI Platform Integration

`integrations/platform_bridge.py` connects to:

| Platform Service | Usage |
|------------------|-------|
| Memory Engine | Customer context storage |
| Workflow Engine | Deal pipeline workflows |
| Orchestrator | Vehicle inquiry delegation |
| Reasoning Engine | Pricing analysis |
| Planning Engine | Purchase journey planning |
| Decision Engine | CRM next-action decisions |
| Learning Engine | Interaction feedback |
| Collaboration Engine | Multi-agent deal sessions |
| Tool Framework | External tool invocation |
| Security Layer | Session/token authentication |

All integrations fail gracefully with fallbacks when platform services are unavailable.

---

## API

### REST API — `/api/auto/v1`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Application health |
| GET/POST | `/vehicles` | Catalog |
| GET | `/vehicles/{id}` | Vehicle detail |
| GET | `/search` | Vehicle search |
| GET/POST | `/dealers` | Dealers |
| POST | `/customers` | Register customer |
| POST | `/leads` | Create lead |
| GET | `/customers/{id}/recommendations` | AI recommendations |
| GET | `/analytics` | Metrics |
| GET | `/dashboard` | Dashboard overview |
| GET | `/mobile/feed` | Mobile home feed |

### Internal API — `/internal/auto/v1`

Requires `Authorization: Bearer <token>`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/pipeline` | Sales pipeline |
| GET | `/inventory` | Stock summary |
| POST | `/deals` | Create deal + workflow |
| POST | `/payments` | Create payment |
| POST | `/payments/{id}/capture` | Capture payment |
| POST | `/ai/pricing` | AI pricing reasoning |
| POST | `/ai/plan` | Purchase plan |

### Webhooks — `/webhooks/auto/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payments` | Payment provider events |
| POST | `/delivery` | Delivery status updates |
| POST | `/crm` | CRM automation events |

---

## Registration

Routes are registered in `api/server.py`:

```python
from applications.auto_marketplace.api.register import register_auto_marketplace_routes

register_auto_marketplace_routes(app)
```

---

## Developer Guide

### Quick start

```python
from applications.auto_marketplace import auto_marketplace

# Health check
print(auto_marketplace.health())

# Full reset (tests)
auto_marketplace.reset()
```

### Design principles

1. **Platform independence** — Application layer only imports from `platform_*` via bridges
2. **No core modifications** — Platform packages remain untouched
3. **Graceful degradation** — AI features fall back when platform unavailable
4. **Versioned API** — `/api/auto/v1` public contract

---

## Tests

```bash
pytest tests/test_auto_marketplace.py -q
```

---

## Next Sprints

- Persistent storage (PostgreSQL repositories)
- Dealer portal UI
- Mobile app SDK
- Payment provider integrations
- Advanced AI pricing and negotiation agents
