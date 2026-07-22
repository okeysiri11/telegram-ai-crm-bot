# AI Ecosystem Knowledge Base

Obsidian-compatible wiki for the TelegramBotCourse / AI Ecosystem repository.

> Start here: [[INDEX]]

## Navigation
[[INDEX]] · [[README]] · [[ROADMAP]] · [[CHANGELOG]] · [[ARCHITECTURE]] · [[PLATFORM_CORE]] · [[PLATFORM_TIMELINE]] · [[API_REFERENCE]] · [[SECURITY]] · [[DEPLOYMENT]]
[[AI_AGENTS]] · [[MEMORY_ENGINE]] · [[KNOWLEDGE_GRAPH]] · [[WORKFLOW_ENGINE]] · [[PLUGIN_SDK]]
Apps: [[applications/AUTO_MARKETPLACE|Auto]] · [[applications/AGRO_MARKETPLACE|Agro]] · [[applications/PORT_ERP|Port]] · [[applications/DRONE_PLATFORM|Drone]] · [[applications/CRM|CRM]] · [[applications/LEGAL_PLATFORM|Legal]]
Sprints: [[sprints/PLATFORM|Platform]] · [[sprints/PORT_ERP|Port]] · [[sprints/AUTO_MARKETPLACE|Auto]] · [[sprints/DRONE_PLATFORM|Drone]]
Diagrams: [[diagrams/PLATFORM_GRAPH|Platform Graph]] · [[diagrams/AGENT_GRAPH|Agent Graph]] · [[diagrams/APPLICATION_GRAPH|App Graph]] · [[diagrams/DATA_FLOW|Data Flow]]
Glossary: [[glossary/TERMS|Terms]] · [[glossary/COMPONENTS|Components]]

## Overview
This folder documents Platform Core v3.0.0, AI Ecosystem v1.5.0-alpha, and vertical applications (Agro, Port ERP, Auto Marketplace, Drone Platform). Content mirrors the live repository architecture and completed sprints.

## Architecture
Knowledge pages are organized by concern: platform engines, applications, sprint histories, diagrams, and glossary. Wiki links (`[[Page]]`) provide bidirectional navigation inside Obsidian.

## Components
- Root reference pages (architecture, APIs, security, deployment)
- Application pages under `applications/`
- Sprint summaries under `sprints/`
- Mermaid-friendly diagrams under `diagrams/`
- Shared vocabulary under `glossary/`

## Relationships
- Platform Core is the certified baseline — see [[PLATFORM_CORE]]
- Ecosystem sits above Core via bridges — see [[ARCHITECTURE]]
- Vertical apps consume Core + Ecosystem through bridge interfaces only

## APIs
Canonical HTTP prefixes are listed in [[API_REFERENCE]].

## Future roadmap
See [[ROADMAP]] for planned platform and application work after the current certified baseline.
