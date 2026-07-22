---
title: GitHub Enterprise Automation
aliases:
  - GitHub Enterprise
  - GitHub Automation
tags:
  - github
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# GitHub Enterprise Automation

## Overview
Knowledge 2.1 — GitHub enterprise automation pack for releases, tags, milestones, templates, and repository health.

## Architecture
Source-of-truth docs live in `knowledge/github/`; GitHub-native files under `.github/`.

## Components
- [[github/RELEASE_GENERATOR]]
- [[github/CHANGELOG_AUTOMATION]]
- [[github/SEMANTIC_VERSIONING]]
- [[github/TAG_GENERATOR]]
- [[github/RELEASE_NOTES_GENERATOR]]
- [[github/MILESTONE_GENERATOR]]
- [[github/REPOSITORY_HEALTH]]
- [[github/CONTRIBUTION_STATS]]
- [[github/REPOSITORY_DASHBOARD]]
- [[github/README_UPDATER]]
- [[github/BADGES]]
- Templates synced to `.github/`

## Relationships
[[INDEX]] · [[dashboard/README]] · [[pipeline/README]]

## Responsibilities
Provide enterprise development infrastructure without changing runtime logic.

## Interfaces
`python3 knowledge/tools/generate_github.py`

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
