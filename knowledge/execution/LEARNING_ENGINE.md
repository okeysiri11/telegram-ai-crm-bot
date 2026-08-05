---
title: ADOS Learning Engine
aliases:
  - Learning Engine
  - Execution Learning
tags:
  - execution
  - learning
  - knowledge
status: foundation
---

# ADOS Learning Engine

## Purpose

Describe how **completed work improves future execution**—so the Enterprise Execution Engine gets smarter without rewriting frozen Core ad hoc.

Engine: [[EXECUTION_ENGINE]] · Knowledge Division: [[../workforce/WORKFORCE|WORKFORCE]] · Factory: [[../agent_factory/AGENT_FACTORY|AGENT_FACTORY]]

---

## Learning loop

```text
Completed (or hotfixed) package
    → Feedback signals
    → Retrospective
    → Mistake tracking
    → Best practices
    → Knowledge extraction
    → Workflow optimization
    → Archived
    → Next Planning / Routing uses updates
```

State: **Learning** → **Archived** ([[EXECUTION_STATES]]).

---

## Inputs

| Input | Source |
|-------|--------|
| Package outcome | Orchestrator Complete record |
| QA evidence | Pass/Fail history, flaky tests |
| Incidents | Operations / Feedback stage |
| Rework counts | Review loops |
| Escalations | Escalation packages |
| Deploy friction | DevOps notes |
| Customer signal | Customer Division |

---

## Retrospectives

**When:** Every Feature that reached Completed (or Sev-1 hotfix).  
**Owner:** Orchestrator facilitates; Team Leads contribute; Knowledge Lead records.

Minimum questions:

1. What was the critical path actually?  
2. Where did Rework concentrate?  
3. Which handoffs were thin or late?  
4. Did routing pick the right teams first time?  
5. What should the next similar Feature copy?

Output: short retro note linked to Package-ID (knowledge page or registry entry).

---

## Mistake tracking

| Field | Purpose |
|-------|---------|
| Mistake ID | Durable reference |
| Package-ID | Provenance |
| Category | routing / design / security / qa-gap / docs-drift / handoff / estimate |
| Impact | time, risk, customer |
| Root cause | 3–5 lines |
| Prevention | rule, checklist, or Factory update |

Mistakes do **not** punish agents; they update gates and templates.

Security mistakes always notify Security Lead.

---

## Best practices

Promote repeated successes into:

- Handoff checklist updates ([[HANDOFF_PROTOCOL]])  
- Workflow pattern notes ([[../workforce/WORKFLOW_PATTERNS|WORKFLOW_PATTERNS]])  
- Routing signal refinements ([[../workforce/TASK_ROUTING|TASK_ROUTING]])  
- Agent role “do / don’t” lines  
- Parallel Execution defaults (earlier contract freeze, etc.)

Best practices require Knowledge Lead acknowledgment before they become “standard.”

---

## Knowledge extraction

Convert package residue into durable knowledge:

| Extract | Destination |
|---------|-------------|
| Architecture decisions | ADR / architecture pages |
| API/behavior | Docs + registries |
| New/changed agents | Agent Factory + Registry |
| Runbooks | Operations knowledge |
| Failure modes | Mistake catalog + QA scenarios |

Extraction is the bridge from **Documentation** stage to long-term **Knowledge Division** memory.

---

## Workflow optimization

Orchestrator + Engineering Manager periodically:

1. Shorten critical paths that are artificially long.  
2. Add merge points where integration pain clustered.  
3. Collapse waves for proven Bug Fix shapes.  
4. Strengthen gates where escapes reached production.  
5. Update Task Decomposer examples from real Epics.

Optimizations must remain consistent with Core/Orchestrator rules (understand → architect → implement → test → document → verify).

---

## Feedback → Learning handoff

```text
Feedback stage
    → Signal: accept | incident | debt
    → Learning Tasks assigned (Knowledge + owning Team Lead)
    → Updates applied
    → Package Archived
```

Deferred Learning (hotfix) creates a **Learning debt** Task with owner and due date—still required.

---

## Success criteria

- Every Archived package has a retro or an explicit waiver (CEO/Product).  
- Recurring mistakes produce checklist/Factory changes within one cycle.  
- Next similar Request routes faster with fewer Rework loops.

---

## Related

[[EXECUTION_ENGINE]] · [[DECISION_ENGINE]] · [[../agents/roles/KnowledgeEngineer|KnowledgeEngineer]] · [[../agent_factory/AGENT_LIFECYCLE|AGENT_LIFECYCLE]]
