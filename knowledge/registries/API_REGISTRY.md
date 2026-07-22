---
title: API Registry
aliases:
  - API Registry
tags:
  - registry
  - api
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---
# API Registry

> Auto-generated 2026-07-22 · [[INDEX]] · [[API_REFERENCE]]

## Overview
Canonical HTTP API prefixes for Platform Core, Ecosystem, and applications.

## Architecture
Gateway `api/server.py` mounts versioned routers. Apps stay behind bridges.

## Components
| API | Prefix | Owner |
|-----|--------|-------|
| Platform Public | `/api/v1` | [[Platform Core]] |
| Platform Management | `/management/v1` | [[Platform Core]] |
| Ecosystem | `/api/ecosystem/v1` | [[Ecosystem]] |
| Agro | `/api/agro/v1` | [[Agro Marketplace]] |
| Port | `/api/port/v1` | [[Port ERP]] |
| Auto | `/api/auto/v1` | [[Auto Marketplace]] |
| Drone | `/api/drone/v1` | [[Drone Platform]] |

## Relationships
Deep reference: [[API_REFERENCE]]. Flows: [[diagrams/DATA_FLOW]] · [[diagrams/flows/API_COMMUNICATION]].

## Responsibilities
Keep prefixes stable; document new routes after each sprint.

## Interfaces
JSON registry field `apis` in `ecosystem_registry.json`.

## REST APIs
This page **is** the REST API registry summary.

## Events
Route registration at process startup; webhook prefixes per app.

## Future roadmap
OpenAPI export per application.

## References
`docs/api.md`, app `api/register.py` modules.

## Related pages
[[Platform Core]] · [[Auto Marketplace]] · [[Port ERP]] · [[Agro Marketplace]] · [[Drone Platform]]
