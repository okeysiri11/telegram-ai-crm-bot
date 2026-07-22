# Glossary — Terms

---
[[INDEX]] · [[glossary/COMPONENTS]] · [[ARCHITECTURE]]

## Overview
Shared vocabulary for the AI Ecosystem knowledge base.

## Architecture
Terms are organized from platform concepts → ecosystem → applications.

## Components

| Term | Definition |
|------|------------|
| **Platform Core** | Certified `platform_*` engine baseline v3.0.0 |
| **Ecosystem** | Cross-app layer (`ecosystem/`) v1.5.0-alpha |
| **Bridge** | Integration module that optionally calls Core/Ecosystem without mutating them |
| **Vertical / Application** | Domain product under `applications/` |
| **Agent** | Registered AI actor executed via orchestrator |
| **Workflow** | Multi-step process in the workflow engine |
| **Knowledge Graph** | Ecosystem structured knowledge (global_knowledge) |
| **Memory** | Session/semantic stores in `platform_memory` |
| **Sprint** | Numbered delivery increment (e.g. 11.1) |
| **Facade** | Application entry object aggregating domain services |
| **Production Ready** | Certified/commercial release posture |
| **Foundation Alpha** | First vertical scaffold release (Drone 1.0.0-alpha) |

## Relationships
Component catalog: [[glossary/COMPONENTS]]. Timeline: [[PLATFORM_TIMELINE]].

## APIs
“API prefix” means the versioned HTTP root for a surface (see [[API_REFERENCE]]).

## Future roadmap
Expand glossary as Legal and Drone sprints land ([[ROADMAP]]).
