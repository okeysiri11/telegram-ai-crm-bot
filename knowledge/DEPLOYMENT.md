# Deployment


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
Deployment guidance for Platform Core production posture, configuration layer (Sprint **5.4**), reliability/recovery (Sprint **5.3**), and application commercial releases (Agro/Port/Auto 2.0.0).

## Architecture
- Configuration & feature flags: `platform_configuration`
- Reliability / recovery engines
- Observability metrics (`/metrics`) and health probes
- App production engines (e.g. Auto/Port enterprise release modules)
- Repository docs: `docs/deployment.md`, `docs/OPERATIONS.md`, `docs/RELIABILITY.md`

## Components
- Health: liveness, readiness, deep health (apps)
- Metrics / telemetry
- DB health check
- Plugin manager startup hook
- Per-app production validation suites

## Relationships
- Depends on [[SECURITY]] and [[PLATFORM_CORE]] ops layers
- Application readiness flags in manifests (`production_ready`)
- Timeline: [[PLATFORM_TIMELINE]]

## APIs
Ops endpoints: `/liveness`, `/readiness`, `/health`, `/system/db-health`, `/metrics`, plus app `/health` and deep probes.

## Future roadmap
GitOps profiles per vertical and multi-region Ecosystem deployments ([[ROADMAP]]).

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
