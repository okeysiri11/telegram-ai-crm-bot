---
title: Release Notes Generator
aliases:
  - GH Release Notes Generator
tags:
  - github
  - release-notes
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# Release Notes Generator

## Overview
Release notes pipeline for GitHub Releases.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
- Canonical notes: [[releases/RELEASE_NOTES]]
- CLI: `python3 knowledge/tools/release_notes.py`
- Enterprise refresh: `python3 knowledge/tools/knowledge20_update.py`

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
