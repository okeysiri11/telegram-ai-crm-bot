---
title: ADOS Team Interactions
aliases:
  - Team Interactions
  - Collaboration Model
tags:
  - workforce
  - collaboration
status: foundation
---

# ADOS Team Interactions

## Purpose

Describe how workforce teams **collaborate** on a single change—handoffs, consults, and **review loops**.

Workforce: [[WORKFORCE]] · Routing: [[TASK_ROUTING]] · Communication: [[COMMUNICATION_PROTOCOL]]

---

## Canonical engineering collaboration chain

For a typical product feature that touches structure, data, APIs, and UI:

```text
Architecture
    ↓
Backend
    ↓
Database
    ↓
Frontend
    ↓
QA
    ↓
Documentation
    ↓
Knowledge
```

### What each arrow means

| Handoff | Producer delivers | Consumer needs |
|---------|-------------------|----------------|
| Architecture → Backend | Placement decision, constraints, non-goals | Clear module boundaries |
| Backend → Database | Data requirements / draft model | Schema & migration plan |
| Database → Backend | Approved schema/migration | Implement ports/stores |
| Backend → Frontend | Stable API contract | UI implementation |
| Frontend → QA | Flows + edge cases | Acceptance execution |
| QA → Documentation | Pass disposition + verified behavior | Accurate guides |
| Documentation → Knowledge | Narrative docs | Specs, registries, cross-links |

**DevOps** and **Security** join as **parallel review loops** (not always in the linear spine)—see below.

---

## Parallel / cross-cutting loops

### Security review loop

```text
Any trust-boundary change
    → Security Lead / Security Engineer
    → Approve | Request changes | Block
    → (if changes) owning team rework → Security again
```

Blocks stop the chain until resolved or CEO L3 waiver.

### Architecture review loop

```text
Structure / coupling / new surface
    → Chief Architect / Enterprise Architect
    → Proceed | Redesign | Escalate
    → Implementation only after Proceed
```

### DevOps / deploy loop

```text
Release-bound package
    → DevOps / Infrastructure
    → Package, env, rollback
    → Ops awareness
```

### Product intake loop

```text
Product Manager clarifies acceptance intent
    ↔ Orchestrator
    → Division teams
```

---

## Review loops (general pattern)

```text
        ┌── Request changes ──────────────┐
        │                                 │
Deliver → Review → Approve ──→ Next stage │
        │                                 │
        └── Block / Reject ──→ Escalate or Rework ─┘
```

States align with [[COMMUNICATION_PROTOCOL]]: Request, Response, Review, Approval, Reject, Rework, Complete.

---

## Multi-division collaboration examples

| Scenario | Divisions |
|----------|-----------|
| New CRM field + UI | Business + Engineering (Backend/Frontend/DB/QA) + Knowledge |
| Production incident | Operations + Infrastructure + Security (+ Engineering if defect) |
| Campaign pack | Creative + Business + AI Production Lead + Communication |
| New agent in Factory | Knowledge + Engineering (AI/Architect) + Orchestrator |
| Customer onboarding flow | Customer + Business + Communication + Knowledge |

---

## Interaction rules

1. **One owner** per package; others consult.  
2. Do not skip Architecture when structure changes.  
3. Frontend waits for **contract stability** (or uses versioned stubs agreed with Backend).  
4. QA gates Documentation (“document reality”).  
5. Knowledge finalizes discoverability after Docs.  
6. Security/Architect **Block** overrides schedule pressure.

---

## Related

[[WORKFLOW_PATTERNS]] · [[ESCALATION_MODEL]] · [[../agents/ORCHESTRATOR|ORCHESTRATOR]]
