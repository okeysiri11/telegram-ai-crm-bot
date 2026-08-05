---
title: ADOS Knowledge Index
aliases:
  - Knowledge Index
tags:
  - memory
  - indexing
status: foundation
---

# ADOS Knowledge Index

## Purpose

Describe **what is indexed** for Memory Engine search and how index domains stay aligned with the Knowledge Graph.

Enterprise Memory: [[ENTERPRISE_MEMORY]] · Graph: [[KNOWLEDGE_GRAPH]] · Memory Engine: [[MEMORY_ENGINE]]

---

## Indexed domains

| Domain | Examples indexed |
|--------|------------------|
| **Projects** | Project nodes, membership, status, links to modules |
| **Modules** | CRM, ERP, Marketplace, … manifests, owners, APIs |
| **Documents** | Specs, guides, ADRs, runbooks, release notes |
| **Providers** | Provider ID, capabilities, health summaries, fallbacks |
| **Workflows** | Pattern defs, instances, stage templates |
| **API** | Endpoints, schemas, registry entries |
| **Architecture** | Boundaries, placement decisions, freeze rules |
| **Agents** | Registry entries, types, lifecycle state |
| **Skills** | Skill packs, routing tags, version |

Also indexed when present: Decisions, Reviews, Deployments, Incidents, Lessons ([[DECISION_MEMORY]]).

---

## Index record

```text
Index ID:     …
Domain:       Documents | API | …
Node ID:      kg:…
Tokens / embeddings / fields
Security class + tenant
Updated_at
```

---

## Indexing triggers

| Trigger | Action |
|---------|--------|
| Document publish / Knowledge Update | Reindex Document + edges |
| AgentActivated / Registry change | Reindex Agent |
| Provider register/health change | Reindex Provider (non-secret) |
| Workflow register | Reindex Workflow |
| Architecture Decision written | Reindex Decision + Architecture |
| DeploymentCompleted | Reindex Deployment lineage |
| Module manifest change | Reindex Module + API |

Emit `KnowledgeUpdated` (or index-updated subtype) after durable reindex.

---

## Index quality rules

1. Secrets and raw credentials never indexed.  
2. Business PII follows classification and retention.  
3. Stale index entries tombstoned when nodes retire.  
4. Hybrid search relies on both **fields** (structured) and **embeddings** (semantic).  
5. External provider hits are not auto-indexed as enterprise truth until promotion.

---

## Related

[[CONTEXT_ENGINE]] · [[LEARNING_ENGINE]] · [[../providers/PROVIDER_REGISTRY|PROVIDER_REGISTRY]] · [[../agent_factory/AGENT_REGISTRY|AGENT_REGISTRY]]
