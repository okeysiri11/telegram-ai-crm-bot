---
title: Knowledge Tools
aliases:
  - Knowledge Tools README
tags:
  - tools
  - knowledge-1.2
---

# Knowledge Tools

## Overview
Automation utilities for the Obsidian knowledge vault (Sprints Knowledge 1.1–1.2).

## Architecture
| Script | Purpose |
|--------|---------|
| `documentation_assistant.py` | Core assistant engine |
| `generate_docs.py` | Registry generator (1.1) |
| `update_docs.py` | Incremental doc sync |
| `build_graph.py` | Mermaid automation |
| `update_dashboards.py` | Dashboard refresh |
| `check_links.py` | Validation report |
| `release_notes.py` | Release notes + changelog |
| `project_report.py` | Project report |
| `update_everything.py` | Full pipeline |
| `architecture_guardian.py` | Architecture Guardian engine (1.3) |
| `architecture_check.py` | Architecture + dependency check |
| `project_health.py` | Project health |
| `technical_debt.py` | Technical debt register |
| `recommendations.py` | Architect recommendations |
| `full_architecture_review.py` | Full architect review |

## Components
- Data: `../data/ecosystem_registry.json`, `../data/project_snapshot.json`
- Docs: [[automation/DOCUMENTATION_ASSISTANT]] · [[automation/DOCUMENTATION_AUTOMATION]]

## Relationships
Outputs land only under `knowledge/` and `.obsidian/`.

## Responsibilities
Keep documentation synchronized without touching application source code.

## Interfaces
```bash
python3 knowledge/tools/update_everything.py
```

## REST APIs
N/A

## Events
CLI invocation → analysis → write markdown → save snapshot

## Future roadmap
CI workflow calling `update_docs.py` on merge.

## References
[[VALIDATION_REPORT]] · [[ARCHITECTURE_CHANGES]]

## Related pages
[[INDEX]] · [[DASHBOARD]]
