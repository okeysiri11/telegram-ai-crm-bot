# Knowledge Base Index

Entry point for the AI Ecosystem knowledge wiki.

## Navigation
[[INDEX]] · [[README]] · [[ROADMAP]] · [[CHANGELOG]] · [[ARCHITECTURE]] · [[PLATFORM_CORE]] · [[PLATFORM_TIMELINE]] · [[API_REFERENCE]] · [[SECURITY]] · [[DEPLOYMENT]]
[[AI_AGENTS]] · [[MEMORY_ENGINE]] · [[KNOWLEDGE_GRAPH]] · [[WORKFLOW_ENGINE]] · [[PLUGIN_SDK]]
Apps: [[applications/AUTO_MARKETPLACE|Auto]] · [[applications/AGRO_MARKETPLACE|Agro]] · [[applications/PORT_ERP|Port]] · [[applications/DRONE_PLATFORM|Drone]] · [[applications/CRM|CRM]] · [[applications/LEGAL_PLATFORM|Legal]]
Sprints: [[sprints/PLATFORM|Platform]] · [[sprints/PORT_ERP|Port]] · [[sprints/AUTO_MARKETPLACE|Auto]] · [[sprints/DRONE_PLATFORM|Drone]]
Diagrams: [[diagrams/PLATFORM_GRAPH|Platform Graph]] · [[diagrams/AGENT_GRAPH|Agent Graph]] · [[diagrams/APPLICATION_GRAPH|App Graph]] · [[diagrams/DATA_FLOW|Data Flow]]
Glossary: [[glossary/TERMS|Terms]] · [[glossary/COMPONENTS|Components]]

## Overview
This index links every major knowledge page. Use it as the Obsidian home note or vault entry.

## Architecture
Stack (bottom → top):
1. [[PLATFORM_CORE|Platform Core v3.0.0]] — certified engines (memory, orchestrator, agents, workflow, tools, cognition, ops)
2. AI Ecosystem v1.5.0-alpha — identity, workspace, assistant, workforce, governance
3. Applications — [[applications/AGRO_MARKETPLACE|Agro]], [[applications/PORT_ERP|Port ERP]], [[applications/AUTO_MARKETPLACE|Auto]], [[applications/DRONE_PLATFORM|Drone]]

Diagrams: [[diagrams/PLATFORM_GRAPH]] · [[diagrams/APPLICATION_GRAPH]] · [[diagrams/AGENT_GRAPH]] · [[diagrams/DATA_FLOW]]

## Components
| Area | Pages |
|------|-------|
| Platform engines | [[MEMORY_ENGINE]] · [[AI_AGENTS]] · [[WORKFLOW_ENGINE]] · [[PLUGIN_SDK]] · [[KNOWLEDGE_GRAPH]] |
| Ops | [[SECURITY]] · [[DEPLOYMENT]] · [[API_REFERENCE]] |
| History | [[PLATFORM_TIMELINE]] · [[CHANGELOG]] · [[sprints/PLATFORM]] |
| Apps | [[applications/AUTO_MARKETPLACE]] · [[applications/AGRO_MARKETPLACE]] · [[applications/PORT_ERP]] · [[applications/DRONE_PLATFORM]] · [[applications/CRM]] · [[applications/LEGAL_PLATFORM]] |
| Sprint logs | [[sprints/PORT_ERP]] · [[sprints/AUTO_MARKETPLACE]] · [[sprints/DRONE_PLATFORM]] |
| Glossary | [[glossary/TERMS]] · [[glossary/COMPONENTS]] |

## Relationships
- Apps **must not** mutate Platform Core or Ecosystem packages; they use bridges.
- Sprint histories summarize completed work without changing code.
- Canonical deep-dive docs also exist under repository `docs/` (referenced from each page).

## APIs
- Platform: `/api/v1`, `/management/v1`
- Ecosystem: `/api/ecosystem/v1`
- Agro: `/api/agro/v1`
- Port: `/api/port/v1`
- Auto: `/api/auto/v1`
- Drone: `/api/drone/v1`

Full detail: [[API_REFERENCE]]

## Future roadmap
[[ROADMAP]] tracks post-foundation work (Drone expansion, deeper Ecosystem registration, Legal vertical productization).
