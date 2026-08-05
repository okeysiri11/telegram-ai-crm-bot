---
title: ADOS Execution States
aliases:
  - Execution States
  - Package States
tags:
  - execution
  - states
status: foundation
---

# ADOS Execution States

## Purpose

Define the **lifecycle states** of an Execution Engine package (Epic/Feature/Task and, by inheritance, Subtasks/Units).

Engine: [[EXECUTION_ENGINE]] · Decisions: [[DECISION_ENGINE]] · Communication: [[../workforce/COMMUNICATION_PROTOCOL|COMMUNICATION_PROTOCOL]]

---

## State list

```text
Requested
Planned
Design
Approved
In Progress
Blocked
Review
QA
Ready
Deploying
Completed
Learning
Archived
```

---

## State definitions

| State | Meaning | Typical stage |
|-------|---------|---------------|
| **Requested** | Package-ID created; raw ask captured | Receive Request |
| **Planned** | Objective, non-goals, priority, draft Epic/Feature | Analyze + Planning |
| **Design** | Architecture (and security design if needed) under review | Architecture Review |
| **Approved** | Design Proceed (+ scope approval); build may start | End of Architecture Review |
| **In Progress** | Teams executing assigned Units | Parallel Execution |
| **Blocked** | Waiting on predecessor, decision, or external dependency | Any; especially Parallel Execution |
| **Review** | Deliverables under Architect/Security/peer Review | Review |
| **QA** | Acceptance and regression under QA | QA |
| **Ready** | QA Pass + Docs + Knowledge gates met for release intent | Documentation + Knowledge Update |
| **Deploying** | Release in flight | Deployment |
| **Completed** | Deployed (or terminal non-deploy Complete) and acceptance confirmed | Feedback |
| **Learning** | Retrospective and extraction in progress | Feedback + Learning |
| **Archived** | Learning recorded; package closed | End of Learning |

---

## Allowed transitions

```text
Requested → Planned
Planned → Design | Approved | Archived   (Approved if no design risk; Archived if cancelled)
Design → Approved | Planned | Blocked     (Rework design → Planned; wait → Blocked)
Approved → In Progress
In Progress → Blocked | Review | In Progress
Blocked → In Progress | Design | Planned | Archived
Review → In Progress | QA | Blocked       (Rework → In Progress; Reject may → Design)
QA → In Progress | Ready | Review         (Fail → In Progress; Pass → Ready; re-open Review if needed)
Ready → Deploying | Completed             (Completed if no deploy needed)
Deploying → Completed | Blocked | In Progress
Completed → Learning
Learning → Archived
```

Cancellation: from most pre-Deploy states → **Archived** with CEO/Product authority as required.

---

## Mapping to communication intents

| State entry | Typical Intent |
|-------------|----------------|
| Requested | Request |
| Planned / Design | Response, Review |
| Approved | Approval |
| In Progress | Response / Complete (units) |
| Blocked | Escalate or Response (blocker) |
| Review | Review |
| QA | Review |
| Ready | Approval (merge readiness) |
| Deploying | Request (to DevOps) |
| Completed | Complete |
| Learning | Request (retro) |
| Archived | Complete (terminal) |

---

## State ownership

| State | Primary steward |
|-------|-----------------|
| Requested–Planned | Orchestrator |
| Design–Approved | Chief Architect (+ Orchestrator) |
| In Progress / Blocked | Owning Team Lead + Orchestrator |
| Review | Named reviewers |
| QA | QA Team |
| Ready | Orchestrator |
| Deploying | DevOps / Infrastructure |
| Completed–Learning–Archived | Orchestrator + Knowledge Lead |

---

## Rules

1. No **Deploying** without **Ready** (except Sev-1 hotfix with logged Learning debt).  
2. **Blocked** must name the blocking Package-ID or decision.  
3. **Completed** without **Learning** is incomplete enterprise practice—enter Learning promptly.  
4. Child Units may be In Progress while parent Feature is still Design only if explicitly non-blocking and marked provisional.

---

## Related

[[PARALLEL_EXECUTION]] · [[LEARNING_ENGINE]] · [[../workforce/ESCALATION_MODEL|ESCALATION_MODEL]]
