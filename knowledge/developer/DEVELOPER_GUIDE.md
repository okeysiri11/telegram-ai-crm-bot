---
title: Developer Guide
aliases:
  - Developer Guide
tags:
  - developer
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Developer Guide

## Overview
Developer portal — Developer Guide.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
- Start at [[INDEX]] and [[developer/ARCHITECTURE_GUIDE]]
- Run apps via existing repo tooling; do not mutate Core from apps
- After sprints: `python3 knowledge/tools/knowledge20_update.py`

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
