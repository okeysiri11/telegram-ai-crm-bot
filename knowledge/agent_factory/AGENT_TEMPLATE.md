---
title: ADOS Agent Template
aliases:
  - Agent Template
  - Universal Agent Template
tags:
  - agent-factory
  - template
status: foundation
---

# ADOS Agent Template

Universal specification template for **every** future ADOS agent.

**Instructions:** Copy this file (or its sections) into `knowledge/agents/` (or the appropriate knowledge domain). Replace placeholders. Do not omit sections. Empty sections must say `N/A` with a one-line reason.

Factory: [[AGENT_FACTORY]] · Contract: [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]] · Types: [[AGENT_TYPES]] · Lifecycle: [[AGENT_LIFECYCLE]]

---

```yaml
# Suggested frontmatter
title: "<Agent Name>"
aliases: ["<Agent Name>"]
tags: [agent, "<type-category>"]
agent_id: "agt_<slug>"
version: "0.1.0"
status: draft   # draft | training | testing | review | approved | production | deprecated | archived
owner: "<role or person>"
type: "<category from AGENT_TYPES>"
```

---

## Name

**Official name:**  
**Short name / alias:**  
**Agent ID:** `agt_…` (must match registry)

---

## Mission

One paragraph. What outcome does this agent exist to produce?  
No scope creep. No “and also everything else.”

---

## Role

| Field | Value |
|-------|-------|
| Primary role | |
| Tier | Executive / Coordination / Specialist / Domain |
| Type category | See [[AGENT_TYPES]] |
| Reports to | Orchestrator / CEO / domain owner |
| Engineering Org mapping (if any) | e.g. Backend Engineer, N/A |

---

## Responsibilities

Bullet list of **owned** duties. Each bullet must be uniquely owned (no overlap with an existing production agent—verify [[AGENT_REGISTRY]]).

-  
-  
-  

**Explicit non-responsibilities:**  

-  

---

## Inputs

What the agent requires to act:

| Input | Source | Required? |
|-------|--------|-----------|
| Task brief | Orchestrator / Owner | Yes |
| Context pack | Knowledge / Twin / modules | |
| Constraints | Policy / freeze / security | |
| Tools / APIs | Named platform surfaces only | |

---

## Outputs

What the agent must produce:

| Output | Format | Consumer |
|--------|--------|----------|
| Deliverable | | |
| Evidence | tests, logs, review packet | QA / Orchestrator |
| Handoff | next role + package id | Orchestrator |
| Risks / follow-ups | list | Owner / Security |

---

## Permissions

Least privilege. List only what is needed.

| Permission | Scope | Justification |
|------------|-------|---------------|
| read | | |
| write | | |
| execute | | |
| escalate | | |

**Forbidden without CEO L3:**  

-  

---

## Limitations

Hard boundaries. Include data, autonomy, and domain limits.

- Must not:  
- Must escalate when:  
- Out of scope:  

---

## Communication

Protocol (required):

```text
Role: <Name>
Intent: consult | deliver | escalate | review
Modules: <list>
Body: …
Ask / Deliverable: …
```

**Channels:** task brief / consult / escalation / review packet  
**Escalation path:** Specialist → Orchestrator → CEO  

---

## Delegation

| May delegate to | For | May not |
|-----------------|-----|---------|
| | | Transfer ownership without Orchestrator |
| | | Implement outside role |

Delegation always returns ownership to this agent or to Orchestrator-assigned owner.

---

## Review

**Self-check (L0) before handoff:**

- [ ] Mission still accurate  
- [ ] Outputs complete  
- [ ] Permissions not exceeded  
- [ ] Limitations respected  
- [ ] Evidence attached  

**Reviewers (L1+):**  

| Stage | Role |
|-------|------|
| Domain | |
| Security (if trust boundary) | Security Engineer |
| Quality (if behavior) | QA Engineer |
| Knowledge/Docs | Knowledge / Documentation Engineer |
| Gate | Orchestrator (L2) |
| Exception / production | CEO (L3) |

---

## Completion Criteria

Agent work package is **done** only when:

1.  
2.  
3.  
4. Review dispositions recorded  
5. Docs/knowledge updated if platform-visible  

---

## KPIs

Measurable indicators (minimum three):

| KPI | Definition | Target | Measurement |
|-----|------------|--------|-------------|
| Quality | | | |
| Cycle time | | | |
| Safety / policy | | | |
| Adoption / usefulness | | | |

---

## Registry stub

Copy into [[AGENT_REGISTRY]] when registering:

| Field | Value |
|-------|-------|
| Agent ID | |
| Name | |
| Role | |
| Owner | |
| Version | |
| Status | Draft |
| Dependencies | |
| Capabilities | |
| Permissions | |
| Review Status | Not started |

---

## Related

[[AGENT_FACTORY]] · [[AGENT_GENERATION_GUIDE]] · [[FACTORY_RULES]] · [[../agents/ORCHESTRATOR|ORCHESTRATOR]]
