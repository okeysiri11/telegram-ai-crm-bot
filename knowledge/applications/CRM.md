# CRM

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/APPLICATION_GRAPH]] · [[API_REFERENCE]]


## Overview
CRM is a **cross-cutting capability**, not a single `applications/crm` package. Implementations exist inside Auto Marketplace, Agro Marketplace, and the legacy Telegram CRM gateway.

## Architecture
- **Auto CRM** — sales pipeline, customer intelligence, AI sales (Sprint 6.3+) — `docs/CRM_ENGINE.md`, `docs/AI_SALES.md`
- **Agro CRM** — farmers/buyers/suppliers trading CRM (Sprint 8.3) — `docs/AGRO_CRM.md`
- **Legacy Telegram CRM** — leads/clients/managers HTTP API and bot FSM — `docs/SYSTEM_OVERVIEW.md`

## Components
- Lead / customer / deal entities
- Pipelines and forecasting
- AI sales assistants
- Role-based routing (repository vertical CRM routing docs)

## Relationships
- Primary hosts: [[applications/AUTO_MARKETPLACE]], [[applications/AGRO_MARKETPLACE]]
- Agents: [[AI_AGENTS]]
- Legal matters may attach to CRM cases in future — [[applications/LEGAL_PLATFORM]]

## APIs
- Auto: `/api/auto/v1` CRM/sales routes
- Agro: `/api/agro/v1` CRM routes
- Legacy: `/api/leads`, `/api/clients`, `/api/managers`, …

## Future roadmap
Shared CRM kernel in Ecosystem without breaking vertical packages ([[ROADMAP]]).

## Responsibilities
Document and navigate this concern within the Obsidian living vault (Knowledge 1.1).

## Interfaces
Wiki links, dashboards, and registries. Runtime interfaces described where applicable.

## REST APIs
See [[registries/API_REGISTRY]] and [[API_REFERENCE]] when this page owns HTTP surfaces; otherwise N/A.

## Events
Domain or documentation events as applicable; see related sprint pages.

## References
Repository `docs/`, manifests, [[standards/DOCUMENTATION_STANDARDS]].

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[ROADMAP]] · [[registries/COMPONENT_REGISTRY]]
