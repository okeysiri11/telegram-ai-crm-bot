---
title: ADOS Agent Lifecycle
aliases:
  - Agent Lifecycle
tags:
  - agent-factory
  - lifecycle
  - governance
status: foundation
---

# ADOS Agent Lifecycle

## Purpose

Define the **mandatory stages** every agent passes through from idea to retirement.

No agent may be treated as production-ready unless its lifecycle status is **Production** (or an explicitly approved temporary exception with CEO L3).

Factory: [[AGENT_FACTORY]] · Registry: [[AGENT_REGISTRY]] · Rules: [[FACTORY_RULES]]

---

## Stages

```text
Draft → Training → Testing → Review → Approved → Production
                                              ↘ Deprecated → Archived
```

| Stage | Meaning | Who advances |
|-------|---------|--------------|
| **Draft** | Spec started from [[AGENT_TEMPLATE]]; incomplete OK | Author / Knowledge Engineer |
| **Training** | Spec complete; prompts/examples/context packs being prepared | Owner + AI/Knowledge specialists |
| **Testing** | Validation pipeline running; acceptance scenarios executed | QA + owner |
| **Review** | Formal L1/L2 (and L3 if required) review in progress | Orchestrator + reviewers |
| **Approved** | Review passed; ready for activation; not yet live | Orchestrator (L2); CEO if L3 |
| **Production** | Active in organization; KPIs monitored | Owner acknowledges; Orchestrator records |
| **Deprecated** | Must not be used for new work; replacement identified | Orchestrator + owner |
| **Archived** | Historical only; removed from routing | Knowledge Engineer + Orchestrator |

---

## Transition rules

### Forward path

| From | To | Entry criteria |
|------|----|----------------|
| Draft | Training | All template sections present (or justified N/A); type chosen; uniqueness check started |
| Training | Testing | Mission, permissions, limitations, KPIs filled; draft registry row exists |
| Testing | Review | Validation evidence attached; known defects listed |
| Review | Approved | Review Status = Approved; no open Block |
| Approved | Production | Registry finalized; docs published; owner activation ack |
| Production | Deprecated | Replacement plan or sunset reason recorded |
| Deprecated | Archived | No remaining dependents; knowledge marked archived |

### Backward path

| Trigger | Action |
|---------|--------|
| Failed validation | Testing → Draft or Training |
| Review Request changes | Review → Testing or Draft |
| Production incident / policy breach | Production → Deprecated (or immediate disable + Review) |
| Scope redesign | Any stage → Draft with version bump |

### Forbidden skips

- Draft → Approved  
- Testing → Production  
- Review → Production without Approved  
- Any stage → Production without registry row  

---

## Versioning across lifecycle

- **0.x** — Draft through Review  
- **1.0.0+** — First Production activation  
- Breaking mission/permission changes require **major** version and re-entry at Review (minimum)  
- Deprecated agents keep version; status conveys usability  

---

## Evidence required per stage

| Stage | Minimum evidence |
|-------|------------------|
| Draft | Template instance path |
| Training | Context/prompt pack checklist |
| Testing | Test plan results / scenarios |
| Review | Review packets + dispositions |
| Approved | L2 (and L3 if required) record |
| Production | Activation timestamp + owner |
| Deprecated | Replacement agent ID or rationale |
| Archived | Archive date + curator |

---

## Operational notes

- Lifecycle status in knowledge frontmatter **must match** [[AGENT_REGISTRY]].  
- Orchestrator routing uses Production agents only (Deprecated only for migration tasks).  
- Archived agents remain searchable for audit, not for delegation.

---

## Related

[[AGENT_FACTORY]] · [[AGENT_GENERATION_GUIDE]] · [[AGENT_TEMPLATE]] · [[../agents/ORCHESTRATOR|ORCHESTRATOR]]
