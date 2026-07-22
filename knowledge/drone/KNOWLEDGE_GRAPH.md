---
title: Knowledge Graph
aliases: [Knowledge Graph]
tags: [drone, graph]
generated: 2026-07-22
sprint: "11.8"
---

# Knowledge Graph

## Drone Engineering Suite (11.5)

```mermaid
flowchart LR
  ES[Engineering Suite] --> AF[Airframe]
  ES --> PR[Propulsion]
  ES --> BAT[Battery]
  ES --> EL[Electronics]
  ES --> PCB[PCB]
  ES --> CAD[CAD]
  ES --> SIM[Perf Sim]
  ES --> AI[Engineering AI]
  AF --> Dash[[drone/DRONE_DASHBOARD]]
```

## Manufacturing & Production (11.6)

```mermaid
flowchart LR
  MFG[Manufacturing Suite] --> ORD[Orders]
  MFG --> ASM[Assembly]
  MFG --> BOM[BOM]
  MFG --> WH[Warehouse]
  MFG --> WF[Workflow]
  MFG --> QA[QA]
  MFG --> LIFE[Lifecycle]
  MFG --> PAI[Production AI]
  ORD --> PD[[drone/PRODUCTION_DASHBOARD]]
```

## Mission Operations (11.7)

```mermaid
flowchart LR
  OPS[Mission Ops] --> MC[Mission Center]
  OPS --> FL[Fleet]
  OPS --> GC[Ground Control]
  OPS --> SW[Swarm]
  OPS --> EM[Emergency]
  OPS --> MAI[Mission AI]
  MC --> MD[[drone/MISSION_OPS_DASHBOARD]]
```

## Drone Cloud & Global Command (11.8)

```mermaid
flowchart LR
  CLD[Drone Cloud] --> RM[Remote Ops]
  CLD --> FC[Fleet Cloud]
  CLD --> GCC[Global Command]
  CLD --> DT[Digital Twin]
  CLD --> SEC[Security]
  CLD --> API[Enterprise APIs]
  CLD --> CAI[Cloud AI]
  GCC --> CD[[drone/CLOUD_DASHBOARD]]
```

Links: [[drone/ENGINEERING_REGISTRY]] · [[drone/MANUFACTURING_REGISTRY]] · [[drone/MISSION_OPS_REGISTRY]] · [[drone/CLOUD_REGISTRY]] · [[drone/CLOUD_DASHBOARD]] · [[drone/MISSION_OPS_DASHBOARD]] · [[INDEX]]
