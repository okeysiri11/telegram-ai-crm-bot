---
title: ADOS Task Routing
aliases:
  - Task Routing
  - Work Routing Rules
tags:
  - workforce
  - routing
status: foundation
---

# ADOS Task Routing

## Purpose

Define **rules for routing work** from the Orchestrator to the correct division and team.

Workforce: [[WORKFORCE]] · Interactions: [[TEAM_INTERACTIONS]] · Orchestrator: [[../agents/ORCHESTRATOR|ORCHESTRATOR]]

---

## Routing principle

```text
Understand request → Detect signals → Select Division → Select Team → Emit work package
```

Never route to “everyone.” Prefer the **smallest** team set that can own the outcome.

---

## Primary routing table

| Work signal | Routes to |
|-------------|-----------|
| **UI work** | Frontend Team (Engineering Division) |
| **API work** | Backend Team (Engineering Division) |
| **Security** | Security Team (Security Lead / Security Engineer; cross-cutting) |
| **Documentation** | Documentation Team (Engineering + Knowledge Division as needed) |
| **Knowledge updates** | Knowledge Team (Knowledge Division) |
| **Testing** | QA Team (Engineering Division) |
| **Schema / migrations** | Database Team (Engineering Division) |
| **Architecture / placement** | Chief Architect / Enterprise Architect |
| **Deploy / CI / packaging** | DevOps / Infrastructure Division |
| **Incidents / runbooks** | Operations Division |
| **CRM / ERP / vertical business** | Business Division |
| **Campaigns / creative packs** | Creative Division (+ AI Production Lead) |
| **Customer onboarding / success** | Customer Division |
| **Agent Factory / new agent** | Knowledge Division (+ AI Engineer / Architect) |
| **Provider integration** | Engineering (Backend/AI) + Infrastructure; **no business logic in providers** |

---

## Composite routing (common)

| Request shape | Ordered team set |
|---------------|------------------|
| Full-stack feature | Architect → Backend → Database → Frontend → Security* → QA → Docs → Knowledge → DevOps* |
| API-only bug | Backend → QA → Docs (if behavior visible) |
| UI-only polish | Frontend → QA → Docs |
| Auth change | Architect* → Backend → Security → QA → Docs → Knowledge |
| Prod outage | Operations → Infrastructure → Security* → Engineering if defect |
| New agent | Knowledge (Factory) → Architect* → AI Engineer → Review chain → Registry |

\* = include when impact detected.

---

## Routing rules

1. **Architecture first** if module boundaries or new surfaces are involved.  
2. **Security always** if auth, secrets, external I/O, or tenant data.  
3. **QA always** for behavioral change.  
4. **Docs + Knowledge** for platform-visible change.  
5. **Product Manager** clarifies acceptance when scope is ambiguous—before wide fan-out.  
6. If two teams claim ownership → Escalation ([[ESCALATION_MODEL]]), not double implementation.

---

## Anti-patterns

- Routing UI and API to one “full stack agent” without packages.  
- Skipping QA “because it’s small.”  
- Sending security work only to Backend.  
- Updating prompts without Knowledge/Factory registration.  
- Routing business logic into provider adapters.

---

## Related

[[WORKFLOW_PATTERNS]] · [[COMMUNICATION_PROTOCOL]] · [[../agent_factory/FACTORY_RULES|FACTORY_RULES]]
