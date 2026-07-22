# Platform Core


---
[[INDEX]] · [[ARCHITECTURE]] · [[PLATFORM_CORE]] · [[ROADMAP]] · [[API_REFERENCE]]


## Overview
**AI Platform Core v3.0.0** is the certified, production-ready foundation for all AI verticals. Certification status: **PASS** (score 100.0). Architecture and API contract versions: `1.0.0`.

## Architecture
Platform Core is a set of `platform_*` packages providing memory, multi-agent orchestration, workflows, tools/plugins, cognitive engines, and operational layers. Sprint history: [[sprints/PLATFORM]] · [[PLATFORM_TIMELINE]].

## Components
| Domain | Packages / engines | Version |
|--------|--------------------|---------|
| Memory | `platform_memory` | 2.2.0 |
| Orchestrator | `platform_orchestrator` | 2.3.0 |
| Agents | `platform_agents` | registry 1.0 |
| Workflow | `platform_workflow` (+ legacy `platform_workflows`) | 1.0 |
| Tools / Plugins | `platform_tools`, `platform_plugins`, `platform_plugin_sdk` | 1.0 |
| Cognition | reasoning, planning, decision, learning, collaboration | 1.0 each |
| Ops | security, observability, reliability, configuration, validation | 1.0 each |
| API / SDK | `platform_api`, `platform_sdk`, `platform_management` | v1 |

Related pages: [[MEMORY_ENGINE]] · [[AI_AGENTS]] · [[WORKFLOW_ENGINE]] · [[PLUGIN_SDK]] · [[SECURITY]]

## Relationships
- Consumed by Ecosystem and all applications via bridges.
- Does not own vertical business logic (Agro/Port/Auto/Drone).
- Knowledge graph is Ecosystem-owned — [[KNOWLEDGE_GRAPH]].

## APIs
- Public: `/api/v1` (legacy `/v1` adapters)
- Management: `/management/v1`
See [[API_REFERENCE]] and `platform_manifest.json`.

## Future roadmap
Core remains frozen baseline; enhancements prefer plugins and Ecosystem layers ([[ROADMAP]]).
