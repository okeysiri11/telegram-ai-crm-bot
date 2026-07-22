---
title: Documentation Assistant
aliases:
  - Documentation Assistant
  - AI Documentation Assistant
tags:
  - automation
  - knowledge-1.2
  - assistant
generated: 2026-07-22
sprint: Knowledge 1.2
---

# AI Documentation Assistant

## Overview
Sprint **Knowledge 1.2** introduces an AI Documentation Assistant that analyzes the repository (Git + filesystem), detects incremental changes, and regenerates only the affected Obsidian documentation under `knowledge/`.

## Architecture
```
git status/diff/log + module/API/agent scans
        ↓
knowledge/tools/documentation_assistant.py
        ↓
incremental writers (diff, registries, dashboards, mermaid, validation)
        ↓
knowledge/data/project_snapshot.json
```

## Components
- `documentation_assistant.py` — core engine
- CLI: `update_docs.py`, `build_graph.py`, `update_dashboards.py`, `check_links.py`, `release_notes.py`, `project_report.py`, `update_everything.py`
- Snapshot: `knowledge/data/project_snapshot.json`
- Outputs: [[ARCHITECTURE_CHANGES]] · [[VALIDATION_REPORT]] · [[releases/RELEASE_NOTES]] · [[reports/PROJECT_REPORT]] · [[diagrams/automation/README]]

## Relationships
Extends [[automation/DOCUMENTATION_AUTOMATION]] from Knowledge 1.1. Does not modify Platform Core, Ecosystem, applications, or APIs.

## Responsibilities
- Detect modified/new/removed/renamed modules
- Detect API, architecture, sprint, and agent changes
- Update docs incrementally
- Validate wiki links and coverage

## Interfaces
```bash
python3 knowledge/tools/update_docs.py
python3 knowledge/tools/build_graph.py
python3 knowledge/tools/update_dashboards.py
python3 knowledge/tools/check_links.py
python3 knowledge/tools/release_notes.py
python3 knowledge/tools/project_report.py
python3 knowledge/tools/update_everything.py
```

## REST APIs
N/A — documentation tooling only (read-only API prefix discovery).

## Events
`repo_analyzed`, `changeset_detected`, `docs_updated`, `graphs_built`, `validation_completed`, `snapshot_saved`

## Future roadmap
Knowledge 1.3 — auto-stub broken links; optional CI hook.

## References
[[standards/DOCUMENTATION_STANDARDS]] · [[tools/README]]

## Related pages
[[INDEX]] · [[DASHBOARD]] · [[SPRINT_PROGRESS]] · [[ROADMAP]]
