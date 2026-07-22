---
title: Documentation Automation
aliases:
  - Documentation Automation
tags:
  - automation
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---

# Documentation Automation

## Overview
Sprint Knowledge 1.1 introduces a living documentation generator that updates Markdown registries after every completed sprint — without modifying Platform Core, Ecosystem, or application code.

## Architecture
```
knowledge/data/ecosystem_registry.json  (source of truth)
        ↓
knowledge/tools/generate_docs.py
        ↓
registries/ · statistics/ · agents/ · CHANGELOG · hubs
```

## Components
- `knowledge/data/ecosystem_registry.json`
- `knowledge/tools/generate_docs.py`
- Output registries under [[registries/SPRINT_REGISTRY]], [[registries/API_REGISTRY]], [[registries/MODULE_REGISTRY]], [[registries/COMPONENT_REGISTRY]], [[registries/AGENT_REGISTRY]]
- Statistics [[statistics/STATISTICS]] · Release notes [[releases/RELEASE_NOTES]]

## Relationships
Feeds [[DASHBOARD]], [[SPRINT_PROGRESS]], [[INDEX]], and Obsidian graph hubs like [[Platform Core]].

## Responsibilities
- Capture sprint history, architecture notes, component/API/module/agent registries
- Refresh changelog & release notes sections for Knowledge stream
- Preserve bridge-only documentation rules

## Interfaces
CLI: `python3 knowledge/tools/generate_docs.py`

## REST APIs
None — documentation tooling only.

## Events
`sprint_completed` → update JSON → run generator → commit knowledge diffs

## Future roadmap
Knowledge 1.2: optional read-only manifest scanners; canvas pack generation.

## References
[[standards/DOCUMENTATION_STANDARDS]] · [[releases/RELEASE_NOTES]]

## Related pages
[[INDEX]] · [[ROADMAP]] · [[CHANGELOG]] · [[SPRINT_PROGRESS]]
