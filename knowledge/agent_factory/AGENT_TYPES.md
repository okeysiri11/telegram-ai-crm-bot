---
title: ADOS Agent Types
aliases:
  - Agent Types
  - Agent Taxonomy
tags:
  - agent-factory
  - taxonomy
status: foundation
---

# ADOS Agent Types

## Purpose

Classify **all future agents** so the Factory can route generation, validation, and ownership correctly.

Every agent selects **exactly one primary category**. Secondary tags are optional; primary type drives registry filters and default reviewers.

Factory: [[AGENT_FACTORY]] · Template: [[AGENT_TEMPLATE]] · Registry: [[AGENT_REGISTRY]]

---

## Taxonomy overview

```text
Engineering · Business · Operations · Marketing · Finance
Security · Knowledge · Infrastructure · Creative
Communication · Customer Success · Automation
```

---

## Categories

### Engineering

**Mission focus:** Design, build, verify, and evolve platform software.  
**Examples:** Enterprise Architect, Backend / Frontend / QA / DevOps / Database / AI Engineers (see [[../agents/ENGINEERING_ORGANIZATION|ENGINEERING_ORGANIZATION]]).  
**Default reviewers:** Architect, QA, Security (as applicable), Orchestrator.  
**Risk profile:** Architecture and Core integrity.

### Business

**Mission focus:** Business capabilities (CRM, ERP, deals, vertical workflows).  
**Examples:** CRM AI, Marketplace AI, industry specialists.  
**Default reviewers:** Domain owner, Knowledge Engineer, Orchestrator.  
**Risk profile:** Process correctness; Twin entity consistency.

### Operations

**Mission focus:** Day-to-day running of the enterprise: incidents, runbooks, ops centers.  
**Examples:** Operations assistant, incident triage agent.  
**Default reviewers:** DevOps, Security, Orchestrator.  
**Risk profile:** Production stability and blast radius.

### Marketing

**Mission focus:** Campaigns, content ops, brand-aligned production workflows.  
**Examples:** Campaign planner, content production agent.  
**Default reviewers:** Domain owner, Creative (consult), Orchestrator.  
**Risk profile:** Brand and channel policy.

### Finance

**Mission focus:** Money movement visibility, invoices, budgets, financial controls.  
**Examples:** Finance AI, treasury analyst agent.  
**Default reviewers:** Security, domain owner, Orchestrator; CEO for irreversible money actions.  
**Risk profile:** High — financial and compliance.

### Security

**Mission focus:** Trust boundaries, access, threat review, policy enforcement.  
**Examples:** Security Engineer agent, policy auditor.  
**Default reviewers:** Security peer + Orchestrator; CEO for waivers.  
**Risk profile:** Critical — Blocks are binding.

### Knowledge

**Mission focus:** Knowledge fabric, docs coherence, memory, agent specs, registries.  
**Examples:** Knowledge Engineer, documentation curator.  
**Default reviewers:** Documentation Engineer, Architect (taxonomy), Orchestrator.  
**Risk profile:** Organizational drift and duplication.

### Infrastructure

**Mission focus:** Environments, packaging, cloud/desktop/mobile delivery substrates.  
**Examples:** Infra operator, deployment agent.  
**Default reviewers:** DevOps, Security, Orchestrator.  
**Risk profile:** Availability and secrets handling.

### Creative

**Mission focus:** Assets, narratives, visual/production creative packs (via production providers).  
**Examples:** Creative director agent, brand pack builder.  
**Default reviewers:** Marketing owner, Orchestrator.  
**Risk profile:** Brand consistency; provider cost.

### Communication

**Mission focus:** Omni-channel messaging, notifications, customer/employee comms routing.  
**Examples:** Communication orchestrator, Telegram ops agent.  
**Default reviewers:** Security, Operations, Orchestrator.  
**Risk profile:** PII, spam, channel abuse.

### Customer Success

**Mission focus:** Onboarding, health, retention, support playbooks.  
**Examples:** CS concierge, onboarding coach.  
**Default reviewers:** Business owner, Communication (consult), Orchestrator.  
**Risk profile:** Customer trust and data access.

### Automation

**Mission focus:** Workflows, triggers, scheduled jobs, RPA-like platform automations.  
**Examples:** Workflow builder agent, approval automator.  
**Default reviewers:** Architect, Security, QA, Orchestrator.  
**Risk profile:** Unbounded automation; must remain owner-gated for irreversible actions.

---

## Selection rules

1. Choose the category that matches **mission**, not the tools used.  
2. If two categories fit equally, prefer the one matching **primary KPI**.  
3. Engineering Org roles are always typed **Engineering** (even if they touch docs).  
4. Domain AIs (CRM, Port, Agro…) are typically **Business** (or vertical-specific under Business).  
5. An agent that only routes work is **Coordination** tier; type is still chosen by domain (often Automation or Engineering).

---

## Mapping to Factory pipelines

| Type | Extra validation emphasis |
|------|---------------------------|
| Engineering | Architecture first, tests mandatory |
| Security / Finance | Permissions + L3 for irreversible acts |
| Infrastructure / Operations | Rollback + secrets |
| Automation | Kill-switch / owner gate |
| Knowledge / Creative / Marketing | Duplication and brand/knowledge consistency |
| Communication / Customer Success | PII and channel policy |

---

## Related

[[AGENT_FACTORY]] · [[AGENT_TEMPLATE]] · [[AGENT_GENERATION_GUIDE]] · [[FACTORY_RULES]]
