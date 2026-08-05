---
title: ADOS Task Decomposer
aliases:
  - Task Decomposer
  - Work Decomposition
tags:
  - execution
  - planning
status: foundation
---

# ADOS Task Decomposer

## Purpose

Describe how **one user request** becomes a structured work tree the Execution Engine can assign, parallelize, and track.

Engine: [[EXECUTION_ENGINE]] · Routing: [[../workforce/TASK_ROUTING|TASK_ROUTING]] · Parallelism: [[PARALLEL_EXECUTION]]

---

## Decomposition hierarchy

```text
User Request
    ↓
Epic
    ↓
Feature
    ↓
Task
    ↓
Subtask
    ↓
Execution Units
```

---

## Level definitions

### User Request

| | |
|--|--|
| **Source** | Owner, Product, CEO, incident, Factory ask |
| **Capture** | Stage 1 Receive Request; Package-ID root |
| **Must clarify** | Outcome, constraints, non-goals, urgency |

### Epic

| | |
|--|--|
| **Meaning** | Multi-feature outcome spanning one or more releases |
| **Owner** | Product Manager (+ Orchestrator) |
| **Example** | “Enterprise SSO for all web surfaces” |
| **Exit** | Features listed; architecture risk flagged |

### Feature

| | |
|--|--|
| **Meaning** | User-visible or operator-visible capability with acceptance criteria |
| **Owner** | Product + Engineering Manager / Team Lead |
| **Example** | “Login with OIDC on FullLayout” |
| **Exit** | Architecture Review complete when structure changes |

### Task

| | |
|--|--|
| **Meaning** | Team-sized work package with a single practice owner |
| **Owner** | One team (Backend, Frontend, Database, …) |
| **Example** | “Implement OIDC token exchange API” |
| **Exit** | Subtasks and dependencies declared |

### Subtask

| | |
|--|--|
| **Meaning** | Slice inside a Task; still human/agent-reviewable |
| **Owner** | Engineer / specialist agent |
| **Example** | “Add refresh-token rotation + tests” |
| **Exit** | Execution Units queued |

### Execution Unit

| | |
|--|--|
| **Meaning** | Smallest schedulable action (file/module/test/doc/registry update) |
| **Owner** | Assigned agent instance |
| **Example** | “Write `auth/oidc_client.py` + unit test” |
| **Exit** | Deliverable artifact + Intent Complete or Rework |

---

## Decomposition rules

1. **One owner per node** — Epic/Feature may have sponsors; Task+ has a single owning team.  
2. **No Feature without acceptance** — “done” must be testable.  
3. **Architecture before Feature fan-out** when boundaries change.  
4. **Tasks map to routing signals** (UI → Frontend, API → Backend, …).  
5. **Execution Units stay additive** — no drive-by refactors.  
6. **Security/Docs/Knowledge** appear as Tasks when signals require them—not as afterthoughts.  
7. Prefer **more small Units** over one opaque Task.

---

## Decomposition algorithm (Orchestrator)

```text
1. Restate Request (objective / non-goals)
2. Detect Epic vs single Feature
3. List Features with acceptance
4. Run Architecture Review gate if needed
5. For each Feature: emit Tasks from routing table
6. For each Task: split Subtasks by module/test/doc
7. For each Subtask: mint Execution Units
8. Build dependency graph (blocking edges)
9. Assign teams; mark critical path
10. Enter Parallel Execution
```

---

## Worked sketch

**Request:** “Add export button for CRM deals to CSV.”

```text
Epic: CRM export capabilities
  Feature: CSV export for deals list
    Task: Backend — export endpoint
      Subtask: Query + stream CSV
        EU: endpoint + DTO
        EU: unit tests
    Task: Database — index if needed
      Subtask: Query plan check
        EU: migration only if required
    Task: Frontend — Export control
      Subtask: Button + download UX
        EU: component + wiring
    Task: Security — authz on export
      Subtask: Permission check
        EU: policy + tests
    Task: QA — acceptance
      Subtask: Happy path + auth denial
    Task: Documentation — operator note
    Task: Knowledge — API registry update
```

---

## Anti-patterns

- Epic that is really one Task.  
- Feature with no QA Task.  
- Execution Unit that spans three teams.  
- Skipping Decomposition and assigning “the whole request” to Backend.

---

## Related

[[PARALLEL_EXECUTION]] · [[HANDOFF_PROTOCOL]] · [[EXECUTION_STATES]] · [[../workforce/WORKFLOW_PATTERNS|WORKFLOW_PATTERNS]]
