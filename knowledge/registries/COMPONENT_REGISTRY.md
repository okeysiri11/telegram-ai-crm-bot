---
title: Component Registry
aliases:
  - Component Registry
tags:
  - registry
  - components
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---
# Component Registry

> Auto-generated 2026-07-22 · [[INDEX]]

## Overview
Cross-cutting component catalog spanning engines, apps, and documentation system.

## Architecture
Components are logical capabilities (engines, facades, registries, dashboards).

## Components
| Component | Layer | Page |
|-----------|-------|------|
| Memory Engine | Platform | [[Memory Engine]] |
| Workflow Engine | Platform | [[Workflow Engine]] |
| Plugin SDK | Platform | [[Plugin SDK]] |
| AI Agents | Platform/Eco | [[AI Agents]] |
| Knowledge Graph | Ecosystem | [[Knowledge Graph]] |
| Auto Marketplace | App | [[Auto Marketplace]] |
| Port ERP | App | [[Port ERP]] |
| Agro Marketplace | App | [[Agro Marketplace]] |
| Drone Platform | App | [[Drone Platform]] |
| Legal Platform | Scaffold | [[Legal Platform]] |
| CRM | Capability | [[CRM]] |
| Sprint Registry | Knowledge | [[registries/SPRINT_REGISTRY]] |
| Documentation Generator | Knowledge | [[automation/DOCUMENTATION_AUTOMATION]] |

## Relationships
See [[diagrams/PLATFORM_GRAPH]] and [[diagrams/APPLICATION_GRAPH]].

## Responsibilities
Provide stable names for Obsidian graph nodes and backlinks.

## Interfaces
Human pages + JSON registry.

## REST APIs
N/A for documentation components; app components listed in API registry.

## Events
Documentation regeneration.

## Future roadmap
Expand drone manufacturing components in 11.2+.

## References
[[glossary/COMPONENTS]]

## Related pages
[[ARCHITECTURE]] · [[statistics/STATISTICS]]
