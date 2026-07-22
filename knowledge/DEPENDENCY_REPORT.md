---
title: Dependency Report
aliases:
  - Dependency Report
tags:
  - architecture
  - knowledge-1.3
generated: 2026-07-22
sprint: Knowledge 1.3
---
# Dependency Report

## Overview
Dependency analysis generated 2026-07-22 by Architecture Guardian (read-only).

## Architecture
Coarse package import graph across Platform Core, Ecosystem, and applications.

## Components
### Platform Core dependencies (packages)
- platform_agents
- platform_ai
- platform_api
- platform_architecture
- platform_certification
- platform_collaboration
- platform_configuration
- platform_console
- platform_decision
- platform_identity
- platform_integrations
- platform_jobs
- platform_learning
- platform_legacy
- platform_management
- platform_memory
- platform_observability
- platform_operations
- platform_orchestrator
- platform_planning
- platform_plugin_sdk
- platform_plugins
- platform_realtime
- platform_reasoning
- platform_reliability
- platform_sdk
- platform_security
- platform_tools
- platform_validation
- platform_workflow
- platform_workflows

### Application dependencies
#### agro_marketplace
- applications.agro_marketplace
- ecosystem
- platform_memory
- platform_orchestrator
- platform_reasoning
- platform_workflow

#### auto_marketplace
- applications.agro_marketplace
- applications.auto_marketplace
- applications.port_erp
- ecosystem
- platform_collaboration
- platform_decision
- platform_learning
- platform_memory
- platform_observability
- platform_orchestrator
- platform_planning
- platform_reasoning
- platform_security
- platform_tools
- platform_workflow

#### drone_platform
- applications.drone_platform
- ecosystem
- platform_memory

#### port_erp
- applications.port_erp
- ecosystem
- platform_memory
- platform_orchestrator
- platform_workflow


### Shared libraries
- api
- services
- database
- plugins
- repositories

### Plugin dependencies
- agro
- auto
- construction
- example
- insurance
- legal
- medical
- realty

### AI Agent dependencies (documented)
- Agro AI
- Architect AI
- CRM AI
- Developer AI
- Drone Engineer AI
- Finance AI
- Legal AI
- Manager AI
- Marketplace AI
- Owner AI
- Port AI
- QA AI

## Relationships
[[ARCHITECTURE]] · [[diagrams/automation/DEPENDENCY_GRAPH]] · [[ARCHITECT_RECOMMENDATIONS]]

## Responsibilities
Expose layer coupling for architecture reviews.

## Interfaces
`python3 knowledge/tools/architecture_check.py`

## REST APIs
API surfaces tracked separately in [[registries/API_REGISTRY]]

## Events
dependency_report_generated

## Future roadmap
[[ROADMAP]]

## References
AST import scan (bounded)

## Related pages
[[PROJECT_HEALTH]] · [[TECHNICAL_DEBT]] · [[INDEX]]
