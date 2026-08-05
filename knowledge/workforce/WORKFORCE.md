---
title: ADOS Enterprise Workforce
aliases:
  - Workforce
  - AI Workforce
tags:
  - workforce
  - organization
  - enterprise
status: foundation
---

# ADOS Enterprise Workforce

## Purpose

The **ADOS Enterprise Workforce** is the organizational model for **all ADOS AI teams**.

It defines how executive leadership, the Orchestrator, and operating divisions collaborate so ADOS behaves as a **multi-team enterprise**, not a single assistant.

This package is **documentation only**. No application code changes.

Related foundations:

- Engineering roles: [[../agents/ENGINEERING_ORGANIZATION|ENGINEERING_ORGANIZATION]]
- Orchestration: [[../agents/ORCHESTRATOR|ORCHESTRATOR]]
- Agent contract & factory: [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]] · [[../agent_factory/AGENT_FACTORY|AGENT_FACTORY]]

---

## Complete AI organization hierarchy

```text
ADOS CEO
    │
ADOS Executive Board
    │
ADOS Orchestrator
    │
────────────────────────────────────────────────────────
Engineering Division
Business Division
Operations Division
Creative Division
Infrastructure Division
Knowledge Division
Customer Division
```

---

## Tier definitions

| Tier | Body | Authority |
|------|------|-----------|
| **Executive** | ADOS CEO | Final Go/No-Go, freeze breaks, irreversible production decisions |
| **Governance** | ADOS Executive Board | Cross-division policy, priorities, conflict arbitration above Orchestrator routine |
| **Coordination** | ADOS Orchestrator | Task understanding, routing, review gates, merge readiness |
| **Operating** | Divisions | Domain execution within mission and Factory rules |

---

## Executive layer

### ADOS CEO

- Owns platform vision and non-negotiable constraints.  
- Approves L3 items (architecture freeze breaks, production releases, security exceptions).  
- Does not implement; does not skip review gates.

### ADOS Executive Board

Standing leadership council (see [[ORGANIZATION_CHART]] for named seats):

- Aligns division priorities with portfolio goals.  
- Resolves multi-division conflicts the Orchestrator escalates.  
- Sponsors workforce standards (Factory, Contract, Lifecycle).  
- Reviews enterprise risk (security, finance, customer trust).

Board members typically include: CTO, Chief Architect, Engineering Manager, Product Manager, Security Lead, Knowledge Lead, Operations Lead, AI Production Lead—plus CEO as chair when convened.

---

## Coordination layer

### ADOS Orchestrator

- First responsibility: **understand**, then route.  
- Delegates to the correct **division** and specialist team.  
- Enforces: architecture before build, tests, docs, no unrelated refactors.  
- Owns review chain completeness and escalation into the Board/CEO when required.

Detail: [[../agents/ORCHESTRATOR|ORCHESTRATOR]] · [[TASK_ROUTING]] · [[ESCALATION_MODEL]]

---

## Operating divisions

### Engineering Division

**Mission:** Design, build, and verify platform software.  
**Includes:** Enterprise Architect, Backend, Frontend, QA, DevOps, Security (engineering practice), Database, AI Engineer, Documentation (engineering docs).  
**Primary type:** Engineering ([[../agent_factory/AGENT_TYPES|AGENT_TYPES]]).

### Business Division

**Mission:** Business capabilities—CRM, ERP, verticals, marketplace, deals.  
**Includes:** Domain business agents, Product-aligned specialists.  
**Primary type:** Business.

### Operations Division

**Mission:** Run the enterprise day-to-day—incidents, ops centers, runbooks, live health.  
**Includes:** Operations leads/agents, incident triage.  
**Primary type:** Operations.

### Creative Division

**Mission:** Brand, content packs, creative production workflows (via production providers).  
**Includes:** Creative / marketing production agents.  
**Primary types:** Creative, Marketing.

### Infrastructure Division

**Mission:** Environments, packaging, cloud/desktop/mobile substrates, reliability plumbing.  
**Includes:** Infra operators, deployment specialists.  
**Primary type:** Infrastructure.

### Knowledge Division

**Mission:** Knowledge fabric, agent specs, registries, memory coherence, documentation taxonomy.  
**Includes:** Knowledge Engineer, Documentation Engineer (knowledge-facing), Factory curators.  
**Primary type:** Knowledge.

### Customer Division

**Mission:** Onboarding, support, success, customer communication quality.  
**Includes:** Customer Success and Communication specialists.  
**Primary types:** Customer Success, Communication.

---

## Cross-division principles

1. **Single ownership** of each work package.  
2. **No duplicate responsibilities** across divisions (Factory + Registry).  
3. **Architecture first** when structure changes.  
4. **Documentation and testing mandatory** for behavioral change.  
5. **Delegation before implementation** (Orchestrator discipline).  
6. Divisions **consult**; they do not silently reassign ownership.

---

## How work enters the workforce

```text
Owner / CEO request
    → Orchestrator understands & classifies
    → Routes to Division + Team ([[TASK_ROUTING]])
    → Teams collaborate ([[TEAM_INTERACTIONS]])
    → Escalations follow [[ESCALATION_MODEL]]
    → Communication uses [[COMMUNICATION_PROTOCOL]]
    → Execution follows [[WORKFLOW_PATTERNS]]
```

---

## Success criteria

- Every AI team maps to a division.  
- Every task has a routed owner and review path.  
- Multi-agent feature work can run from intake to deployment without a “god agent.”  
- Escalations and communication states are explicit.

---

## Related pages

[[ORGANIZATION_CHART]] · [[TEAM_INTERACTIONS]] · [[TASK_ROUTING]] · [[ESCALATION_MODEL]] · [[COMMUNICATION_PROTOCOL]] · [[WORKFLOW_PATTERNS]]
