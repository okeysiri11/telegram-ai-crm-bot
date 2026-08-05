---
title: ADOS Escalation Model
aliases:
  - Escalation Model
tags:
  - workforce
  - escalation
  - governance
status: foundation
---

# ADOS Escalation Model

## Purpose

Define the **escalation hierarchy** when an engineer or agent cannot resolve a blocker, conflict, or risk within policy.

Workforce: [[WORKFORCE]] · Org chart: [[ORGANIZATION_CHART]] · Communication: [[COMMUNICATION_PROTOCOL]]

---

## Escalation hierarchy

```text
Engineer
    ↓
Senior Engineer
    ↓
Team Lead
    ↓
Chief Architect
    ↓
ADOS CEO
```

### Parallel escalations (security & ops)

```text
Engineer → Security Lead → ADOS CEO
Engineer → Operations Lead → CTO → ADOS CEO
```

Use the **security parallel path** for Blocks and material trust-boundary risk.  
Use the **ops parallel path** for production incidents.

---

## Level definitions

| Level | Role | Handles |
|-------|------|---------|
| L1 | **Engineer** | Local implementation issues, standard rework |
| L2 | **Senior Engineer** | Cross-file design within a module, mentoring, tech tradeoffs |
| L3 | **Team Lead** | Team priority, ownership disputes within a practice, package splits |
| L4 | **Chief Architect** | Structural conflicts, duplication vs extend, freeze interpretation |
| L5 | **ADOS CEO** | Policy exceptions, L3 approvals, irreversible release, Board-level conflict |

**Orchestrator** may escalate **on behalf of** any level when review gates fail or routing is contested; Orchestrator does not replace Chief Architect for structure.

**CTO / Engineering Manager / Product Manager** participate as Board/management sponsors; they do not skip Architect on structural decisions.

---

## When to escalate

Escalate **up** when:

- Two valid designs conflict and block delivery.  
- Ownership is unclear after Orchestrator clarification.  
- A Security **Block** needs waiver consideration.  
- Scope expands beyond the work package.  
- Deadline pressure would violate Factory/Core rules.  
- Production customer impact is material.

Do **not** escalate for:

- Missing information the requester can supply.  
- Ordinary code review comments.  
- Preference-only style debates already covered by project conventions.

---

## Escalation package (required)

```text
Role escalating:
Level requested:
Summary (5 lines):
Impacted modules:
Attempted options:
Recommendation:
Decision needed by:
```

Use Intent = `escalate` per [[COMMUNICATION_PROTOCOL]].

---

## Resolution and return path

```text
Decision recorded
    → Communicated to Orchestrator + owning Engineer
    → Rework or Proceed
    → Resume review chain
```

Decisions that change architecture must leave a durable note (ADR / knowledge page).

---

## Related

[[TEAM_INTERACTIONS]] · [[TASK_ROUTING]] · [[../agents/ORCHESTRATOR|ORCHESTRATOR]]
