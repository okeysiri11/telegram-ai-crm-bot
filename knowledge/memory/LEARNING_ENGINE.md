---
title: ADOS Memory Learning Engine
aliases:
  - Memory Learning Engine
  - Enterprise Learning Engine
tags:
  - memory
  - learning
status: foundation
---

# ADOS Learning Engine (Memory)

## Purpose

Describe how **completed work updates Enterprise Memory** so every future agent benefits—routing, context, and best practices improve without changing agent implementations.

This document is the **memory/knowledge** view of learning. Execution-stage retros and mistake tracking: [[../execution/LEARNING_ENGINE|Execution LEARNING_ENGINE]].

Enterprise Memory: [[ENTERPRISE_MEMORY]] · Decision Memory: [[DECISION_MEMORY]] · Context: [[CONTEXT_ENGINE]]

---

## Learning loop

```text
Task / Review / Incident / Deployment completes
    → Extract facts & lessons
    → Write Decision / Lesson / Rule nodes
    → Update Knowledge Index
    → Adjust routing & workflow hints
    → Next Context Engine assembly uses improvements
```

---

## Update rules

### Every completed task updates knowledge

- Implementation refs, Document links, Task outcome → graph.  
- Working memory compacted; durable residue promoted via Knowledge gates.  
- Package-ID retained as provenance.

### Every review improves future routing

- Rework hotspots → routing/checklist hints (e.g. “auth changes → Security earlier”).  
- Approve patterns → Skills / Workflow Pattern notes.  
- Does not silently change Core—updates Knowledge + Orchestrator-facing rules.

### Every incident updates best practices

- Incident → Lesson → Rule/runbook nodes.  
- Context Engine boosts these for similar Future Tasks.  
- Security incidents notify Security Lead path.

### Every deployment improves deployment strategy

- Success/failure → Deployment + Lesson nodes.  
- Failover/UPP and DevOps checklists updated when relevant.  
- Rollback notes become searchable Historical Memory.

---

## Writes vs agent code

| Learning writes | Agent code |
|-----------------|------------|
| Graph, index, rules, skills, docs | **Unchanged** |
| Context bundles get richer | Same `execute` contract |
| Router/Orchestrator read new hints | No per-agent memory fork required |

---

## Coordination with Execution Learning

| Execution Learning | Memory Learning |
|--------------------|-----------------|
| Retro facilitation, mistake IDs, SLA | Persist nodes, index, context ranking |
| Workflow optimization proposals | Store approved practices as Rules/Skills |
| Learning debt tracking | Ensure debt packages still write Lessons |

Both run in Execution state **Learning** → **Archived**.

---

## Success criteria

- Completed work measurably enriches Historical Memory.  
- Similar next Tasks assemble better context without agent redeploys.  
- Routing mistakes decline as Review-derived rules accumulate.

---

## Related

[[KNOWLEDGE_INDEX]] · [[AGENT_MEMORY]] · [[../workforce/TASK_ROUTING|TASK_ROUTING]] · [[../execution/EXECUTION_STATES|EXECUTION_STATES]]
