---
title: AI Agents Registry
aliases:
  - AI Agents Registry
  - Agent Registry
tags:
  - registry
  - agents
  - knowledge-1.1
generated: 2026-07-22
sprint: Knowledge 1.1
---
# AI Agents Registry

> Auto-generated 2026-07-22 · [[AI Agents]] · [[diagrams/AGENT_GRAPH]]

## Overview
Registry of platform, ecosystem, and application AI agents documented in the knowledge vault.

## Architecture
Agents register with Platform Core registry/orchestrator; domain agents live in apps; workforce/executive agents in Ecosystem.

## Components
| Agent | Role | Layer | Status |
|-------|------|-------|--------|
| [[Owner AI]] | executive ownership & portfolio decisions | ecosystem | documented |
| [[Manager AI]] | delivery management & sprint coordination | ecosystem | documented |
| [[Developer AI]] | implementation assistance & code guidance | platform | documented |
| [[Architect AI]] | architecture review & system design | platform | documented |
| [[QA AI]] | quality assurance & regression guidance | platform | documented |
| [[Finance AI]] | billing, tariffs, financial ops | application | documented |
| [[Legal AI]] | legal agent / compliance scaffold | vertical | scaffold |
| [[Drone Engineer AI]] | firmware, config, diagnostics (engineering only) | drone | active |
| [[Port AI]] | port ops / digital twin / executive ops | port | active |
| [[Agro AI]] | agro trading, forecasting, quality | agro | active |
| [[CRM AI]] | sales pipeline & customer intelligence | crm | active |
| [[Marketplace AI]] | listings, pricing, recommendations | auto/agro | active |

## Relationships
Communication flows: [[diagrams/flows/AGENT_COMMUNICATION]]. Hub: [[AI Agents]].

## Responsibilities
Document owner, purpose, interfaces, and safe operating policy per agent.

## Interfaces
Agent pages under `knowledge/agents/`; orchestrator TaskRequest patterns in Core.

## REST APIs
Assist endpoints under Ecosystem and app `/ai` or `/assistant` routes.

## Events
Task requests, workflow steps, assistant sessions.

## Future roadmap
Shared skill catalog across agents.

## References
`docs/AGENT_REGISTRY.md`, `docs/AI_WORKFORCE.md`.

## Related pages
[[Owner AI]] · [[Drone Engineer AI]] · [[Port AI]] · [[Agro AI]] · [[CRM AI]] · [[Marketplace AI]]
