---
title: CRM Detail
aliases:
  - CRM Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# CRM Detail

## Overview
CRM capability across Auto, Agro, and legacy gateway.

## Architecture
```mermaid
flowchart LR
  AUTO[Auto CRM] --> PIPE[Pipeline]
  AGRO[Agro CRM] --> TRADE[Trading CRM]
  LEG[Legacy Telegram CRM] --> LEADS[Leads/Clients]
  AI[CRM AI] --> AUTO
  AI --> AGRO
```

## Components
- Hub: [[CRM]]

## Relationships
[[ARCHITECTURE_DASHBOARD]] · [[ARCHITECTURE]] · [[INDEX]] · [[Platform Core]] · [[AI Agents]]

## Responsibilities
Visualize structure for Obsidian and engineering onboarding.

## Interfaces
Mermaid diagram rendered in Obsidian.

## REST APIs
See [[registries/API_REGISTRY]] when applicable.

## Events
N/A (documentation diagram).

## Future roadmap
Keep diagrams aligned after each sprint via [[automation/DOCUMENTATION_AUTOMATION]].

## References
`docs/architecture.md` and app docs.

## Related pages
[[DASHBOARD]] · [[diagrams/PLATFORM_GRAPH]] · [[diagrams/APPLICATION_GRAPH]]
