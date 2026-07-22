---
title: Development Checklist
aliases:
  - Development Checklist
tags:
  - developer
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Development Checklist

## Overview
Developer portal — Development Checklist.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
- Design against architecture guide
- Add/adjust tests
- Update knowledge registries if public surface changes
- Run `check_links.py` and `architecture_check.py` for doc-heavy PRs
- Fill PR template architecture impact section

## Relationships
[[developer/README]] · [[INDEX]]

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
