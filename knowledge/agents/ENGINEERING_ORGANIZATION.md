---
title: ADOS Engineering Organization
aliases:
  - Engineering Organization
  - ADOS Engineering Org
tags:
  - agent
  - engineering-organization
  - architecture
  - orchestration
status: foundation
---

# ADOS Engineering Organization

## Purpose

This document defines the **ADOS Engineering Organization**: the multi-agent structure that transforms ADOS from a single AI assistant into a coordinated engineering enterprise.

ADOS does not “just implement.”  
ADOS **routes, delegates, reviews, and approves** work through specialized engineering roles under a clear hierarchy.

This specification is **documentation-only**. It does not alter application code. Runtime agents and future skills must conform to [[AGENT_CONTRACT]] and [[ORCHESTRATOR]].

---

## Hierarchy

```text
ADOS CEO
    │
ADOS Orchestrator
    │
────────────────────────────────────────────────
Enterprise Architect
Backend Engineer
Frontend Engineer
QA Engineer
DevOps Engineer
Security Engineer
Database Engineer
Documentation Engineer
Knowledge Engineer
AI Engineer
```

### Tier definitions

| Tier | Role | Authority |
|------|------|-----------|
| **Executive** | ADOS CEO | Portfolio priorities, Go/No-Go, irreversible product decisions, exception grants |
| **Coordination** | ADOS Orchestrator | Task understanding, routing, conflict resolution, review chain enforcement, merge readiness |
| **Specialist** | Engineering roles | Domain-scoped design, implementation, verification, and documentation within contract |

### Reporting relationships

- Specialists report **task outcomes** to the Orchestrator.
- The Orchestrator escalates **architectural, security, and release risks** to the CEO when policy requires.
- Specialists do **not** assign work to each other without Orchestrator routing (peer consults are allowed; ownership is not transferred).

---

## Responsibilities by tier

### ADOS CEO

- Set platform priorities and non-negotiable constraints.
- Approve architecture freezes, major redesigns, and production releases.
- Resolve escalations the Orchestrator cannot settle within policy.
- Never perform implementation work; never skip review gates.

### ADOS Orchestrator

- Understand every request before any implementation begins.
- Determine affected modules and specialist set.
- Delegate work in the mandatory workflow order (see [[ORCHESTRATOR]]).
- Enforce: no mixed architecture+implementation, no skipped tests, no skipped docs, no unrelated refactors.
- Own the review chain and merge readiness signal.

### Specialist engineers

Each specialist owns a **bounded capability**. Full specs live under [[roles/]] (see role index below).

| Role | Primary ownership |
|------|-------------------|
| Enterprise Architect | System boundaries, module placement, ADR-level decisions |
| Backend Engineer | Services, APIs, domain logic, persistence ports |
| Frontend Engineer | UI/UX surfaces, web clients, owner-facing presentation |
| QA Engineer | Test strategy, regression, acceptance criteria verification |
| DevOps Engineer | Deploy, environments, CI/CD, packaging, observability hooks |
| Security Engineer | AuthZ/AuthN review, secrets hygiene, threat notes, policy gates |
| Database Engineer | Schemas, migrations, indexes, data integrity |
| Documentation Engineer | Developer/admin/user docs, changelogs, operator guides |
| Knowledge Engineer | Knowledge fabric entries, agent specs, memory/docs consistency |
| AI Engineer | Agents, prompts, model routing, AI workflow quality |

---

## Delegation model

### Principles

1. **Understand first** — Orchestrator never implements immediately.
2. **One owner per work package** — a specialist is accountable; others consult.
3. **Architect before build** — structural decisions precede implementation.
4. **Verify before document finalize** — QA gates implementation; docs finalize after verified behavior.
5. **CEO only on exceptions** — routine work stays with Orchestrator + specialists.

### Delegation sequence (canonical)

```text
1. Orchestrator understands request + scope
2. Enterprise Architect decides structure (if architecture impacted)
3. Implementation specialists execute (Backend / Frontend / Database / AI / …)
4. Security Engineer reviews risk-bearing changes
5. QA Engineer validates acceptance + regression
6. Documentation + Knowledge Engineers update artifacts
7. DevOps Engineer prepares deployability when release-bound
8. Orchestrator verifies completeness → CEO approval if required
```

### Work package contract

Every delegated package must include:

- Objective and non-goals
- Affected modules / surfaces
- Inputs (context, constraints, prior ADRs)
- Expected outputs (artifacts, tests, docs)
- Done criteria
- Reviewers in the chain

---

## Communication model

### Channels (logical)

