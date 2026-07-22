---
title: README
aliases:
  - Knowledge README
tags:
  - readme
  - knowledge-1.1
---

# AI Ecosystem Knowledge Base

Obsidian living architecture documentation for the entire AI Ecosystem.

> **Start here:** [[INDEX]]

## Overview
Sprint **Knowledge 1.1** transforms `knowledge/` into a fully interconnected documentation system with registries, dashboards, Mermaid diagrams, AI agent pages, and a generator that updates Markdown after sprints.

## Architecture
Workspaces: hubs · applications · agents · registries · diagrams · dashboards · statistics · standards · automation · templates · canvas · excalidraw.

## Components
- Generator: `knowledge/tools/generate_docs.py`
- Data: `knowledge/data/ecosystem_registry.json`
- Obsidian config: `.obsidian/`

## Relationships
Does **not** modify Platform Core, Ecosystem, or application business logic.

## Responsibilities
Human + automated documentation only.

## Interfaces
Open the folder as an Obsidian vault (or include it in the repo vault). Default note: [[INDEX]].

## REST APIs
Documented in [[registries/API_REGISTRY]].

## Events
Run generator after each sprint completion.

## Future roadmap
[[ROADMAP]]

## References
[[standards/DOCUMENTATION_STANDARDS]] · [[automation/DOCUMENTATION_AUTOMATION]]

## Related pages
[[DASHBOARD]] · [[INDEX]] · [[CHANGELOG]]
