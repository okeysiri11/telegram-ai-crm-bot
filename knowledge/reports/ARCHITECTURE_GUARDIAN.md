---
title: Architecture Guardian Report
aliases:
  - Architecture Guardian
tags:
  - guardian
  - knowledge-1.3
generated: 2026-07-22
sprint: Knowledge 1.3
---
# Architecture Guardian Report

## Overview
Summary of architectural violations and detector results.

## Architecture
Detectors: violations, duplicates, circular deps, abstractions, misplaced code, orphans, unused APIs, dead docs.

## Components
- Violations: **2**
- Circular dependency chains: **0**
- Duplicate doc stems: **11**
- Missing abstractions: **0**
- Misplaced code signals: **0**
- Orphan signals: **0**
- Unused API doc signals: **0**
- Dead documentation candidates: **17**

### Violations (sample)
- [high] cross_app_import: `applications.auto_marketplace` imports `applications.port_erp` — prefer bridges only
- [high] cross_app_import: `applications.auto_marketplace` imports `applications.agro_marketplace` — prefer bridges only

### Circular
- None

## Relationships
[[DEPENDENCY_REPORT]] · [[TECHNICAL_DEBT]] · [[ARCHITECT_RECOMMENDATIONS]]

## Responsibilities
Continuously validate AI Ecosystem architecture rules.

## Interfaces
`python3 knowledge/tools/architecture_check.py`

## REST APIs
N/A (analysis only)

## Events
architecture_check_completed

## Future roadmap
[[ROADMAP]]

## References
[[automation/ARCHITECTURE_GUARDIAN]]

## Related pages
[[PROJECT_HEALTH]] · [[INDEX]]
