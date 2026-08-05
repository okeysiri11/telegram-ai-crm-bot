---
title: ADOS Agent Generation Guide
aliases:
  - Agent Generation Guide
  - How to Create an Agent
tags:
  - agent-factory
  - guide
  - howto
status: foundation
---

# ADOS Agent Generation Guide

## Purpose

Step-by-step method to create a new enterprise-grade agent **from scratch** using the Factory.

Target time for a compliant **Draft**: **under five minutes** (see closing playbook).

Factory: [[AGENT_FACTORY]] · Template: [[AGENT_TEMPLATE]] · Rules: [[FACTORY_RULES]]

---

## End-to-end flow

```text
Requirements → Spec (Template) → Validation → Review → Documentation
    → Registration → Activation
```

---

## 1. Requirements

Capture before writing the spec:

| Question | Answer |
|----------|--------|
| What painful job should disappear? | |
| Who is the owner? | |
| Which [[AGENT_TYPES]] category? | |
| What must it never do? | |
| Which modules/surfaces does it touch? | |
| Does a similar agent already exist? ([[AGENT_REGISTRY]]) | |

**Exit criteria:** Need statement ≤ 5 lines; type chosen; uniqueness scan done.

---

## 2. Spec creation

1. Copy [[AGENT_TEMPLATE]].  
2. Fill **Name, Mission, Role** first (forces clarity).  
3. Fill **Responsibilities** and **non-responsibilities**.  
4. Fill **Inputs / Outputs**.  
5. Fill **Permissions** (least privilege) and **Limitations**.  
6. Fill **Communication, Delegation, Review, Completion Criteria, KPIs**.  
7. Set frontmatter `status: draft`, `version: 0.1.0`.

**Exit criteria:** No blank required sections (use `N/A` + reason only when truly not applicable).

---

## 3. Validation

Run the Factory validation pipeline ([[AGENT_FACTORY]]):

- [ ] Completeness  
- [ ] [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]] mapping  
- [ ] No duplicate ownership  
- [ ] Permissions ≤ need  
- [ ] KPIs measurable  
- [ ] Limitations explicit  

Advance lifecycle to **Training** then **Testing** as evidence appears ([[AGENT_LIFECYCLE]]).

**Exit criteria:** Deficiency list empty or accepted with owners.

---

## 4. Review

1. Orchestrator opens Review stage.  
2. Assign L1 reviewers by type (see [[AGENT_TYPES]] defaults).  
3. Collect Approve / Changes / Block.  
4. Resolve Blocks (Security/Architect binding).  
5. Orchestrator L2; CEO L3 if required.

**Exit criteria:** Review Status = Approved; lifecycle = Approved.

---

## 5. Documentation

- Publish agent page under `knowledge/agents/` (or domain path).  
- Link from relevant INDEX / agent lists.  
- Documentation Engineer reviews audience clarity.  
- Knowledge Engineer ensures registry + cross-links.

**Exit criteria:** Spec URL stable; discoverable within 2 clicks from agents index or Factory docs.

---

## 6. Registration

Add row to [[AGENT_REGISTRY]] with all required fields:

Agent ID · Name · Role · Owner · Version · Status · Dependencies · Capabilities · Permissions · Review Status

**Exit criteria:** Registry row matches spec frontmatter.

---

## 7. Activation

1. Lifecycle → **Production**.  
2. Owner acknowledges.  
3. Orchestrator enables routing (logical / operational).  
4. KPI baseline date set.  
5. Announce in activity/ops channel if enterprise policy requires.

**Exit criteria:** Agent is Production in registry; eligible for delegation.

---

## Five-minute Draft playbook

Use this when speed matters but quality bars remain:

| Minute | Action |
|--------|--------|
| 0:00–0:45 | Write mission + type + owner; scan registry for duplicates |
| 0:45–2:00 | Paste [[AGENT_TEMPLATE]]; fill Name/Mission/Role/Responsibilities/Limitations |
| 2:00–3:30 | Fill Inputs/Outputs/Permissions/KPIs (3 KPIs minimum) |
| 3:30–4:30 | Fill Communication + Completion Criteria; set `agt_` id |
| 4:30–5:00 | Save page; add Draft registry stub; open validation checklist |

You now have a **Factory-compliant Draft**.  
Training → Production still requires validation, review, docs, registration, and activation—do not skip those for live use.

---

## Anti-patterns

- Prompt-only agents with no spec  
- Activating without registry  
- Copying another agent’s mission with a new name  
- “God agent” with unbounded permissions  
- Skipping QA/docs because “it’s just an AI”  

---

## Related

[[FACTORY_RULES]] · [[AGENT_LIFECYCLE]] · [[AGENT_REGISTRY]] · [[../agents/ORCHESTRATOR|ORCHESTRATOR]]
