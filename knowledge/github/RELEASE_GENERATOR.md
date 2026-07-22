---
title: GitHub Release Generator
aliases:
  - Release Generator
tags:
  - github
  - release
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# GitHub Release Generator

## Overview
Documents how to cut GitHub Releases from Knowledge version metadata.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
- Current knowledge version: `2.0.0`
- Latest commit: `419eed4 Refactor CRM event handling to enhance publish/subscribe interactions and improve code clarity. This update optimizes integration with the event bus and supports the ongoing unification of event management across the platform.`
- Uses [[github/RELEASE_NOTES_GENERATOR]] + [[releases/RELEASE_NOTES]]
- Suggested tag: `knowledge-v2.0.0`
- Command sketch: `gh release create knowledge-v2.0.0 -F knowledge/releases/RELEASE_NOTES.md`

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
