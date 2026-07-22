---
title: Application Registry
aliases:
  - Application Registry
  - AI Application Registry
tags:
  - registry
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Application Registry

## Overview
Registry of applications in the AI Ecosystem.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
| Application | Package | Version | API |
|-------------|---------|---------|-----|
| Agro Marketplace | `applications/agro_marketplace` | 2.0.0 | `/api/agro/v1` |
| Port ERP | `applications/port_erp` | 2.0.0 | `/api/port/v1` |
| Auto Marketplace | `applications/auto_marketplace` | 2.0.0 | `/api/auto/v1` |
| Drone Platform | `applications/drone_platform` | 1.0.0-alpha | `/api/drone/v1` |
| CRM | `cross-cutting` | capability | `embedded` |
| Legal Platform | `src/verticals/legal` | scaffold | `pending` |

## Relationships
[[registries/MODULE_REGISTRY]] · [[registries/API_REGISTRY]] · [[INDEX]]

## Responsibilities
Provide enterprise development infrastructure without changing runtime logic.

## Interfaces
Markdown + generators under `knowledge/tools/`.

## REST APIs
N/A — documentation/infrastructure only.

## Events
generated_by_enterprise_infra

## Future roadmap
[[ROADMAP]]

## References
[[automation/ENTERPRISE_INFRASTRUCTURE]]

## Related pages
[[INDEX]] · [[PROJECT_STATUS]] · [[EXECUTIVE_DASHBOARD]]
