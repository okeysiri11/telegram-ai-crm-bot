# Agro Marketplace Administrator Guide

## Scope

Administrators and owners operate Agro Marketplace **2.0.0 Commercial** without modifying AI Platform Core or AI Ecosystem.

## Administrator Portal

`GET /api/agro/v1/portal/administrator` — users, partners, marketplace metrics.

## Release administration

1. `GET /api/agro/v1/ops/version` — confirm `2.0.0` / Production Ready / Commercial
2. `POST /api/agro/v1/ops/validation` — full validation
3. `POST /api/agro/v1/ops/readiness` — readiness score
4. `POST /api/agro/v1/ops/certify` — mark release certified
5. `POST /api/agro/v1/ops/release` — commercial production bundle + reports

## Partner administration

- Connect bank / insurance / logistics / government / lab / ERP / marketplace partners
- Subscribe outbound webhooks under `/api/agro/v1/webhooks/subscriptions`
- Inbound partner events: `/webhooks/agro/v1/partners`

## Permissions

Roles: farmer, buyer, supplier, exporter, logistics, administrator, owner, ai_agent  
Administrator and Owner have wildcard (`*`) permissions.

## Configuration

| Setting | Production value |
|---------|------------------|
| `application_version` | `2.0.0` |
| `application_status` | `Production Ready` |
| `release` | `Commercial` |

Do not change Platform Core or Ecosystem packages to “fix” Agro issues — use bridges and ops reports instead.
