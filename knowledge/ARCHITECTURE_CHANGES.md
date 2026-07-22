---
title: Architecture Changes
aliases:
  - Architecture Changes
  - Architecture Diff
tags:
  - architecture
  - diff
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Architecture Changes

## Overview
Architecture diff generated 2026-07-22 from Git + module scan (Knowledge 1.2).

## Architecture
Compare previous `project_snapshot.json` to current repository layout.

## Components
### Added modules
- None

### Modified modules
- None

### Removed modules
- None

### Renamed (git signals)
- None

### Detected architecture notes
- None

## Relationships
[[ARCHITECTURE]] · [[ARCHITECTURE_DASHBOARD]] · [[diagrams/architecture/MODULE_RELATIONSHIPS]]

## Responsibilities
Explain structural delta for architects and sprint planners.

## Interfaces
Produced by `documentation_assistant.py`.

## REST APIs
API deltas listed in release notes when `api` area touched.

## Events
snapshot_compared, architecture_diff_written

## Future roadmap
[[ROADMAP]]

## References
`knowledge/data/project_snapshot.json`

## Related pages
[[VALIDATION_REPORT]] · [[releases/RELEASE_NOTES]] · [[INDEX]]

### Impact analysis
- Area `agents` requires doc refresh
- Area `dashboards` requires doc refresh
- Area `knowledge` requires doc refresh

### Dependencies
- Applications depend on Platform Core + Ecosystem via bridges only
- Knowledge tools must not mutate runtime packages
