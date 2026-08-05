---
title: ADOS Organization Chart
aliases:
  - Organization Chart
  - Reporting Structure
tags:
  - workforce
  - org-chart
status: foundation
---

# ADOS Organization Chart

## Purpose

Define the **reporting structure** for the Enterprise Workforce—human-equivalent leadership seats that AI roles and division leads map into.

Workforce: [[WORKFORCE]] · Escalation: [[ESCALATION_MODEL]]

---

## Reporting structure (executive + leads)

```text
                            ADOS CEO
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
             CTO        Chief Architect    Product Manager
              │                 │                 │
              │                 │                 │
     Engineering Manager   (architecture)   (portfolio/roadmap)
              │
    ┌─────────┼─────────┬──────────┬──────────┐
    │         │         │          │          │
 Security   Knowledge  Operations  AI Production  (matrix to divisions)
   Lead       Lead       Lead         Lead
```

**Orchestrator** reports operationally to the **CEO** (coordination mandate) and works **with** the Executive Board; it is not a substitute for CTO/Architect authority on structure.

---

## Role definitions

### CEO

| | |
|--|--|
| **Reports to** | Owner / board of the enterprise (external to ADOS AI org) |
| **Direct reports** | CTO, Chief Architect, Product Manager, Orchestrator (coordination), Executive Board attendees |
| **Authority** | L3 approvals, freeze breaks, production Go/No-Go |
| **Does not** | Implement features; bypass review |

### CTO

| | |
|--|--|
| **Reports to** | CEO |
| **Focus** | Technology strategy, engineering capacity, platform reliability trajectory |
| **Partners with** | Chief Architect (structure), Engineering Manager (delivery), Security Lead (risk) |
| **Division span** | Engineering + Infrastructure (strategic) |

### Chief Architect

| | |
|--|--|
| **Reports to** | CEO (solid); advises CTO |
| **Focus** | System boundaries, module placement, ADR-level decisions |
| **Maps to** | Enterprise Architect agent / practice |
| **Authority** | Architecture Approve / Redesign / Escalate; blocks structural anti-patterns |

### Engineering Manager

| | |
|--|--|
| **Reports to** | CTO |
| **Focus** | Delivery of Engineering Division work packages, staffing of specialist agents, quality cadence |
| **Partners with** | Product Manager (scope), QA practice, Orchestrator (routing) |

### Product Manager

| | |
|--|--|
| **Reports to** | CEO |
| **Focus** | Roadmap, prioritization, acceptance intent, Business/Customer alignment |
| **Partners with** | Orchestrator (intake clarity), Business & Customer Divisions |

### Security Lead

| | |
|--|--|
| **Reports to** | CTO (solid); dotted to CEO for material risk |
| **Focus** | Trust boundaries, permissions, threat review, waiver policy |
| **Authority** | Security **Block** is binding without CEO L3 waiver |
| **Division span** | Cross-cutting; strongest with Engineering & Infrastructure |

### Knowledge Lead

| | |
|--|--|
| **Reports to** | Chief Architect (taxonomy) / CEO (enterprise knowledge mandate) |
| **Focus** | Knowledge Division, registries, agent Factory coherence, docs discoverability |
| **Partners with** | Documentation practice, Agent Factory curators |

### Operations Lead

| | |
|--|--|
| **Reports to** | CTO |
| **Focus** | Operations Division—incidents, runbooks, live health, ops centers |
| **Partners with** | Infrastructure Division, Security Lead |

### AI Production Lead

| | |
|--|--|
| **Reports to** | CTO / Product Manager (matrix) |
| **Focus** | Creative & AI production workflows, provider production packs, campaign/content pipelines |
| **Division span** | Creative Division (+ Marketing-type agents); consults AI Engineer practice |

---

## Division lead mapping

| Division | Primary executive sponsor |
|----------|---------------------------|
| Engineering | Engineering Manager + Chief Architect |
| Business | Product Manager |
| Operations | Operations Lead |
| Creative | AI Production Lead |
| Infrastructure | CTO + Operations Lead |
| Knowledge | Knowledge Lead |
| Customer | Product Manager (+ Operations for live support) |

---

## Matrix note

Specialists (Backend, Frontend, QA…) report **practice-wise** through Engineering Manager / Chief Architect, and **task-wise** through Orchestrator packages. Task ownership never overrides architecture or security blocks.

---

## Related

[[WORKFORCE]] · [[TEAM_INTERACTIONS]] · [[ESCALATION_MODEL]] · [[../agents/ENGINEERING_ORGANIZATION|ENGINEERING_ORGANIZATION]]
