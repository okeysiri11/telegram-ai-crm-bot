---
title: ADOS Agent Memory
aliases:
  - Agent Memory
tags:
  - memory
  - agents
status: foundation
---

# ADOS Agent Memory

## Purpose

Describe memory classes **owned or namespaced by agents**, and how they relate to shared Enterprise Memory—without letting agents become siloed sources of truth.

Enterprise Memory: [[ENTERPRISE_MEMORY]] · Factory: [[../agent_factory/AGENT_LIFECYCLE|AGENT_LIFECYCLE]] · Contract: [[../agents/AGENT_CONTRACT|AGENT_CONTRACT]]

---

## Memory classes

### Personal memory

- Private to one agent instance/role (checklist state, preferred local notes).  
- Not visible to other agents by default.  
- May not store cross-tenant business secrets.  
- Cleared or archived on `AgentStopped` / Retire unless promoted.

### Shared memory

- Explicitly shared across agents via graph edges or shared namespaces (e.g. handoff buffers for a Package-ID).  
- Orchestrator-visible.  
- Prefer Working Memory on the Package over informal shared dumps.

### Team memory

- Practice or division scoped (Backend Team conventions, QA scenario packs).  
- Owner: Team Lead / Knowledge Lead.  
- Durable when curated into Knowledge Memory / Skills.

### Temporary memory

- Scratch for a single Execution Unit (tool dumps, drafts).  
- Aggressive TTL; never sole copy of a Decision.  
- Safe to drop on unit Complete.

### Archived memory

- Cold storage of personal/team scratch after agent retire or package Archive.  
- Retrievable via Decision/Historical search if promotion occurred; otherwise ops-only.

---

## Hierarchy vs Enterprise Memory

```text
Temporary → Personal → Team → Shared → Enterprise Knowledge / Decision Memory
```

Promotion upward requires Learning/Knowledge gates—not silent agent writes to long-term truth.

---

## Lifecycle hooks

| Event | Memory action |
|-------|----------------|
| AgentActivated | Load personal + team baselines via Context Engine |
| TaskAssigned | Attach Package working + shared handoff memory |
| Complete / Learning | Extract lessons; flush temporary |
| AgentStopped | Archive personal; revoke shared leases |

---

## Rules

1. Agents **read** enterprise context from Context Engine; they **write** durable facts through Memory Engine with provenance.  
2. No personal vector store as bypass of Knowledge Graph.  
3. Team memory does not override Enterprise Rules.  
4. Security context applies to all classes.

---

## Related

[[CONTEXT_ENGINE]] · [[MEMORY_ENGINE]] · [[../ados_os/EVENT_BUS|EVENT_BUS]] · [[../workforce/TEAM_INTERACTIONS|TEAM_INTERACTIONS]]
