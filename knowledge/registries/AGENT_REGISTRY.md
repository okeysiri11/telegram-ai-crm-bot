---
title: AI Agents Registry
aliases:
  - AI Agents Registry
  - Agent Registry
tags:
  - registry
  - agents
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# AI Agents Registry

## Overview
Agent registry refreshed by Documentation Assistant detection.

## Architecture
Documented agents live in `knowledge/agents/`; code hints are read-only paths.

## Components
### Documented agents
- [[Agro AI]]
- [[Architect AI]]
- [[CRM AI]]
- [[Developer AI]]
- [[Drone Engineer AI]]
- [[Finance AI]]
- [[Legal AI]]
- [[Manager AI]]
- [[Marketplace AI]]
- [[Owner AI]]
- [[Port AI]]
- [[QA AI]]

### Added this run
- None

### Removed this run
- None

### Code hints (read-only)
- `applications/auto_marketplace/ai_sales/agents.py`
- `applications/auto_marketplace/crm/ai_assistant.py`
- `applications/auto_marketplace/finance/ai_assistant.py`
- `applications/drone_platform/ai/assistant.py`
- `database/models/ai_advertising_agent.py`
- `database/models/ai_agents.py`
- `database/models/ai_procurement_agent.py`
- `database/models/ai_sales_agent.py`
- `database/models/ai_sales_assistant.py`
- `ecosystem/ai/assistant.py`
- `ecosystem/api/assistant_handlers.py`
- `migrations/versions/1c972a907102_ai_sales_assistant_v1.py`
- `migrations/versions/1eadc101eebb_ai_sales_agent_v1.py`
- `migrations/versions/ab1a2593ea2e_ai_procurement_agent_v1.py`
- `migrations/versions/d7506c3a0146_ai_advertising_agent_v1.py`
- `platform_agents/base_agent.py`
- `platform_memory/repositories/agent_memory_repository.py`
- `platform_orchestrator/agent_registry.py`
- `platform_orchestrator/base_agent.py`
- `platform_plugins/insurance_agent_plugin/agent.py`
- `platform_tools/agent_bridge.py`
- `platform_workflow/agent_assignment.py`
- `repositories/ai_advertising_agent_repository.py`
- `repositories/ai_procurement_agent_repository.py`
- `repositories/ai_sales_agent_repository.py`
- `repositories/ai_sales_assistant_repository.py`
- `services/ai_agents.py`
- `services/crypto_otc_agent.py`
- `services/hr_agent.py`
- `services/pg_ai_advertising_agent_engine.py`
- `services/pg_ai_advertising_agent_v1.py`
- `services/pg_ai_procurement_agent_engine.py`
- `services/pg_ai_procurement_agent_v1.py`
- `services/pg_ai_sales_agent_engine.py`
- `services/pg_ai_sales_agent_v1.py`
- `services/pg_ai_sales_assistant_engine.py`
- `tests/test_agent_registry.py`
- `tests/test_unified_assistant.py`

### Relationships / workflows
- [[diagrams/flows/AGENT_COMMUNICATION]]
- [[diagrams/automation/AGENT_GRAPH]]
- Permissions: bridge-only; engineering agents remain safe-use scoped

## Relationships
[[AI Agents]] · [[diagrams/AGENT_GRAPH]]

## Responsibilities
Detect new/updated/removed agents and keep wiki roster current.

## Interfaces
documentation_assistant.scan_agents

## REST APIs
App assistant endpoints documented in API registry

## Events
agent_registry_updated

## Future roadmap
Shared skill catalog

## References
`docs/AGENT_REGISTRY.md`

## Related pages
[[Owner AI]] · [[Drone Engineer AI]] · [[INDEX]]
