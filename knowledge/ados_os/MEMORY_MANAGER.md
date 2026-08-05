---
title: ADOS Memory Manager
aliases:
  - Memory Manager
tags:
  - ados-os
  - memory
status: foundation
---

# ADOS Memory Manager

## Purpose

Describe how ADOS OS manages **memory scopes**—from volatile session state to durable enterprise knowledge—without conflating chat context with the Knowledge Base.

OS: [[ADOS_OS]] · Knowledge routing: [[ADOS_OS]] · Learning: [[../execution/LEARNING_ENGINE|LEARNING_ENGINE]]

---

## Memory scopes

```text
short-term memory
working memory
long-term knowledge
enterprise memory
project memory
agent memory
```

---

## Short-term memory

| | |
|--|--|
| **Lifetime** | Seconds–minutes; single turn or burst |
| **Contents** | Immediate LLM context window slices, tool results just fetched |
| **Volatility** | High—discard freely |
| **Owner** | Runtime / provider session |

Not a source of truth for architecture or policy.

---

## Working memory

| | |
|--|--|
| **Lifetime** | Active Package-ID / session |
| **Contents** | Current plan, open Tasks, partial handoffs, draft decisions |
| **Volatility** | Cleared or compacted when package Archived (after Learning extraction) |
| **Owner** | Orchestrator + Execution Engine |

Maps closely to Execution states In Progress / Blocked / Review.

---

## Long-term knowledge

| | |
|--|--|
| **Lifetime** | Durable (wiki, registries, ADRs) |
| **Contents** | Specs, role docs, Factory templates, architecture decisions |
| **Volatility** | Low—change via Documentation → Knowledge gates |
| **Owner** | Knowledge Division |

This is the **Knowledge Base** ADOS OS routes to—not raw chat logs.

---

## Enterprise memory

| | |
|--|--|
| **Lifetime** | Organization lifetime |
| **Contents** | Policies, freeze rules, workforce model, OS contracts, edition/license facts |
| **Volatility** | Governance-controlled |
| **Owner** | CEO / Board / Knowledge Lead |

Includes cross-project invariants (Core freeze, provider boundary rules).

---

## Project memory

| | |
|--|--|
| **Lifetime** | Product/repo/program |
| **Contents** | Module maps, sprint outcomes, Package history, Learning retros for this codebase |
| **Volatility** | Medium—evolves with releases |
| **Owner** | Engineering Manager + Knowledge Lead |

TelegramBotCourse vs ADOS runtime repos may have **separate** project memory with shared enterprise memory.

---

## Agent memory

| | |
|--|--|
| **Lifetime** | Per agent instance / role |
| **Contents** | Role priors, recent package notes, personal checklist state |
| **Volatility** | Cleared on AgentStopped/Retire unless promoted to long-term knowledge |
| **Owner** | Agent + Factory lifecycle |

Agents must **not** store secrets or cross-tenant data in unconstrained memory.

---

## Memory Manager responsibilities

1. Allocate/isolate scopes per security and user context.  
2. Promote working → long-term only through Knowledge Update / Learning extraction.  
3. Compact short-term without dropping Package-ID audit trails (those live in events/store).  
4. Serve Knowledge routing: query → correct scope → correct page/registry.  
5. Deny providers direct write to enterprise memory.

---

## Flows

```text
Task execution  → working memory updates
QA Pass + Docs  → candidates for long-term knowledge
Learning stage  → enterprise/project practice updates
AgentActivated  → load agent memory namespace
AgentStopped    → flush or archive agent memory per policy
```

---

## Anti-patterns

- Treating the LLM context as the Knowledge Base.  
- Writing CRM facts only into agent memory.  
- Cross-project leakage without enterprise policy.  
- Silent mutation of long-term knowledge without events (`KnowledgeUpdated`).

---

## Related

[[EVENT_BUS]] · [[STARTUP_SEQUENCE]] · [[../execution/LEARNING_ENGINE|LEARNING_ENGINE]] · [[../workforce/WORKFORCE|WORKFORCE]]
