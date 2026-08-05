---
title: ADOS Parallel Execution
aliases:
  - Parallel Execution
  - Dependency Graph
tags:
  - execution
  - parallelism
status: foundation
---

# ADOS Parallel Execution

## Purpose

Describe how the Execution Engine runs **multiple teams at once** without chaos—via dependency graphs, blocking rules, critical path, and merge points.

Engine: [[EXECUTION_ENGINE]] · Decomposer: [[TASK_DECOMPOSER]] · Handoffs: [[HANDOFF_PROTOCOL]]

---

## Parallel teams

Teams may execute **concurrently** when their Tasks have **no blocking edge** between them.

| Pattern | Example |
|---------|---------|
| Docs stubs while Backend builds | Documentation drafts API shapes marked “provisional” |
| Frontend stubs against contract | OpenAPI/contract frozen → Frontend + Backend parallel |
| Security threat model | Runs parallel to early Backend once Architect Proceeds |
| Knowledge registry prep | Parallel to Docs after Feature scope is stable |

**Orchestrator** schedules waves; teams do not invent parallel work outside the graph.

---

## Dependency graph

```text
Nodes  = Tasks / Subtasks / Execution Units
Edges  = must-finish-before (blocking) OR informs (non-blocking)
Waves  = sets of nodes with all blocking predecessors Complete
```

### Edge types

| Edge | Meaning | Scheduler behavior |
|------|---------|-------------------|
| **Blocks** | Consumer cannot start (or cannot finish) until producer Completes | Wait |
| **Informs** | Consumer may start; must re-check when producer updates | Soft sync |
| **Reviews** | Gate node; can Rework producer | Hold merge |

---

## Blocking tasks

A Task is **blocking** when downstream work cannot honestly proceed without its deliverable.

Typical blockers:

- Architecture Review (Proceed) before structure-changing Tasks  
- API contract freeze before Frontend against live contract  
- Schema/migration before stores that depend on new columns  
- Security Approval before deploy of trust-boundary changes  
- QA Pass before Documentation claims “verified” behavior  
- Knowledge Update before declaring platform discoverability Complete (when required)

Blocked Execution Units enter state **Blocked** ([[EXECUTION_STATES]]) with a named predecessor Package-ID.

---

## Non-blocking tasks

A Task is **non-blocking** when it can proceed with stubs, drafts, or prior knowledge—and re-sync later.

Examples:

- Frontend UI chrome against mock API  
- Provisional docs marked draft  
- Test harness scaffolding  
- Threat-model notes before final code review  

Non-blocking work must declare **re-sync merge points**.

---

## Critical path

The **critical path** is the longest chain of blocking Tasks from Request to Deployment.

```text
Architect Proceed → Backend API → Database (if required) → Frontend integrate
    → Security Approve → QA Pass → Docs → Knowledge → Deploy
```

Rules:

1. Protect critical-path owners from unrelated interrupts.  
2. Escalate early if a critical-path node is Blocked beyond SLA.  
3. Prefer shortening the path by earlier contract freeze—not by skipping gates.

---

## Merge points

**Merge points** are Orchestrator checkpoints where parallel branches rejoin.

| Merge point | After | Gate |
|-------------|-------|------|
| **Design merge** | Architecture Review | Proceed before build wave |
| **Contract merge** | Backend (+ DB) contract freeze | Frontend may drop stubs |
| **Integration merge** | Backend + Frontend + DB Complete | Enter Review/QA |
| **Quality merge** | QA Pass | Docs allowed to claim verified |
| **Release merge** | Docs + Knowledge Complete | Deploying |
| **Learning merge** | Feedback captured | Learning → Archived |

At each merge: Intent Review → Approval (or Rework) per [[../workforce/COMMUNICATION_PROTOCOL|COMMUNICATION_PROTOCOL]].

---

## Wave execution model

```text
Wave 0: Analyze / Plan / Architect
Wave 1: Parallel non-blocked build Tasks
Wave 2: Integration after contract merge
Wave 3: Review + Security
Wave 4: QA
Wave 5: Docs + Knowledge (Knowledge may wait on Docs)
Wave 6: Deployment
Wave 7: Feedback + Learning
```

Waves may collapse for tiny Bug Fixes ([[../workforce/WORKFLOW_PATTERNS|WORKFLOW_PATTERNS]]) but gates remain named.

---

## Anti-patterns

- Starting Frontend and Backend with no contract and no re-sync point.  
- Declaring “parallel” while everything secretly waits on one engineer.  
- Skipping merge points to “save time.”  
- Treating Security as non-blocking on auth changes.

---

## Related

[[HANDOFF_PROTOCOL]] · [[DECISION_ENGINE]] · [[../workforce/TEAM_INTERACTIONS|TEAM_INTERACTIONS]]
