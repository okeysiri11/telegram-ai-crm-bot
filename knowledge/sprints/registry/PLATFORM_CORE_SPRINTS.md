---
title: Platform Core Sprint Cards
tags:
  - sprint-registry
  - knowledge-1.1
generated: 2026-07-22
---

# Platform Core Sprint Cards

## Overview
Detailed sprint cards (Purpose, Features, Components, API, Architecture changes, Version, Status, Dependencies).

## Architecture
Subset of [[registries/SPRINT_REGISTRY]] with expanded columns for planning and audits.

## Components

| Sprint | Purpose | Features | Components | API | Architecture changes | Version | Status | Dependencies |
|--------|---------|----------|------------|-----|----------------------|---------|--------|--------------|
| 1.5 | Certification RC1 | Baseline freeze, certification PASS | platform_* certified set | `/api/v1` contract 1.0 | Frozen Core architecture | 3.0.0 | completed | — |
| 2.1-2.2 | Memory | Session/long-term/semantic memory | platform_memory | bridge APIs | Memory 2.2.0 | memory 2.2.0 | completed | 1.5 |
| 2.3 | Orchestrator | Multi-agent routing | platform_orchestrator | task APIs | Orchestrator 2.3.0 | orch 2.3.0 | completed | 2.1-2.2 |
| 3.1 | Agent registry | Register/discover agents | platform_agents | registry | Agent layer | 1.0 | completed | 2.3 |
| 3.2 | Workflow | Workflow/task engines | platform_workflow | workflow APIs | Process automation | 1.0 | completed | 3.1 |
| 3.3 | Plugins | Tools + Plugin SDK | platform_tools/plugins/sdk | plugin manager | Extensibility | 1.0 | completed | 3.2 |
| 4.1-4.5 | Cognition | Reason/plan/decide/learn/collaborate | cognitive engines | engine APIs | Cognitive stack | 1.0 | completed | 3.3 |
| 5.1-5.5 | Ops | Security→validation | ops layers | management | Production ops | 1.0 | completed | 4.1-4.5 |


## Relationships
[[SPRINT_PROGRESS]] · [[sprints/PLATFORM]] · [[sprints/PORT_ERP]] · [[sprints/AUTO_MARKETPLACE]] · [[sprints/DRONE_PLATFORM]] · [[ROADMAP]]

## Responsibilities
Provide complete sprint metadata for living documentation.

## Interfaces
Markdown tables + registry JSON.

## REST APIs
Per-sprint API column.

## Events
Sprint completion updates.

## Future roadmap
[[ROADMAP]]

## References
[[automation/DOCUMENTATION_AUTOMATION]]

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[statistics/STATISTICS]]
