---
title: ADOS Session Manager
aliases:
  - Session Manager
tags:
  - runtime
  - sessions
status: foundation
---

# ADOS Session Manager

## Purpose

Describe **session types** the AI Runtime uses to bind identity, context, and recovery state around agent execution.

AI Runtime: [[AI_RUNTIME]] · Agent Memory: [[../memory/AGENT_MEMORY|AGENT_MEMORY]] · Context: [[../memory/CONTEXT_ENGINE|CONTEXT_ENGINE]]

---

## Session types

### Workspace Session

- Host/IDE or OS workspace binding (e.g. Cursor workspace, operator console).  
- Carries edition, open surfaces, user identity.  
- Parent for nested Project/Conversation sessions.

### Project Session

- Scoped to a Project node / repo / program.  
- Loads Project memory and module allow-lists.  
- Multiple Agent Sessions may share one Project Session.

### Conversation Session

- Interactive dialogue thread (chat, Telegram, in-app).  
- Holds conversation memory (volatile); promotes summaries only via gates.  
- Maps to Interactive Queue work.

### Agent Session

- One agent instance run: Created→…→Archived.  
- Holds reservations, heartbeats, tool state, Package-ID link.  
- Primary unit Supervisor monitors.

### Shared Session

- Cross-agent handoff buffer for a Package-ID (Shared memory view).  
- Participants listed; Orchestrator visible.  
- Closed at merge point or package Archive.

### Recovery Session

- Rehydrates after crash, forced cancel, or host restart.  
- Reads Execution Log + working memory checkpoints.  
- May resume Waiting/Running or mark Failed if unsafe.

---

## Session graph (typical)

```text
Workspace Session
    └── Project Session
            ├── Conversation Session (optional)
            ├── Agent Session (Backend)
            ├── Agent Session (Frontend)
            └── Shared Session (Package-ID)
```

Emergency work may attach Recovery Session under Project Session.

---

## Lifecycle

| Event | Action |
|-------|--------|
| Start work | Create/attach sessions; Initialize agent |
| Heartbeat | Refresh Agent Session lease |
| Handoff | Update Shared Session artifacts |
| Complete | Close Agent Session; keep Project as needed |
| Crash | Open Recovery Session from log |
| Archive | Flush temps; retain log/graph refs |

---

## Rules

1. Every Running agent has exactly one Agent Session.  
2. Security context is immutable for the session lifetime (re-auth = new session).  
3. Shared Session is not a dump of secrets.  
4. Recovery never skips Review gates already required.

---

## Related

[[AGENT_RUNTIME]] · [[EXECUTION_LOG]] · [[AGENT_COMMUNICATION_PROTOCOL]]
