---
title: ADOS Enterprise Memory
aliases:
  - Enterprise Memory
tags:
  - memory
  - knowledge
  - enterprise
status: foundation
---

# ADOS Enterprise Memory

## Purpose

**Enterprise Memory** is the enterprise-wide memory architecture **shared by every ADOS component**—OS, Orchestrator, Execution Engine, Agent Factory, UPP, modules, and agents.

It is the durable and working substrate behind the Knowledge Graph, Context Engine, and Learning Engine. Chat windows and provider context are **not** substitutes for Enterprise Memory.

This package is **documentation only**. No application code is modified.

Related:

- OS Memory Manager (runtime scopes): [[../ados_os/MEMORY_MANAGER|MEMORY_MANAGER]]  
- ADOS OS: [[../ados_os/ADOS_OS|ADOS_OS]]  
- Execution Learning: [[../execution/LEARNING_ENGINE|Execution LEARNING_ENGINE]]  
- Knowledge Division: [[../workforce/WORKFORCE|WORKFORCE]]  
- UPP knowledge capability: [[../providers/CAPABILITY_REGISTRY|CAPABILITY_REGISTRY]]

---

## Responsibilities

### Long-term memory

Durable facts, policies, ADRs, registries, and frozen constraints that outlive any session. Source of truth for “what ADOS believes” about architecture and enterprise rules.

### Working memory

Active Package-ID state: open tasks, partial handoffs, blockers, draft plans. Cleared or compacted when packages Archive—after Learning extraction into long-term/graph form.

### Conversation memory

Turn-level dialogue and tool traces bound to a session or Package-ID. Volatile by default; promote only curated summaries into Knowledge/Decision Memory.

### Project memory

Repo/program-scoped history: modules, sprints, package outcomes, local conventions. Separate projects share **enterprise** memory, not each other’s secrets.

### Business memory

Domain objects and outcomes—companies, deals, vertical facts—owned by business modules but **indexed** into the Knowledge Graph with clear tenancy and security class.

### Agent memory

Per-agent namespaces (personal/shared/team/temporary/archived)—see [[AGENT_MEMORY]]. Must not become a shadow CRM or bypass security context.

### Knowledge memory

Specs, docs, skills, rules, and graph relationships that the Knowledge Division stewards—the wiki/registries layer agents retrieve via Context Engine.

---

## Position in the stack

```text
ADOS OS
    ↓
Memory Engine          ← [[MEMORY_ENGINE]]
    ↓
Knowledge Graph        ← [[KNOWLEDGE_GRAPH]]
    ↓
Context Engine         ← [[CONTEXT_ENGINE]]
    ↓
Learning Engine        ← [[LEARNING_ENGINE]]
    ↓
Every Agent
```

---

## Principles

1. **One enterprise fabric** — components write/read through Memory Engine APIs, not ad-hoc files.  
2. **Graph + search** — objects are nodes; retrieval is hybrid ([[MEMORY_ENGINE]]).  
3. **Promotion is gated** — working/conversation → long-term only via Docs/Knowledge/Learning.  
4. **Security context travels** — tenant, role, and classification on every read/write.  
5. **Agents stay thin** — they consume assembled context; they do not reimplement memory.  
6. **Align with OS scopes** — Enterprise Memory is the architecture; Memory Manager is the OS runtime mapping.

---

## Package map

| Document | Role |
|----------|------|
| [[KNOWLEDGE_GRAPH]] | Nodes & relationships |
| [[MEMORY_ENGINE]] | Read/write/search |
| [[CONTEXT_ENGINE]] | Pre-task context assembly |
| [[DECISION_MEMORY]] | Searchable decisions & lessons |
| [[AGENT_MEMORY]] | Agent memory classes |
| [[KNOWLEDGE_INDEX]] | What gets indexed |
| [[LEARNING_ENGINE]] | How completion updates memory |

---

## Success criteria

- Any agent can retrieve relevant enterprise context without custom memory code.  
- Decisions, incidents, and deployments are searchable ([[DECISION_MEMORY]]).  
- Learning closes the loop so the next task routes and executes better.

---

## Related

[[MEMORY_ENGINE]] · [[CONTEXT_ENGINE]] · [[../execution/EXECUTION_ENGINE|EXECUTION_ENGINE]]
