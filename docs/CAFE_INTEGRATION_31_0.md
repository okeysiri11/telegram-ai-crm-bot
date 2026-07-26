# Cafe Integration Guide — Sprint 31.0

## Why a Cafe OS suite?

Cafe had **catalog + shell only** (no Hub product APIs). Documented gap before implementation. Created a **thin additive** Cafe OS that:

- Owns F&B domain: tables, menu, reservations, orders, kitchen queue, QR menu, delivery, CRM events, owner dashboard
- **Reuses** Commerce Core for payments, loyalty, POS (`industry=cafe`)
- **Reuses** Platform Builder Concierge + AI Team + Mission Control + Comms + OBS
- Does **not** fork Beauty OS or Automotive CRM

## API prefix

`/api/enterprise-cos/v1`

| Method | Path |
|--------|------|
| GET/POST | `/health`, `/bootstrap` |
| GET/POST | `/tables`, `/menu` |
| POST | `/staff`, `/customers`, `/reservations`, `/orders` |
| GET/POST | `/kitchen`, `/qr-menu` |
| POST | `/delivery`, `/crm` |
| GET | `/dashboard` |

## Shared platform

Same as Automotive/Beauty: ISAM, PermissionGuard, WorkspaceLayout, PB Concierge/AI Team/MC, enterprise-comms, OBS, pilotMetrics.
