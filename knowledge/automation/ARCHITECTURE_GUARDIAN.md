---
title: Architecture Guardian
aliases:
  - Architecture Guardian
  - AI Project Architect
tags:
  - automation
  - architecture
  - knowledge-1.3
---

# AI Project Architect & Architecture Guardian

## Overview
Sprint **Knowledge 1.3** adds a read-only Architecture Guardian that validates AI Ecosystem layering, dependencies, documentation health, and quality scores — writing reports only under `knowledge/`.

## Architecture
```
repository scan (AST imports + inventory)
        ↓
knowledge/tools/architecture_guardian.py
        ↓
DEPENDENCY_REPORT · scores · debt · recommendations · health · history
        ↓
Dashboards + Obsidian bookmarks
```

## Components
- `architecture_guardian.py`
- CLI: `architecture_check.py`, `project_health.py`, `technical_debt.py`, `recommendations.py`, `full_architecture_review.py`
- Outputs: [[DEPENDENCY_REPORT]] · [[ARCHITECT_RECOMMENDATIONS]] · [[TECHNICAL_DEBT]] · [[PROJECT_HEALTH]] · [[ARCHITECTURE_HISTORY]] · [[reports/ARCHITECTURE_GUARDIAN]]

## Relationships
Complements [[automation/DOCUMENTATION_ASSISTANT]] (1.2). Does not modify Platform Core, applications, or APIs.

## Responsibilities
Detect violations, duplicates, circular deps, missing abstractions, misplaced code, orphans, unused API docs, dead documentation; compute architecture scores; recommend improvements.

## Interfaces
```bash
python3 knowledge/tools/architecture_check.py
python3 knowledge/tools/project_health.py
python3 knowledge/tools/technical_debt.py
python3 knowledge/tools/recommendations.py
python3 knowledge/tools/full_architecture_review.py
```

## REST APIs
N/A — analysis/documentation only.

## Events
`architecture_analyzed`, `scores_calculated`, `debt_updated`, `history_appended`

## Future roadmap
CI quality gate using guardian scores; Knowledge 1.4 auto-propose bridge stubs (docs only).

## References
[[standards/DOCUMENTATION_STANDARDS]] · [[tools/README]]

## Related pages
[[INDEX]] · [[EXECUTIVE_DASHBOARD]] · [[PROJECT_HEALTH]] · [[ROADMAP]]
