---
title: Drone Dashboard
aliases:
  - Drone Dashboard
tags:
  - drone
  - dashboard
generated: 2026-07-22
sprint: "11.6"
---

# Drone Dashboard

## Overview
Readiness dashboard for Drone Platform through Sprint 11.6 (Manufacturing & Production).

## Architecture
Part of [[Drone Platform]].

## Components
- Engineering Suite Ready (11.5)
- Drone Manufacturing Ready
- Assembly Platform Ready
- Warehouse Ready
- Production AI Ready
- Quality Assurance Ready
- Lifecycle Management Ready
- Links: [[drone/PRODUCTION_DASHBOARD]] [[drone/MANUFACTURING_REGISTRY]] [[drone/WAREHOUSE_REGISTRY]] [[drone/BOM_REGISTRY]] [[drone/ASSEMBLY_REGISTRY]] [[drone/ENGINEERING_REGISTRY]] [[drone/KNOWLEDGE_GRAPH]]

## Relationships
[[Drone Platform]] · [[ARCHITECTURE_DASHBOARD]] · [[INDEX]] · [[Knowledge Graph]]

## Interfaces
Docs: `docs/ENGINEERING.md`, `docs/AIRFRAME.md`, `docs/POWER_SYSTEM.md`, `docs/BATTERY_ENGINEERING.md`, `docs/PCB_ENGINEERING.md`, `docs/CAD_INTEGRATION.md`

## REST APIs
`/api/drone/v1/engineering/*`

## Events
drone_engineering_suite_updated

## Related pages
[[INDEX]] · [[sprints/DRONE_PLATFORM]]
