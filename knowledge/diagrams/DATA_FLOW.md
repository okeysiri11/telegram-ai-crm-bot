# Data Flow

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/PLATFORM_GRAPH]] · [[diagrams/AGENT_GRAPH]] · [[diagrams/APPLICATION_GRAPH]] · [[diagrams/DATA_FLOW]]


## Overview
Request and data movement from clients through the API gateway into Platform, Ecosystem, and applications.

## Architecture
```mermaid
sequenceDiagram
  participant C as Client
  participant GW as api/server.py
  participant APP as App Router
  participant BR as Bridges
  participant ECO as Ecosystem
  participant CORE as Platform Core
  C->>GW: HTTP /api/<app>/v1/...
  GW->>APP: dispatch
  APP->>BR: optional auth/memory/workflow
  BR->>ECO: identity/assistant (optional)
  BR->>CORE: memory/orchestrator/tools (optional)
  APP-->>C: JSON response
  C->>GW: /api/v1 or /management/v1
  GW->>CORE: platform handlers
  CORE-->>C: JSON response
```

## Components
- Gateway assembly in `api/server.py`
- App `api/register.py` modules
- Bridge stubs when Core/Ecosystem unavailable
- Observability via `/metrics` and health probes — [[DEPLOYMENT]]

## Relationships
Aligns with [[ARCHITECTURE]] layering and [[SECURITY]] auth middleware patterns.

## APIs
Full prefix table: [[API_REFERENCE]].

## Future roadmap
Async event-bus fan-out from Ecosystem communication layer into all apps ([[ROADMAP]]).
