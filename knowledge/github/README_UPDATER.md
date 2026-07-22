---
title: README Updater
aliases:
  - README Updater
tags:
  - github
  - readme
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# README Updater

## Overview
Guidance for refreshing repository README badges and knowledge pointers (does not overwrite root README automatically without explicit run flags).

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
- Knowledge entry: [[INDEX]]
- Badges: [[github/BADGES]]
- Developer portal: [[developer/README]]
- Generated stub: `knowledge/github/README_SNIPPET.md`

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
