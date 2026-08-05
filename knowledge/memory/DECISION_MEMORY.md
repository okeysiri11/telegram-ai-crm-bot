---
title: ADOS Decision Memory
aliases:
  - Decision Memory
tags:
  - memory
  - decisions
  - learning
status: foundation
---

# ADOS Decision Memory

## Purpose

Ensure that **every consequential enterprise action becomes searchable memory**—so future agents and humans can find why ADOS chose a path, what shipped, what broke, and what was learned.

Enterprise Memory: [[ENTERPRISE_MEMORY]] · Graph: [[KNOWLEDGE_GRAPH]] · Execution Decisions: [[../execution/DECISION_ENGINE|DECISION_ENGINE]]

---

## What becomes searchable

| Record | Captures |
|--------|----------|
| **Every architectural decision** | Placement, Proceed/Redesign, ADR link, Architect, Package-ID |
| **Every implementation** | What changed (modules/APIs), owner agent/team, commit/ref if any |
| **Every review** | Reviewer, disposition (Approve/Rework/Reject/Block), findings |
| **Every deployment** | Environment, version, start/complete, rollback notes |
| **Every incident** | Severity, cause nodes, fix Package-ID, customer impact |
| **Every lesson learned** | Retro outcomes, mistake IDs, best-practice promotions |

---

## Node shape

```text
Type: Decision | Review | Deployment | Incident | Lesson
Links: Task, Project, Agent, Document, Rule, Event
Properties: disposition, summary, evidence refs
Search: structured + semantic + vector
```

---

## Write path

```text
Execution / Ops event
    → Memory Engine write (durable)
    → Knowledge Graph edges
    → Knowledge Index update
    → Available to Context Engine (Historical Memory)
```

Architecture decisions additionally require Architect (or CEO L3) provenance. Security Blocks are immutable facts (waiver separate node).

---

## Retrieval examples

- “Why was UPP chosen over direct OpenAI in CRM?” → Decision + Document.  
- “Last three failed deployments of module.crm” → Deployment nodes + Incident links.  
- “Reviews that Reworked auth handoffs” → Review nodes filtered by module tag.

---

## Rules

1. Searchable ≠ public — security class still applies.  
2. Lessons without linked Package-ID are low quality; Learning Engine should reject orphans.  
3. Implementation memory stores **references**, not entire codebases.  
4. Do not duplicate full docs—link Document nodes.

---

## Related

[[LEARNING_ENGINE]] · [[CONTEXT_ENGINE]] · [[../execution/LEARNING_ENGINE|Execution LEARNING_ENGINE]] · [[../workforce/COMMUNICATION_PROTOCOL|COMMUNICATION_PROTOCOL]]
