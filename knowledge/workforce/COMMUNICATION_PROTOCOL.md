---
title: ADOS Communication Protocol
aliases:
  - Communication Protocol
tags:
  - workforce
  - communication
status: foundation
---

# ADOS Communication Protocol

## Purpose

Standardize how workforce agents and leads **talk about work**—so every message has a clear state and next action.

Workforce: [[WORKFORCE]] · Escalation: [[ESCALATION_MODEL]] · Agent contract: [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]]

---

## Message envelope (required)

```text
Role: <name>
Intent: request | response | review | approval | reject | rework | complete | escalate | consult
Modules: <list>
Package-ID: <id>
Body: <content>
Ask / Deliverable: <clear next>
```

---

## Communication states

### Request

**Meaning:** Ask for work, information, or a decision.  
**Sender:** Orchestrator, Product Manager, peer consult.  
**Must include:** Objective, non-goals, constraints, done criteria (for work requests).

### Response

**Meaning:** Answer a Request with information or acknowledgment.  
**Must include:** What is known / unknown; blockers if any.  
**Does not** mark the package complete.

### Review

**Meaning:** Evaluate a deliverable against checklist.  
**Sender:** Architect, Security, QA, Docs, Knowledge, Orchestrator.  
**Must include:** Scope reviewed, findings, disposition preview.

### Approval

**Meaning:** Explicit positive gate.  
**Levels:** L0 self / L1 domain / L2 Orchestrator / L3 CEO.  
**Must include:** Scope approved, version/package id, residual risks (if any).

### Reject

**Meaning:** Deliverable is not acceptable; stop current path.  
**Must include:** Reasons, severity, whether escalation is required.  
**Differs from Rework:** Reject may kill the approach; Rework keeps the objective.

### Rework

**Meaning:** Return to owner with required changes.  
**Must include:** Change list, priority, re-review expectation.  
**Owner** remains accountable.

### Complete

**Meaning:** Package done criteria met and gates passed for this stage.  
**Must include:** Evidence links, handoff to next team (or “terminal complete”).  
**Orchestrator** confirms stage Complete before merge/deploy Complete.

---

## State machine (happy path)

```text
Request → Response → (Deliver) → Review → Approval → Complete
                         ↑           │
                         └── Rework ←┘
```

With failure:

```text
Review → Reject → Escalate? → CEO/Architect decision → Rework or Close
```

---

## Channel etiquette

| Do | Don’t |
|----|-------|
| One Intent per message | Mix Approval and Rework in one vague note |
| Cite Package-ID | “Please fix stuff” |
| Separate consult from ownership transfer | Silent scope expansion |
| Put Security findings first | Bury Blocks in chat |

---

## Mapping to Factory / Org

| Protocol state | Typical lifecycle / gate |
|----------------|--------------------------|
| Request | Intake / Draft package |
| Review | Agent or code Review stage |
| Approval | L1–L3 |
| Rework | Return to Testing/Draft |
| Complete | Stage exit / merge readiness |

---

## Related

[[TEAM_INTERACTIONS]] · [[WORKFLOW_PATTERNS]] · [[../agents/ORCHESTRATOR|ORCHESTRATOR]]
