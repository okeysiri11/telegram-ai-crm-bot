---
title: ADOS Workflow Patterns
aliases:
  - Workflow Patterns
  - Standard Workflows
tags:
  - workforce
  - workflows
status: foundation
---

# ADOS Workflow Patterns

## Purpose

Describe **standard workflows** the Enterprise Workforce uses repeatedly.

Workforce: [[WORKFORCE]] · Routing: [[TASK_ROUTING]] · Interactions: [[TEAM_INTERACTIONS]]

---

## Pattern template

Each pattern lists: Trigger → Route → Sequence → Reviews → Complete → Deploy (if any).

---

## 1. New Feature

**Trigger:** Product/Owner requests new capability.

```text
Orchestrator understands
    → Architect (if structure)
    → Backend → Database → Frontend
    → Security (if trust boundary)
    → QA
    → Documentation → Knowledge
    → DevOps (if release-bound)
    → Orchestrator L2 → CEO L3 if production release
```

**Complete when:** Acceptance met, tests pass, docs/knowledge updated, merge readiness true.  
**Communication:** Request → … → Approval → Complete.

---

## 2. Bug Fix

**Trigger:** Defect in production or test.

```text
Orchestrator triages severity
    → Owning team (Backend/Frontend/Infra/…)
    → QA verifies fix + regression
    → Docs if user-visible behavior changed
    → DevOps if hotfix deploy
```

**Rules:** No unrelated refactors; Security if vulnerability.  
**Escalate:** Sev-1 customer impact → Operations Lead + CEO awareness.

---

## 3. Architecture Review

**Trigger:** New module, boundary change, duplication risk, freeze question.

```text
Request to Chief Architect
    → Options analysis
    → Decision (Proceed / Redesign / Escalate)
    → Durable ADR / knowledge note
    → Orchestrator updates routing constraints
```

**Implementation must wait** for Proceed when marked architecture-impacting.

---

## 4. Security Review

**Trigger:** Auth, secrets, external I/O, tenant data, dangerous defaults.

```text
Owning team submits review packet
    → Security Lead / Security Engineer
    → Approve | Rework | Block
    → (Block) escalate for waiver only via CEO L3
    → QA includes security scenarios
```

**Block is binding.**

---

## 5. Refactoring

**Trigger:** Technical debt reduction without intended behavior change.

```text
Orchestrator scopes non-goals (no feature creep)
    → Architect confirms no boundary violation
    → Owning engineers execute
    → QA regression mandatory
    → Docs only if public contracts/names change
```

**Rules:** Prefer small packages; no “refactor + feature” combos.

---

## 6. Documentation Update

**Trigger:** Docs drift, release notes, operator guides, API catalogs.

```text
Documentation Team updates guides
    → Knowledge Team updates specs/registries/links
    → Optional QA smoke of documented steps
    → Orchestrator Complete
```

If docs reveal product bugs → open Bug Fix pattern.

---

## 7. Additional standard patterns (brief)

| Pattern | Spine |
|---------|-------|
| **New Agent (Factory)** | Knowledge → Template → Validate → Review → Register → Activate |
| **Incident Response** | Ops → Infra → Security* → Eng defect* → Postmortem → Knowledge |
| **Provider Integration** | Architect → Backend/AI → Security → QA → Docs → Knowledge |
| **Deprecation** | Architect/Product → Owner → Docs/Knowledge → Registry Deprecated → Archive |

---

## Pattern compliance checklist

- [ ] Routed per [[TASK_ROUTING]]  
- [ ] Interactions respect review loops  
- [ ] Communication states used correctly  
- [ ] Escalation path known  
- [ ] Factory/Core rules not violated  

---

## Related

[[COMMUNICATION_PROTOCOL]] · [[ESCALATION_MODEL]] · [[../agent_factory/AGENT_GENERATION_GUIDE|AGENT_GENERATION_GUIDE]]
