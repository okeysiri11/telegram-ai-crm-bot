# Roadmap


---
[[INDEX]] · [[ARCHITECTURE]] · [[PLATFORM_CORE]] · [[ROADMAP]] · [[API_REFERENCE]]


## Overview
Forward-looking plan for Platform Core, AI Ecosystem, and vertical applications after the certified Platform Core v3.0.0 baseline and commercial releases of Agro / Port / Auto.

## Architecture
Roadmap items respect the layering rule: Platform Core remains stable; Ecosystem extends cross-app capabilities; applications evolve behind bridges only.

## Components
| Horizon | Focus |
|---------|--------|
| Near | Drone Platform beyond 11.1 (fleet ops, manufacturing depth, simulation) |
| Near | Register all apps in Ecosystem `registered_applications` |
| Mid | Legal Platform as first-class `applications/` product |
| Mid | Deeper knowledge-graph federation across apps |
| Long | Multi-tenant global networks, partner ecosystems |

## Relationships
- Depends on completed sprints: [[sprints/PLATFORM]], [[sprints/PORT_ERP]], [[sprints/AUTO_MARKETPLACE]], [[sprints/DRONE_PLATFORM]]
- Aligns with [[PLATFORM_TIMELINE]] and [[CHANGELOG]]

## APIs
New surface area will continue under versioned prefixes (`/api/<app>/v1`) documented in [[API_REFERENCE]].

## Future roadmap
1. **Drone 11.2+** — manufacturing execution, advanced telemetry analytics, fleet maintenance.
2. **Ecosystem 1.6** — universal app registry, stronger governance policies, shared knowledge sync.
3. **Legal Platform 1.0** — productize scaffold vertical into application package.
4. **CRM unification** — shared CRM patterns across Agro/Auto without breaking bridges.
5. **Plugin marketplace** — expand [[PLUGIN_SDK]] catalog for vertical-specific tools.
