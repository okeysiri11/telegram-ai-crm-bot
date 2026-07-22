# Platform Graph

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/PLATFORM_GRAPH]] · [[diagrams/AGENT_GRAPH]] · [[diagrams/APPLICATION_GRAPH]] · [[diagrams/DATA_FLOW]]


## Overview
Structural graph of Platform Core engines and their adjacency to Ecosystem and applications.

## Architecture
```mermaid
flowchart TB
  subgraph Core["Platform Core v3.0.0"]
    MEM[Memory 2.2.0]
    ORCH[Orchestrator 2.3.0]
    AG[Agent Registry]
    WF[Workflow/Task]
    TOOLS[Tools/Plugins/SDK]
    COG[Reasoning/Planning/Decision/Learning/Collaboration]
    OPS[Security/Obs/Reliability/Config/Validation]
  end
  subgraph Eco["Ecosystem v1.5.0-alpha"]
    ID[Identity/Workspace]
    ASST[Unified Assistant]
    KG[Global Knowledge]
    GOV[Governance]
  end
  subgraph Apps["Applications"]
    AGRO[Agro 2.0]
    PORT[Port 2.0]
    AUTO[Auto 2.0]
    DRONE[Drone 1.0.0-alpha]
  end
  MEM --> ORCH --> AG
  AG --> WF --> TOOLS
  COG --> ORCH
  OPS --> Core
  Eco --> Core
  Apps -->|bridges| Eco
  Apps -->|bridges| Core
  ASST --> KG
  ASST --> MEM
```

## Components
Nodes map to pages: [[PLATFORM_CORE]], [[MEMORY_ENGINE]], [[AI_AGENTS]], [[WORKFLOW_ENGINE]], [[PLUGIN_SDK]], [[KNOWLEDGE_GRAPH]], [[SECURITY]].

## Relationships
Strict dependency direction: Apps → bridges → Ecosystem/Core. Core does not import apps.

## APIs
HTTP edges summarized in [[diagrams/DATA_FLOW]] and [[API_REFERENCE]].

## Future roadmap
Add Legal app node when productized ([[applications/LEGAL_PLATFORM]]).
