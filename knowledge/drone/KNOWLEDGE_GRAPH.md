---
title: Knowledge Graph
aliases: [Knowledge Graph]
tags: [drone, graph]
generated: 2026-07-22
sprint: "11.5"
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

Links: [[drone/ENGINEERING_REGISTRY]] · [[drone/MANUFACTURING_REGISTRY]] · [[drone/PRODUCTION_DASHBOARD]] · [[drone/DRONE_DASHBOARD]] · [[INDEX]]
