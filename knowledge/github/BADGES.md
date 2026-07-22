---
title: Badge Generator
aliases:
  - Badges
tags:
  - github
  - badges
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Badge Generator

## Overview
Markdown badges for README / docs.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
```markdown
![Knowledge](https://img.shields.io/badge/Knowledge-2.0.0-blue)
![Platform Core](https://img.shields.io/badge/Platform_Core-3.0.0-green)
![Ecosystem](https://img.shields.io/badge/Ecosystem-1.5.0--alpha-lightgrey)
![Docs](https://img.shields.io/badge/Docs-Obsidian-purple)
```

Rendered references live in [[github/README_SNIPPET]].

## Relationships
[[INDEX]] · [[dashboard/README]] · [[pipeline/README]]

## Responsibilities
Provide enterprise development infrastructure without changing runtime logic.

## Interfaces
Markdown + generators under `knowledge/tools/`.

## REST APIs
N/A — documentation/infrastructure only.

## Events
generated_by_enterprise_infra

## Future roadmap
[[ROADMAP]]

## References
[[automation/ENTERPRISE_INFRASTRUCTURE]]

## Related pages
[[INDEX]] · [[PROJECT_STATUS]] · [[EXECUTIVE_DASHBOARD]]
