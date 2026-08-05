---
title: ADOS Agent Communication Protocol (Runtime)
aliases:
  - Agent Communication Protocol
  - Runtime ACP
tags:
  - runtime
  - communication
  - agents
status: foundation
---

# ADOS Agent Communication Protocol

## Purpose

Describe **runtime messages between agents, Orchestrator, and Supervisor**. Aligns with workforce [[../workforce/COMMUNICATION_PROTOCOL|COMMUNICATION_PROTOCOL]] intents; this document names the **wire-level message kinds** the Runtime transports.

AI Runtime: [[AI_RUNTIME]] · Sessions: [[SESSION_MANAGER]] · Event Bus: [[../ados_os/EVENT_BUS|EVENT_BUS]]

---

## Message kinds

| Kind | Meaning |
|------|---------|
| **request** | Ask for work, data, or a decision |
| **response** | Answer a request (not terminal Complete) |
| **approval** | Explicit gate open (maps to Approval intent) |
| **review** | Evaluate deliverable; may precede approval |
| **handoff** | Transfer ownership/artifacts to next agent ([[../execution/HANDOFF_PROTOCOL|HANDOFF_PROTOCOL]]) |
| **broadcast** | Fan-out informational update to session participants |
| **event** | Fact notification (often mirrored on OS Event Bus) |
| **failure** | Hard failure signal with code and retryability |
| **heartbeat** | Liveness + progress token from Running agent |

---

## Envelope

```text
Kind:         request | response | …
From:         agent_session_id | orchestrator | supervisor
To:           agent_session_id | broadcast | orchestrator
Package-ID:   …
Correlation:  message_id / in_reply_to
Payload:      …
Security ctx: tenant/roles
Timestamp:    …
```

---

## Kind rules

### request / response

- Every request expects response or failure within timeout.  
- Orchestrator requests start most Agent Sessions.

### approval / review

- Only authorized roles (Decision Engine) produce binding approval.  
- Agents may request review; they do not self-approve L2/L3 gates.

### handoff

- Must include deliverable checklist fields.  
- Receiver Accept → their Agent Session Running; else Rework/Reject via review/failure.

### broadcast

- No silent ownership change.  
- Used for barrier notices, budget warnings, cancel storms.

### event

- Prefer OS Event Bus for cross-module facts; ACP event for in-session sync.

### failure

- Sets retryability; Supervisor + Retry Queue consult this.  
- Non-retryable → Failed instance.

### heartbeat

- Required while Running; missing → stalled detection.  
- Payload may include step name and %—not secrets.

---

## Mapping to workforce intents

| ACP kind | Workforce Intent |
|----------|------------------|
| request | Request |
| response | Response |
| review | Review |
| approval | Approval |
| handoff | Request/Complete to next |
| failure | Reject or Escalate path |
| (rework) | often review + request |

---

## Related

[[SUPERVISOR]] · [[EXECUTION_LOG]] · [[../execution/DECISION_ENGINE|DECISION_ENGINE]]
