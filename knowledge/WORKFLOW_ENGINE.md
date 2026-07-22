# Workflow Engine


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
`platform_workflow` (and legacy `platform_workflows`) implements workflow and task engines at version **1.0** (Sprint **3.2**). Used to model multi-step business and agent processes.

## Architecture
Workflows are created with named steps, assignees, and metadata; engines track lifecycle and handoffs. Applications start workflows through platform bridges when available (stub-safe offline).

## Components
- Workflow definitions / steps
- Task engine
- Integration with [[AI_AGENTS]] orchestrator
- Tool invocations via [[PLUGIN_SDK]] / tools framework

## Relationships
- Part of [[PLATFORM_CORE]]
- Called from Auto/Agro/Port bridges for deal, export, or ops flows
- Documented in repository `docs/WORKFLOW_ENGINE.md`

## APIs
Python `workflow_engine` APIs; HTTP via Platform `/api/v1` and management plane as exposed.

## Future roadmap
Richer visual workflow authoring and cross-app workflow templates ([[ROADMAP]]).
