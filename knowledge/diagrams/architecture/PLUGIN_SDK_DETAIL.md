---
title: Plugin SDK Detail
aliases:
  - Plugin SDK Detail
tags:
  - diagram
  - architecture
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Plugin SDK Detail

## Overview
Plugin SDK and tool framework.

## Architecture
```mermaid
flowchart TB
  SDK[Plugin SDK] --> PM[Plugin Manager]
  PM --> T1[Tool A]
  PM --> T2[Tool B]
  AG[Agents] --> PM
  WF[Workflows] --> PM
```

## Components
- Canonical: [[Plugin SDK]]

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
