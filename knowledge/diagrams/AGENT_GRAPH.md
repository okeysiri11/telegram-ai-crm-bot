# Agent Graph

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/PLATFORM_GRAPH]] · [[diagrams/AGENT_GRAPH]] · [[diagrams/APPLICATION_GRAPH]] · [[diagrams/DATA_FLOW]]


## Overview
How agents are registered, orchestrated, and specialized per layer/application.

## Architecture
```mermaid
flowchart LR
  REG[Agent Registry] --> ORCH[Orchestrator]
  ORCH --> ECO_W[Ecosystem Workforce / Executive AI]
  ORCH --> AUTO_AI[Auto AI Sales / Assistant]
  ORCH --> AGRO_AI[Agro AI Agents]
  ORCH --> PORT_AI[Port Ops / Digital Twin AI]
  ORCH --> DRONE_AI[Drone Engineering Assistant]
  ORCH --> LEGAL_A[Legal Agent scaffold]
  REG --> MEM[(Memory Engine)]
  ORCH --> WF[Workflow Engine]
  ORCH --> TOOLS[Tools / Plugins]
  ECO_W --> KG[Knowledge Graph]
```

## Components
- Core registry + orchestrator — [[AI_AGENTS]]
- Cognitive engines feeding decisions
- App assistants with domain policies (e.g. drone engineering-only)

## Relationships
Agents consume [[MEMORY_ENGINE]], [[WORKFLOW_ENGINE]], [[PLUGIN_SDK]], and optionally [[KNOWLEDGE_GRAPH]].

## APIs
Assist endpoints under Ecosystem and app prefixes — [[API_REFERENCE]].

## Future roadmap
Shared skill catalog and cross-app handoff protocols ([[ROADMAP]]).
