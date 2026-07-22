---
title: Port AI
aliases:
  - Port AI
tags:
  - agent
  - port
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---
# Port AI

## Overview
**Port AI** — port ops / digital twin / executive ops. Status: `active`. Layer: `port`.

## Architecture
Participates in the multi-agent topology coordinated by Platform orchestrator and Ecosystem workforce patterns. See [[diagrams/flows/AGENT_COMMUNICATION]] · [[diagrams/AGENT_GRAPH]] · [[registries/AGENT_REGISTRY]] · [[AI Agents]].

## Components
- Role definition
- Session / task interface
- Policy constraints
- Backlinks to domain pages

## Relationships
[[diagrams/flows/AGENT_COMMUNICATION]] · [[diagrams/AGENT_GRAPH]] · [[registries/AGENT_REGISTRY]] · [[AI Agents]] · domain apps [[Auto Marketplace]] [[Port ERP]] [[Agro Marketplace]] [[Drone Platform]] [[CRM]] [[Legal Platform]]

## Responsibilities
Port ops / digital twin / executive ops. Must respect bridge-only integration and safe-use policies (especially engineering agents).

## Interfaces
Orchestrator task requests; app assistant HTTP endpoints; Ecosystem assistant where applicable.

## REST APIs
Varies by host app — see [[registries/API_REGISTRY]]. Drone: `/api/drone/v1/ai/*`. Auto: `/api/auto/v1/assistant/*`.

## Events
assist_requested, task_delegated, workflow_step_assigned, session_remembered

## Future roadmap
Skill catalog entries and shared evaluation harness.

## References
[[registries/AGENT_REGISTRY]] · `docs/AGENT_REGISTRY.md` · `docs/AI_WORKFORCE.md`

## Related pages
[[AI Agents]] · [[Memory Engine]] · [[Workflow Engine]] · [[INDEX]]
