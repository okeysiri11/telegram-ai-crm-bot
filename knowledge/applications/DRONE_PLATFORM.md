# Drone Platform

---
[[INDEX]] · [[ARCHITECTURE]] · [[diagrams/APPLICATION_GRAPH]] · [[API_REFERENCE]]


## Overview
**Drone Platform** (`applications/drone_platform/`) version **1.1.0-alpha** — UAV engineering ERP + AI workspace. Sprint **11.1** foundation. Detail: [[sprints/DRONE_PLATFORM]] · `docs/DRONE_PLATFORM.md`.

## Architecture
Facade: `DronePlatformApplication`. In-memory foundation store with domain services for registry, projects/engineering, firmware, missions, telemetry, inventory, documentation, and engineering AI. Bridges only — does not modify Core, Ecosystem, Agro, Port, or Auto.

## Components
- Component/UAV registry (motors, ESC, FC, radios, payloads, …)
- Engineering projects: BOM, CAD/PCB, wiring, revisions
- Firmware workspace: ArduPilot, PX4, INAV, Betaflight
- Mission planning: waypoints, geofences, rally, templates
- Inventory / warehouse / purchasing / lifecycle
- Manufacturing & simulation stubs
- AI engineering assistant (safe engineering scope only)

## Relationships
- [[PLATFORM_CORE]] + Ecosystem via bridges
- Peer apps untouched
- Diagram: [[diagrams/APPLICATION_GRAPH]]

## APIs
`/api/drone/v1` — health, registry, projects, engineering, firmware, missions, telemetry, inventory, documentation, ai

## Future roadmap
11.2+ manufacturing depth, fleet maintenance, advanced telemetry analytics ([[ROADMAP]]).

## Responsibilities
Document and navigate this concern within the Obsidian living vault (Knowledge 1.1).

## Interfaces
Wiki links, dashboards, and registries. Runtime interfaces described where applicable.

## REST APIs
See [[registries/API_REGISTRY]] and [[API_REFERENCE]] when this page owns HTTP surfaces; otherwise N/A.

## Events
Domain or documentation events as applicable; see related sprint pages.

## References
Repository `docs/`, manifests, [[standards/DOCUMENTATION_STANDARDS]].

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[ROADMAP]] · [[registries/COMPONENT_REGISTRY]]

## Sprint 11.2
Firmware Intelligence — [[drone/FIRMWARE_DASHBOARD]]
