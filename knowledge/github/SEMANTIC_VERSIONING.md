---
title: Semantic Version Manager
aliases:
  - Semantic Versioning
  - SemVer
tags:
  - github
  - versioning
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Semantic Version Manager

## Overview
Semantic version policy for Knowledge infrastructure and guidance for apps.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
- Knowledge MAJOR.MINOR.PATCH — current **2.0.0**
- MAJOR: enterprise infra / incompatible doc contracts
- MINOR: additive generators/dashboards
- PATCH: fixes to docs/automation
- Platform Core remains `3.0.0`
- Version file: `knowledge/data/ecosystem_registry.json` meta.version

## Relationships
[[INDEX]] · [[dashboard/README]] · [[pipeline/README]]

## Responsibilities
Provide enterprise development infrastructure without changing runtime logic.

## Interfaces
Markdown + generators under `knowledge/tools/`.

## REST APIs
N/A — documentation/infrastructure only.

## Events
generated_by_enterprise_infra

## Future roadmap
[[ROADMAP]]

## References
[[automation/ENTERPRISE_INFRASTRUCTURE]]

## Related pages
[[INDEX]] · [[PROJECT_STATUS]] · [[EXECUTIVE_DASHBOARD]]