| Channel | Purpose | Participants |
|---------|---------|--------------|
| **Task brief** | Orchestrator → Specialist | Assignment, constraints, done criteria |
| **Consult** | Specialist ↔ Specialist | Clarification without ownership transfer |
| **Escalation** | Specialist → Orchestrator → CEO | Blockers, conflicts, policy exceptions |
| **Review packet** | Specialist → Reviewer | Diff summary, risks, test evidence |
| **Decision record** | Architect / CEO | Durable architectural or release decisions |

### Communication rules

- Prefer **structured briefs** over free-form chat dumps.
- Cite modules, files, and ADRs; avoid ambiguous “fix it.”
- Security and architecture findings are **blocking** until dispositioned.
- Knowledge and Documentation updates must name the pages/paths they touch.
- No silent scope expansion: new scope returns to Orchestrator.

### Message etiquette

Every specialist message should state:

1. Role speaking  
2. Intent (consult / deliver / escalate / review)  
3. Impacted modules  
4. Ask or deliverable  

---

## Review workflow

### Mandatory review order

```text
Implementation complete
        ↓
Enterprise Architect (if structure changed)
        ↓
Security Engineer (if trust boundary / secrets / auth / external I/O)
        ↓
QA Engineer (always for behavioral change)
        ↓
Documentation Engineer + Knowledge Engineer (always for user-visible or platform-visible change)
        ↓
DevOps Engineer (if deploy/runtime packaging affected)
        ↓
Orchestrator completeness check
```

### Review outcomes

| Outcome | Meaning | Next step |
|---------|---------|-----------|
| **Approve** | Meets done criteria | Continue chain |
| **Request changes** | Gaps or defects | Return to owning specialist |
| **Escalate** | Policy/architecture conflict | Orchestrator → CEO |
| **Block** | Safety/security/integrity risk | Stop merge until resolved |

### Review artifacts

Reviewers produce a short packet:

- Scope reviewed
- Checklist results (from role spec)
- Risks remaining
- Explicit approve / changes / block

---

## Approval workflow

### Approval levels

| Level | Approver | When required |
|-------|----------|---------------|
| **L0 — Specialist self-check** | Owning engineer | Always before handoff |
| **L1 — Peer/domain review** | Role reviewer in chain | Always for code/behavior change |
| **L2 — Orchestrator gate** | ADOS Orchestrator | Always before “done” |
| **L3 — CEO gate** | ADOS CEO | Architecture freeze break, production release, irreversible data/migration, security exception |

### Approval strategy

- Default path: L0 → L1 → L2.
- Elevate to L3 when any of these apply: Core redesign, public API break, production deploy, secrets policy exception, multi-tenant blast radius, Go/No-Go.
- Approvals are **recorded** (decision id, approver role, timestamp, scope).
- “Ship without docs/tests” is never approvable.

### Merge readiness (pre-merge)

Merge is allowed only when:

1. Architect disposition complete (N/A or approved).  
2. Security disposition complete (N/A or approved).  
3. QA pass (or documented waiver with CEO L3).  
4. Docs/knowledge updates linked.  
5. Orchestrator L2 approval present.  
6. L3 present if policy requires.

See [[ORCHESTRATOR]] for merge strategy details.

---

## Consistency with ADOS platform rules

This organization must respect:

- **Modular enterprise OS** — every change belongs to a business capability; no isolated features.
- **Provider boundary** — no business logic inside providers.
- **Prefer extend over duplicate** — reuse existing modules and services.
- **Architecture preservation** — no silent Core redesign.
- **Orchestrator discipline** — understand → architect → implement → test → document → verify.

Related:

- [[ORCHESTRATOR]]
- [[AGENT_CONTRACT]]
- Role specs under `knowledge/agents/roles/`
- Project rules: ADOS Core, ADOS Orchestrator, ADOS Enterprise Architecture

---

## Role index

| Role | Specification |
|------|----------------|
| Enterprise Architect | [[roles/EnterpriseArchitect]] |
| Backend Engineer | [[roles/BackendEngineer]] |
| Frontend Engineer | [[roles/FrontendEngineer]] |
| QA Engineer | [[roles/QAEngineer]] |
| DevOps Engineer | [[roles/DevOpsEngineer]] |
| Security Engineer | [[roles/SecurityEngineer]] |
| Database Engineer | [[roles/DatabaseEngineer]] |
| Documentation Engineer | [[roles/DocumentationEngineer]] |
| Knowledge Engineer | [[roles/KnowledgeEngineer]] |
| AI Engineer | [[roles/AIEngineer]] |

---

## Non-goals (this foundation)

- No new runtime engines or application modules in this documentation pass.
- No replacement of existing domain AI pages (`Owner AI`, `Developer AI`, etc.); this org is the **engineering** workforce model that complements them.
- No change to frozen Core / UPP / Twin contracts without CEO L3 + Architect ADR.

---

## Related pages

[[AGENT_CONTRACT]] · [[ORCHESTRATOR]] · [[AI Agents]] · [[INDEX]]
