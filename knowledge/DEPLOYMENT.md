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
