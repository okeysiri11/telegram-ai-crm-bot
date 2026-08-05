---
title: ADOS Decision Engine
aliases:
  - Decision Engine
tags:
  - execution
  - governance
  - decisions
status: foundation
---

# ADOS Decision Engine

## Purpose

Define **who can approve, reject, request changes, and escalate** during Execution Engine stages.

Engine: [[EXECUTION_ENGINE]] · Protocol: [[../workforce/COMMUNICATION_PROTOCOL|COMMUNICATION_PROTOCOL]] · Escalation: [[../workforce/ESCALATION_MODEL|ESCALATION_MODEL]] · Org: [[../workforce/ORGANIZATION_CHART|ORGANIZATION_CHART]]

---

## Decision verbs

| Verb | Meaning |
|------|---------|
| **Approve** | Gate opens; work may proceed or merge |
| **Reject** | Current approach stops; may close Feature or force new Design |
| **Request changes (Rework)** | Objective stands; deliverable must be fixed and re-reviewed |
| **Escalate** | Decision moves up the hierarchy |
| **Block** | Hard stop (esp. Security); needs higher waiver to override |

---

## Who can approve

| Scope | Authority | Level |
|-------|-----------|-------|
| Own Execution Unit done | Owning Engineer (self-check) | L0 |
| Practice deliverable | Senior Engineer / Team Lead | L1 |
| Architecture Proceed | Chief Architect / Enterprise Architect | L1–L2 |
| Security for trust boundary | Security Lead / Security Engineer | L1–L2 |
| QA Pass | QA Team | L1 |
| Docs / Knowledge Complete | Documentation / Knowledge Leads | L1 |
| Package merge readiness | ADOS Orchestrator | L2 |
| Freeze break, production Go/No-Go, security waiver | ADOS CEO | L3 |
| Roadmap / acceptance intent | Product Manager | L1 (scope), not a substitute for Architect/Security |

**Rule:** Higher level may Approve lower scopes; lower may not Approve higher gates.

---

## Who can reject

| Actor | May reject |
|-------|------------|
| Chief Architect | Structural designs, placements, freeze-violating plans |
| Security Lead | Unsafe designs, missing controls (also **Block**) |
| QA | Builds that fail acceptance or critical regressions |
| Orchestrator | Incomplete packages, skipped stages, missing evidence |
| Team Lead | Out-of-scope Subtasks inside their practice |
| Product Manager | Features that miss acceptance intent (scope Reject) |
| CEO | Any L3-bound outcome; may Reject Board-escalated proposals |

Reject must include reasons and whether Escalation is required.

---

## Who can request changes (Rework)

| Actor | Typical Rework target |
|-------|----------------------|
| Any Reviewer (Architect, Security, QA, Docs, Knowledge, peer) | Owning team’s last deliverable |
| Orchestrator | Missing artifacts, weak decomposition, skipped handoff fields |
| Senior Engineer / Team Lead | Quality inside practice |
| Product Manager | Acceptance mismatches (behavior, not structure) |

Rework keeps Package-ID and objective; it does not invent a new Epic silently.

---

## Who escalates

| Actor | Escalates when |
|-------|----------------|
| Engineer | Blocked beyond local options |
| Senior Engineer | Cross-module conflict unresolved |
| Team Lead | Cross-team ownership dispute |
| Orchestrator | Routing conflict, repeated gate failure, SLA breach on critical path |
| Security Lead | Block that may need CEO waiver—or policy gap |
| Chief Architect | Freeze interpretation / multi-division structure conflict |
| Product Manager | Priority conflict across Epics |
| Anyone | Sev-1 customer impact → Operations Lead + CEO awareness |

Hierarchy: Engineer → Senior → Team Lead → Chief Architect → CEO ([[../workforce/ESCALATION_MODEL|ESCALATION_MODEL]]).

---

## Decision matrix by stage

| Stage | Approve | Reject / Block | Rework | Escalate |
|-------|---------|----------------|--------|----------|
| Analyze / Planning | Orchestrator, Product | Product (scope) | Orchestrator | Product → CEO |
| Architecture Review | Chief Architect | Architect | Architect | Architect → CEO |
| Parallel Execution | Team Lead (local) | Team Lead | Peers / Lead | Lead → Architect |
| Review | Architect / Security / Orchestrator | Same | Reviewers | Per path |
| QA | QA | QA | QA → owners | Orchestrator |
| Docs / Knowledge | Docs / Knowledge Leads | Leads | Leads | Knowledge Lead → Architect |
| Deployment | DevOps + Orchestrator; CEO if prod | Orchestrator / CEO | DevOps → owners | Ops → CTO → CEO |
| Learning | Knowledge + Orchestrator | — | — | Orchestrator if learning debt ignored |

---

## Conflict resolution order

```text
1. Security Block (binding)
2. Architecture Reject / Redesign
3. CEO L3 decision
4. Product scope Reject (does not override 1–2)
5. Orchestrator merge-readiness Reject
```

---

## Related

[[EXECUTION_STATES]] · [[HANDOFF_PROTOCOL]] · [[LEARNING_ENGINE]]
