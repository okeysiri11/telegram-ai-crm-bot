# AI Agents


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
Agent capabilities span Platform Core agent registry (`platform_agents`), multi-agent orchestrator (`platform_orchestrator` 2.3.0), Ecosystem workforce/executive AI, and application-specific assistants (sales, agro AI, port ops AI, drone engineering AI).

## Architecture
```
Agent Registry (Core)
    ↓
Orchestrator (task routing, multi-agent protocol)
    ↓
App assistants / Ecosystem workforce
```
See [[diagrams/AGENT_GRAPH]] and repository `docs/AGENT_REGISTRY.md`.

## Components
- **Registry** — register, discover, version agents (Sprint 3.1)
- **Orchestrator** — task requests, async execution, routing (Sprint 2.3)
- **Cognitive stack** — reasoning, planning, decision, learning, collaboration (4.1–4.5)
- **Ecosystem** — unified assistant, AI workforce, executive AI (7.3–7.4)
- **App agents** — Auto AI sales, Agro AI, Port digital twin/ops AI, Drone engineering assistant

## Relationships
- Agents may use [[MEMORY_ENGINE]], [[WORKFLOW_ENGINE]], and [[PLUGIN_SDK]] tools.
- Ecosystem [[KNOWLEDGE_GRAPH]] feeds the unified assistant.
- Application pages: [[applications/AUTO_MARKETPLACE]], [[applications/AGRO_MARKETPLACE]], [[applications/PORT_ERP]], [[applications/DRONE_PLATFORM]]

## APIs
- Platform orchestration via Core `/api/v1` and management routes
- Ecosystem assistant under `/api/ecosystem/v1`
- App AI endpoints e.g. `/api/auto/v1/assistant/*`, `/api/drone/v1/ai/*`

## Future roadmap
Stronger cross-app agent federation and shared skill catalogs ([[ROADMAP]]).
