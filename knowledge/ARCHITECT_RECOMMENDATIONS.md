---
title: Architect Recommendations
aliases:
  - Architect Recommendations
  - AI Recommendations
tags:
  - architecture
  - recommendations
  - knowledge-1.3
generated: 2026-07-22
sprint: Knowledge 1.3
---
# Architect Recommendations

## Overview
AI Project Architect recommendations based on guardian findings.

## Architecture
Prioritize dependency rules (bridges only) and documentation graph hygiene.

## Components
### Suggested actions
- **Module split / boundaries:** replace cross-app imports with explicit bridge facades.
- **Documentation:** link or archive dead knowledge pages to reduce vault noise.
- **Tests:** increase automated test coverage near domain facades.
- **Coupling:** reduce wide imports; prefer narrow bridge interfaces.
- **Future:** federate app knowledge graphs into Ecosystem global knowledge (see [[ROADMAP]]).
- **Future:** keep Architecture Guardian in CI via `full_architecture_review.py`.

### Suggested refactoring targets
- No circular deps detected

### Suggested module / abstraction work
- None

### Misplaced code
- None

## Relationships
[[TECHNICAL_DEBT]] · [[DEPENDENCY_REPORT]] · [[PROJECT_HEALTH]]

## Responsibilities
Guide safe architectural evolution without runtime code edits from knowledge tools.

## Interfaces
`python3 knowledge/tools/recommendations.py`

## REST APIs
N/A

## Events
recommendations_generated

## Future roadmap
[[ROADMAP]]

## References
Architecture Guardian findings

## Related pages
[[ARCHITECTURE_HISTORY]] · [[EXECUTIVE_DASHBOARD]] · [[INDEX]]
