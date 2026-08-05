---
title: ADOS Memory Engine
aliases:
  - Memory Engine
tags:
  - memory
  - search
status: foundation
---

# ADOS Memory Engine

## Purpose

The **Memory Engine** is the service API for **retrieving, writing, and searching** Enterprise Memory and the Knowledge Graph. All components use it; none bypass it for durable memory.

Enterprise Memory: [[ENTERPRISE_MEMORY]] · Graph: [[KNOWLEDGE_GRAPH]] · OS: [[../ados_os/MEMORY_MANAGER|MEMORY_MANAGER]]

---

## Operations

### Memory retrieval

- Fetch by Node ID, Package-ID, or typed key.  
- Enforce security context (tenant/roles/classification).  
- Return structured records + optional relationship neighborhood.

### Memory write

- Create/update nodes and edges with provenance.  
- Working/conversation writes are scoped and TTLed.  
- Long-term / knowledge / decision writes require gate metadata (Docs/Knowledge/Learning/Architect as applicable).  
- Emit `KnowledgeUpdated` (or memory-specific events) on durable changes.

### Memory search

- Entry point that dispatches to structured, semantic, vector, or hybrid modes.  
- Always scoped by caller context and allow-lists.

---

## Search modes

### Semantic search

Natural-language intent → ranked nodes/docs by meaning (embeddings + graph hints). Used for “what did we decide about providers?”

### Vector search

Pure embedding similarity over indexed chunks/nodes. Fast recall; may miss exact IDs—combine with structured filters.

### Structured search

Exact filters: type, Project, Agent ID, state, capability, date range, Package-ID. Used for “all Tasks in Project X with state Completed.”

### Hybrid search

```text
Structured filters
    ∩ / re-rank
Semantic + Vector candidates
    → Graph expansion (1–2 hops)
    → Dedupe + security filter
    → Ranked results
```

Default for Context Engine assembly.

---

## Write classes

| Class | Examples | Durability |
|-------|----------|------------|
| Ephemeral | Conversation turns | Short TTL |
| Working | Task plan, blockers | Package lifetime |
| Durable | Documents, Decisions, Rules | Long-term |
| Business | Company/deal facts via modules | Module-owned + indexed |

---

## Engine invariants

1. Agents call Memory Engine—they do not embed private vector DBs as source of truth.  
2. Providers may supply `knowledge` / `search` capabilities; results are **ingested or cited**, not silently treated as enterprise truth without promotion.  
3. Deletes are soft or governed; Learning may retain mistake/decision lineage.  
4. Align scope names with OS Memory Manager where runtime maps to architecture.

---

## Related

[[CONTEXT_ENGINE]] · [[KNOWLEDGE_INDEX]] · [[../ados_os/EVENT_BUS|EVENT_BUS]]
