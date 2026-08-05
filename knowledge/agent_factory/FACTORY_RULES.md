---
title: ADOS Agent Factory Rules
aliases:
  - Factory Rules
tags:
  - agent-factory
  - governance
  - rules
status: foundation
---

# ADOS Agent Factory Rules

Non-negotiable operating rules for the Agent Factory.

Factory: [[AGENT_FACTORY]] · Guide: [[AGENT_GENERATION_GUIDE]] · Contract: [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]]

---

## 1. No duplicated responsibilities

- Before creating an agent, search [[AGENT_REGISTRY]] by mission and capabilities.  
- If overlap exists, **extend** the existing agent or **split** via Enterprise Architect—never mint a clone.  
- Two Production agents must not own the same primary responsibility.

## 2. Single ownership

- Every agent has exactly one **Owner**.  
- Every work package has exactly one **accountable specialist/agent**.  
- Consults do not transfer ownership.  
- Ownership changes require Orchestrator acknowledgment and registry update.

## 3. Architecture first

- Classify type ([[AGENT_TYPES]]) and placement before prompts or tools.  
- Structural or cross-module agents require Architect disposition.  
- Respect ADOS layers: no business logic in providers; prefer extend over duplicate.  
- Core redesign is forbidden without CEO L3 + Architect ADR.

## 4. Documentation mandatory

- No Production agent without a completed [[AGENT_TEMPLATE]]-based spec.  
- Platform-visible behavior changes require Documentation / Knowledge updates.  
- Registry entry and knowledge page must stay synchronized.

## 5. Testing mandatory

- Behavioral agents require a Testing-stage evidence pack before Review.  
- QA owns acceptance disposition for behavior-changing agents.  
- “Works in chat once” is not evidence.

## 6. Review mandatory

- Lifecycle path includes **Review** before **Approved**.  
- Security Blocks are binding.  
- Orchestrator L2 required for activation; CEO L3 when policy demands.  
- No auto-approve for security, architecture freeze breaks, or missing docs/tests.

## 7. Delegation before implementation

- Aligns with [[../agents/ORCHESTRATOR|ORCHESTRATOR]]: understand → route → architect (if needed) → implement → test → document → verify.  
- Factory generation itself is delegated work: authors do not self-activate to Production.  
- Agents must not implement outside their Limitations / Permissions.

---

## Enforcement

| Violation | Response |
|-----------|----------|
| Duplicate mission in Production | Deprecate duplicate; merge ownership |
| Missing docs/tests at activation | Block activation; return to Testing/Draft |
| Unregistered “shadow agent” | Do not route; require Factory intake |
| Permission overreach | Security Block; redesign permissions |
| Skip Review | Invalid status transition; audit note |

---

## Compliance statement

> An agent that violates Factory Rules is not an ADOS enterprise agent—even if it is clever.

---

## Related

[[AGENT_FACTORY]] · [[AGENT_LIFECYCLE]] · [[AGENT_REGISTRY]] · [[../agents/ENGINEERING_ORGANIZATION|ENGINEERING_ORGANIZATION]]
