---
title: Knowledge Tools
aliases:
  - Knowledge Tools README
tags:
  - tools
  - knowledge-2.0
---

# Knowledge Tools

## Overview
Automation utilities for the Obsidian knowledge vault (Knowledge 1.1 → **2.0**).

## Architecture
| Script | Purpose |
|--------|---------|
| `enterprise_infra.py` | Knowledge 2.0 enterprise engine |
| `knowledge20_update.py` | Full Knowledge 2.0 refresh |
| `generate_github.py` | GitHub automation pack |
| `generate_architecture_viz.py` | Architecture visualization |
| `generate_analytics_dashboards.py` | Analytics dashboards |
| `generate_developer_portal.py` | Developer portal |
| `generate_release_pipeline.py` | Release pipeline docs |
| `validate_release_pipeline.py` | Pipeline artifact validation |
| `documentation_assistant.py` | Knowledge 1.2 assistant |
| `architecture_guardian.py` | Knowledge 1.3 guardian |
| `generate_docs.py` / `update_*` / `check_links.py` | Living docs tooling |

## Components
- Packs: `knowledge/github`, `architecture`, `dashboard`, `developer`, `pipeline`
- Data: `knowledge/data/*`

## Relationships
[[automation/ENTERPRISE_INFRASTRUCTURE]] · [[automation/DOCUMENTATION_ASSISTANT]] · [[automation/ARCHITECTURE_GUARDIAN]]

## Responsibilities
Generate documentation and developer infrastructure only — never mutate runtime application logic.

## Interfaces
```bash
python3 knowledge/tools/knowledge20_update.py
python3 knowledge/tools/validate_release_pipeline.py
```

## REST APIs
N/A

## Events
enterprise_infra_run

## Future roadmap
[[ROADMAP]]

## References
[[INDEX]]

## Related pages
[[github/README]] · [[developer/README]] · [[pipeline/README]]
