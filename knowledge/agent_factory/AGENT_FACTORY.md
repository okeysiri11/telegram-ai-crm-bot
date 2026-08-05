---
title: ADOS Agent Factory
aliases:
  - Agent Factory
  - Factory
tags:
  - agent-factory
  - architecture
  - documentation
status: foundation
---

# ADOS Agent Factory

## Purpose

The **ADOS Agent Factory** is the reusable framework for **designing, validating, registering, and activating** enterprise-grade AI agents.

It turns agent creation from ad-hoc prompting into a **repeatable industrial process**:

```text
Need → Spec → Validate → Review → Register → Activate → Operate → Retire
```

The Factory does **not** replace the Engineering Organization.  
It **feeds** it: every generated agent must comply with [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]], fit a type in [[AGENT_TYPES]], and follow lifecycle stages in [[AGENT_LIFECYCLE]].

**Scope of this package:** documentation and architecture only. No application code changes.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     ADOS CEO / Owner                          │
└────────────────────────────┬────────────────────────────────┘
                             │ policy & activation approval
┌────────────────────────────▼────────────────────────────────┐
│                   ADOS Orchestrator                           │
│         routes Factory work; enforces review gates            │
└───────┬─────────────────────┬───────────────────┬───────────┘
        │                     │                   │
┌───────▼────────┐  ┌─────────▼────────┐  ┌───────▼──────────┐
│ Agent Factory  │  │ Engineering Org  │  │ Knowledge Fabric │
│ (this framework)│  │ (roles & reviews)│  │ (specs & registry)│
└───────┬────────┘  └─────────┬────────┘  └───────┬──────────┘
        │                     │                   │
        └──────────┬──────────┴─────────┬─────────┘
                   ▼                    ▼
            Agent Spec (template)   Agent Registry
            Agent Type taxonomy     Lifecycle status
```

### Factory components (logical)

| Component | Document | Role |
|-----------|----------|------|
| Factory charter | [[AGENT_FACTORY]] (this file) | Purpose, pipelines, lifecycle overview |
| Universal template | [[AGENT_TEMPLATE]] | Spec skeleton for every agent |
| Type taxonomy | [[AGENT_TYPES]] | Classification of future agents |
| Lifecycle model | [[AGENT_LIFECYCLE]] | Draft → Archived stages |
| Central registry | [[AGENT_REGISTRY]] | Canonical inventory fields |
| Generation guide | [[AGENT_GENERATION_GUIDE]] | How to create an agent end-to-end |
| Operating rules | [[FACTORY_RULES]] | Non-negotiable factory constraints |

### Integration principles

- **Architecture first** — placement and type before prompts or tools.  
- **Single ownership** — one accountable owner role per agent.  
- **No duplicate responsibilities** — check registry before minting.  
- **Contract compliance** — every agent maps to [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]] sections.  
- **Engineering Org alignment** — generation and review use Orchestrator + specialists ([[../agents/ENGINEERING_ORGANIZATION|ENGINEERING_ORGANIZATION]], [[../agents/ORCHESTRATOR|ORCHESTRATOR]]).

---

## Generation pipeline

```text
1. Capture need (mission, audience, trigger)
2. Classify type ([[AGENT_TYPES]])
3. Check registry for overlap ([[AGENT_REGISTRY]])
4. Instantiate [[AGENT_TEMPLATE]]
5. Fill permissions, limitations, KPIs
6. Map Engineering Org reviewers (if engineering-impacting)
7. Produce draft knowledge page(s)
8. Enter lifecycle: Draft
```

### Generation inputs

- Business or engineering need statement  
- Affected modules / surfaces  
- Desired capabilities and hard limitations  
- Owner (human or role)  

### Generation outputs

- Completed agent specification (from template)  
- Proposed registry row  
- Suggested reviewers and test plan stubs  
- Explicit “not overlapping” justification  

Detail: [[AGENT_GENERATION_GUIDE]]

---

## Validation pipeline

```text
Draft spec
    → Completeness check (all template sections present)
    → Contract check (AGENT_CONTRACT mapping)
    → Uniqueness check (no duplicate mission/ownership)
    → Permission sanity (least privilege)
    → Limitation clarity (non-goals explicit)
    → KPI measurability
    → Lifecycle = Testing (when ready)
```

### Validation roles

| Check | Typical owner |
|-------|----------------|
| Completeness / knowledge consistency | Knowledge Engineer |
| Architecture / overlap | Enterprise Architect |
| Security permissions | Security Engineer |
| Behavioral acceptance plan | QA Engineer |
| Docs discoverability | Documentation Engineer |
| Gate to Review | Orchestrator |

Failed validation returns the agent to **Draft** with a deficiency list.  
Agents must not skip to **Approved** without validation evidence.

---

## Deployment pipeline

“Deployment” in the Factory means **activation into the operating organization**, not necessarily a code release.

```text
Approved agent
    → Registry entry finalized (version, status=Production)
    → Knowledge page published / linked from indexes
    → Orchestrator routing hints updated (logical)
    → Owner acknowledges activation
    → Monitoring via KPIs begins
```

### Deployment gates

1. Lifecycle status = **Approved**  
2. Registry row complete  
3. Documentation mandatory artifacts linked  
4. Testing evidence attached (or N/A with Orchestrator rationale)  
5. Review status = Approved (L2; L3 if policy requires)  

Runtime binding to Cursor skills, CLI, APIs, or domain apps is a **separate implementation program**. This Factory defines the **spec and governance** prerequisites for that binding.

---

## Lifecycle (overview)

Stages (full model in [[AGENT_LIFECYCLE]]):

```text
Draft → Training → Testing → Review → Approved → Production
                                              ↘ Deprecated → Archived
```

Factory owns **transitions policy**; Orchestrator owns **who may approve** each transition.

---

## Success criteria for the Factory itself

- A competent operator can produce a compliant agent draft in **under five minutes** using the template + guide.  
- No agent enters Production without registry + review.  
- Duplicate missions are caught before Approval.  
- Every production agent has KPIs and limitations.

---

## Related pages

[[AGENT_TEMPLATE]] · [[AGENT_TYPES]] · [[AGENT_LIFECYCLE]] · [[AGENT_REGISTRY]] · [[AGENT_GENERATION_GUIDE]] · [[FACTORY_RULES]] · [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]] · [[../agents/ENGINEERING_ORGANIZATION|ENGINEERING_ORGANIZATION]]
