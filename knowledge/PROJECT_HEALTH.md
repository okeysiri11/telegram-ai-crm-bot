---
title: Project Health
aliases:
  - Project Health
tags:
  - health
  - architecture
  - knowledge-1.3
generated: 2026-07-22
sprint: Knowledge 1.3
---
# Project Health

## Overview
Project health dashboard snapshot 2026-07-22.

## Architecture
Composite of architecture scores, inventory, and quality gates.

## Components
### Scores
| Metric | Score |
|--------|------:|
| Overall | **77.2** |
| Architecture quality | 84.0 |
| Documentation coverage | 100.0% |
| Module cohesion | 100.0 |
| Coupling (higher=better isolation) | 42.0 |
| Maintainability | 13.4 |
| Complexity | 100.0 |
| Scalability | 100.0 |
| Risk index (lower better) | 24 |

### Inventory
- Platform packages: 31
- Applications: 4
- Ecosystem modules: 17
- Python files: 2416
- Test files: 108
- Knowledge markdown: 122
- Documented agents: 12

### Quality gates
| Gate | Status | Issues |
|------|--------|-------:|
| folder_naming | ✅ PASS | 0 |
| module_naming | ✅ PASS | 0 |
| api_naming | ✅ PASS | 0 |
| documentation | ✅ PASS | 0 |
| wiki_links | ✅ PASS | 0 |
| mermaid_diagrams | ✅ PASS | 0 |
| dependency_rules | ❌ FAIL | 2 |

## Relationships
[[EXECUTIVE_DASHBOARD]] · [[TECHNICAL_DEBT]] · [[ARCHITECT_RECOMMENDATIONS]]

## Responsibilities
Provide a single health artifact for executives and architects.

## Interfaces
`python3 knowledge/tools/project_health.py`

## REST APIs
[[registries/API_REGISTRY]]

## Events
project_health_updated

## Future roadmap
[[ROADMAP]]

## References
Architecture Guardian

## Related pages
[[DASHBOARD]] · [[INDEX]] · [[VALIDATION_REPORT]]
