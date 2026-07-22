---
title: Dependency Graph
aliases: [Dependency Graph]
tags: [drone, dependency, graph]
generated: 2026-07-22
sprint: "11.10"
---

# Dependency Graph

- Platform Core v3 (external, not modified)
- AI Ecosystem v1.5 (bridge)
- Drone Platform modules depend inward on shared store + application facade

```mermaid
flowchart LR
  Core[Platform Core] -.-> Bridge[Platform Bridge]
  EcoExt[AI Ecosystem] -.-> EcoBridge[Ecosystem Bridge]
  Bridge --> App[DronePlatformApplication]
  EcoBridge --> App
  App --> Suites[Domain Suites]
```

Links: [[drone/ARCHITECTURE_GRAPH]] [[drone/KNOWLEDGE_GRAPH]]
