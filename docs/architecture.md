# Architecture — Auto CRM Marketplace Platform

## Overview

The platform combines:

- **Telegram CRM** for auto clients and managers
- **Marketplace** inventory & listings
- **AI Manager** lead qualification and routing
- **Dealer vertical** (cars, billing, partners)
- **Owner analytics** and SLA monitoring
- **REST API** with JWT and OpenAPI/Swagger
- **Notification center** (Telegram / Email / SMS / Push)
- **Media storage** abstraction (Telegram / Local / S3 + CDN)

## Layer diagram

```
Telegram Bot (aiogram)
  ├── Auto Client FSM / Dealer / Manager CRM routers
  ├── AI Manager
  └── Entry / Permission middleware

HTTP API (aiohttp)
  ├── /health /metrics
  ├── /api/* CRM REST (JWT)
  └── /v1/* legacy gateway

Services
  ├── ClientRequestCrmEngine / LeadSla / Escalation
  ├── Inventory / Search / Recommendations
  ├── StorageProvider / NotificationCenter
  ├── PlatformAudit / PlatformPermissions
  └── OwnerAnalytics / AI Manager

PostgreSQL + Redis
  ├── client_requests, inventory, audit_log, lead_sla_records
  ├── marketplace_listings, auto_client_requests_v1
  └── permission_engine_* roles/permissions
```

## Key entities

| Entity | Table | Notes |
|--------|-------|-------|
| Client request | `client_requests` | Pipeline + funnel |
| Auto request | `auto_client_requests_v1` | Legacy-compatible lead record |
| Inventory | `inventory` | Marketplace catalog |
| Listing | `marketplace_listings` | Generated listings |
| Audit | `audit_log` | Platform action trail |
| SLA | `lead_sla_records` | Response / assignment / close timers |

## Media storage

`MEDIA_STORAGE_PROVIDER=telegram|local|s3`

- `TelegramStorage` — file_id primary
- `LocalStorage` — filesystem cache + optional CDN URL
- `S3Storage` — S3-compatible object store
- `CompositeStorage` — primary + local cache

## Escalation

| Delay | Action |
|-------|--------|
| 5 min | Reminder to manager |
| 15 min | Repeat notification |
| 30 min | Reassign to AUTO_MANAGER |
| 60 min | Notify OWNER |

## Security

- Role codes: OWNER, ADMIN, MANAGER, AUTO_MANAGER, DEALER_MANAGER, CLIENT, AI_AGENT
- Permissions via `permission_engine_*` tables
- REST API JWT (`JWT_SECRET`)
