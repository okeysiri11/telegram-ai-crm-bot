---
title: ADOS Handoff Protocol
aliases:
  - Handoff Protocol
tags:
  - execution
  - handoff
status: foundation
---

# ADOS Handoff Protocol

## Purpose

Define **what must be delivered** when work moves between teams in the Execution Engine.

Engine: [[EXECUTION_ENGINE]] · Interactions: [[../workforce/TEAM_INTERACTIONS|TEAM_INTERACTIONS]] · Communication: [[../workforce/COMMUNICATION_PROTOCOL|COMMUNICATION_PROTOCOL]]

---

## Canonical handoff chain

```text
Architect → Backend
    ↓
Backend → Database
    ↓
Database → Frontend
    ↓
Frontend → QA
    ↓
QA → Documentation
    ↓
Documentation → Knowledge
    ↓
Knowledge → Deployment
```

**Note:** Backend often continues after Database returns (implement stores). Frontend may start earlier against a frozen contract (non-blocking) but the **integration handoff** still follows this spine. Security and DevOps attach as review/deploy loops ([[PARALLEL_EXECUTION]]).

---

## Handoff envelope (required)

Every handoff message:

```text
Role: <from>
Intent: request | complete  (to next team)
Package-ID: <id>
Modules: <list>
Deliverable: <artifacts>
Assumptions: <list>
Blockers remaining: <none | list>
Ask: <what next team must do>
```

Receiver responds with Intent = Response, then owns the next stage.

---

## Handoff definitions

### Architect → Backend

| Field | Content |
|-------|---------|
| **Deliverable** | Placement decision, module boundaries, non-goals, constraints, Proceed disposition |
| **Backend needs** | Where to put code; what not to invent |
| **Reject if** | Ambiguous ownership, freeze break without CEO path |

### Backend → Database

| Field | Content |
|-------|---------|
| **Deliverable** | Data requirements, access patterns, draft model, consistency needs |
| **Database needs** | Enough to design schema/migrations safely |
| **Reject if** | Unbounded “store everything”; no query intent |

### Database → Frontend

| Field | Content |
|-------|---------|
| **Deliverable** | Approved schema summary **and** (via Backend) stable API/contract impacting UI; migration status |
| **Frontend needs** | Field names, types, nullability, pagination, error shapes |
| **Practical path** | Database → Backend (stores) → **contract merge** → Frontend; label the merge as Database→Frontend when UI depends on new fields |

### Frontend → QA

| Field | Content |
|-------|---------|
| **Deliverable** | Flows, edge cases, build/env notes, known gaps |
| **QA needs** | Acceptance criteria, how to exercise UI/API |
| **Reject if** | “Looks done” with no testable path |

### QA → Documentation

| Field | Content |
|-------|---------|
| **Deliverable** | Pass disposition, verified behavior, residual risks, failed-then-fixed notes |
| **Docs needs** | Reality, not intent |
| **Reject if** | Fail disposition; docs must wait |

### Documentation → Knowledge

| Field | Content |
|-------|---------|
| **Deliverable** | Guides, API notes, operator steps, links |
| **Knowledge needs** | Specs, registries, graph links, agent/Factory updates |
| **Reject if** | Narrative-only with no registry targets when required |

### Knowledge → Deployment

| Field | Content |
|-------|---------|
| **Deliverable** | Registry/spec Complete signal, discoverability checklist, rollback knowledge pointers |
| **Deployment needs** | Confidence that ops can find runbooks/config; release notes linked |
| **Reject if** | Release-bound Knowledge Tasks still Open |

---

## Parallel / shortcut handoffs

| When | Allowed shortcut |
|------|------------------|
| API-only bug | Backend → QA → Docs (if visible) → Knowledge* → Deploy |
| Docs-only | Documentation → Knowledge → (no Deploy or docs-only publish) |
| Hotfix Sev-1 | Ops/Eng → Deploy with **deferred** Docs/Knowledge + Learning debt logged |

\* Skip only if no knowledge surface changed.

---

## Acceptance of a handoff

Receiver may:

- **Accept** → state In Progress  
- **Request changes** (Rework) → return to sender  
- **Reject** → stop path; escalate if ownership disputed  
- **Escalate** → [[../workforce/ESCALATION_MODEL|ESCALATION_MODEL]]

Authorities: [[DECISION_ENGINE]].

---

## Related

[[PARALLEL_EXECUTION]] · [[EXECUTION_STATES]] · [[../workforce/TEAM_INTERACTIONS|TEAM_INTERACTIONS]]
