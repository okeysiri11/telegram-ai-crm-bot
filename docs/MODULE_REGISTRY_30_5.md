# Module Registry — Sprint 30.5

**Source of truth:** `src/web/workspace/managers/moduleRegistry.ts`

## Registered fields

Each module exposes: Name, Version, Routes, Permissions, Navigation, Widgets, Dashboards, Dependencies, Health Status.

## Business ecosystems (must register)

| Id | Name | Route |
|----|------|-------|
| auto | Automotive | `/workspace/auto` |
| beauty | Beauty | `/workspace/beauty` |
| cafe | Cafe | `/workspace/cafe` |
| agro | Agriculture | `/workspace/agro` |
| drone | Drone | `/workspace/drone` |
| legal | Legal | `/workspace/legal` |
| crypto | Crypto (Bidex) | `/workspace/crypto` |

## Platform modules

| Id | Routes |
|----|--------|
| mission_control | `/platform-builder/mission-control`, `/portals/mission-control` |
| pilot | `/pilot` |

## Deduplication

`applicationRegistry` **derives** ecosystem apps from `moduleRegistry` — no second catalog of names/routes for those modules.
