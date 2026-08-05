---
title: ADOS Knowledge Graph
aliases:
  - Knowledge Graph
tags:
  - memory
  - knowledge-graph
status: foundation
---

# ADOS Knowledge Graph

## Purpose

Describe how **every enterprise object becomes a node**, connected by typed **relationships**, so Memory Engine search and Context Engine assembly can traverse meaning—not just keyword lists.

Enterprise Memory: [[ENTERPRISE_MEMORY]] · Index: [[KNOWLEDGE_INDEX]] · Decisions: [[DECISION_MEMORY]]

---

## Node principle

```text
Object exists in ADOS
    → Node ID + type + properties + security class
    → Relationships to other nodes
    → Indexed for hybrid search
```

Nodes are **references to truth** (module records, docs, registry entries)—not a second unverified database of business logic.

---

## Example node types

| Type | Meaning |
|------|---------|
| **User** | Human actor / owner / operator |
| **Company** | Tenant or business entity |
| **Project** | Program, repo, or product line |
| **Task** | Execution Task / Package work item |
| **Document** | Spec, guide, ADR, runbook |
| **API** | Endpoint or capability surface |
| **Database** | Store, schema, migration lineage |
| **Workflow** | Workflow pattern or instance |
| **Provider** | UPP provider (`provider.openai`, …) |
| **Agent** | Factory-registered agent |
| **Skill** | Reusable skill/capability pack |
| **Decision** | Architectural or operational decision |
| **Rule** | Policy, freeze rule, routing rule |
| **Event** | Significant bus/audit event (as graph fact) |
| **Relationship** | First-class edge record when the link itself carries metadata |

---

## Relationship examples

| Edge | From → To |
|------|-----------|
| `owns` | User → Project |
| `belongs_to` | Task → Project |
| `implements` | API → Module/Document |
| `depends_on` | Module → Provider / API |
| `assigned_to` | Task → Agent |
| `decided_in` | Decision → Document / ADR |
| `caused_by` | Incident Event → Task/Change |
| `learned_from` | Rule → Decision / Incident |
| `employs` | Workflow → Agent / Skill |
| `deployed_as` | Project → Deployment Event |

---

## Node record (logical)

```text
Node ID:        kg:task:PKG-123
Type:           Task
Properties:     { title, state, Package-ID, … }
Security:       tenant, classification
Sources:        [execution, registry, …]
Embeddings:     optional vector ref
Updated:        timestamp
```

---

## Graph rules

1. **Typed edges only** — no anonymous “related.”  
2. **Provenance** — every node cites source system / Package-ID when from execution.  
3. **No secrets as properties** — secret handles only.  
4. **Tenancy** — cross-company edges require explicit policy.  
5. **Providers & agents are nodes** — UPP/Factory register into the graph on activate.  
6. **Relationship nodes** — use when the link needs version, confidence, or review state.

---

## Traversal for context

Context Engine walks: Task → Project → Workspace docs → Enterprise Rules → prior Decisions/Incidents → optional external Knowledge provider nodes.

See [[CONTEXT_ENGINE]].

---

## Related

[[MEMORY_ENGINE]] · [[KNOWLEDGE_INDEX]] · [[../providers/UNIVERSAL_PROVIDER_PLATFORM|UPP]] · [[../agent_factory/AGENT_REGISTRY|AGENT_REGISTRY]]
