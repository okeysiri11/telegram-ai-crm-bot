---
title: ADOS Context Engine
aliases:
  - Context Engine
tags:
  - memory
  - context
status: foundation
---

# ADOS Context Engine

## Purpose

Describe how **context is assembled before every task** so agents and Orchestrator receive the right slice of Enterprise Memory—neither empty nor unbounded.

Enterprise Memory: [[ENTERPRISE_MEMORY]] · Memory Engine: [[MEMORY_ENGINE]] · Orchestrator: [[../agents/ORCHESTRATOR|ORCHESTRATOR]]

---

## Assembly priority

```text
Current Task
    ↓
Project
    ↓
Workspace
    ↓
Enterprise Knowledge
    ↓
Historical Memory
    ↓
External Knowledge
```

Higher layers win on conflict; lower layers fill gaps. Token/budget limits truncate from the **bottom** first.

---

## Layer definitions

| Layer | Contents |
|-------|----------|
| **Current Task** | Objective, non-goals, Package-ID, acceptance, blockers, assigned agent, security context |
| **Project** | Project node, modules in scope, local conventions, open related Tasks |
| **Workspace** | Active workspace/OS session: open docs, user intent, environment edition |
| **Enterprise Knowledge** | Rules, freeze policies, Workforce/UPP/OS contracts, shared ADRs |
| **Historical Memory** | Prior Decisions, Reviews, Deployments, Incidents, lessons for similar Tasks ([[DECISION_MEMORY]]) |
| **External Knowledge** | Optional UPP `search` / `knowledge` provider results—**cited**, lowest trust until promoted |

---

## Assembly algorithm

```text
1. Load Current Task node + working memory
2. Traverse graph: Task → Project → key Documents/APIs
3. Attach Workspace session facts
4. Inject Enterprise Rules / Skills relevant by capability tags
5. Hybrid search Historical Memory (similarity + filters)
6. Optionally query External Knowledge; mark as external
7. Budget-pack into context window / tool bundle
8. Hand to agent execute() / Orchestrator stage
```

---

## Priority rules

1. **Safety first** — security/enterprise rules never dropped for budget.  
2. **Task fidelity** — acceptance and non-goals always present.  
3. **Prefer graph neighbors** over random semantic hits.  
4. **Historical** informs; it does not override current Approvals.  
5. **External** never silently overrides Enterprise Knowledge.

---

## Output contract

```text
context_bundle:
  task: …
  project: …
  workspace: …
  enterprise: […]
  historical: […]
  external: […]
  graph_refs: [Node IDs]
  budget: { used, max }
```

Agents consume `context_bundle`; they do not re-query ad hoc unless tools allow Memory Engine access under policy.

---

## Related

[[AGENT_MEMORY]] · [[LEARNING_ENGINE]] · [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]] · [[../workforce/TASK_ROUTING|TASK_ROUTING]]
