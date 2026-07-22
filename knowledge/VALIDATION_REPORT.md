---
title: Validation Report
aliases:
  - Validation Report
tags:
  - validation
  - knowledge-1.2
generated: 2026-07-22
sprint: Knowledge 1.2
---
# Validation Report

## Overview
Knowledge validation run 2026-07-22.

## Architecture
Static checks over Markdown wiki links, sections, diagrams, and API registry presence.

## Components
- Markdown files scanned: **115**
- Broken wiki links: **21**
- Missing required sections: **0**
- Duplicate stems: **10**
- Missing diagrams: **0**
- Missing API registry files: **0**

### Broken wiki links (sample)
- `VALIDATION_REPORT.md -> [[Ecosystem]]`
- `VALIDATION_REPORT.md -> [[Wiki Links]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `VALIDATION_REPORT.md -> [[build_graph]]`
- `registries/API_REGISTRY.md -> [[Ecosystem]]`
- `diagrams/APPLICATION_GRAPH.md -> [[Ecosystem]]`
- `standards/DOCUMENTATION_STANDARDS.md -> [[Wiki Links]]`
- `diagrams/automation/AGENT_GRAPH.md -> [[build_graph]]`
- `diagrams/automation/ARCHITECTURE_GRAPH.md -> [[build_graph]]`
- `diagrams/automation/API_GRAPH.md -> [[build_graph]]`
- `diagrams/automation/WORKFLOW_GRAPH.md -> [[build_graph]]`
- `diagrams/automation/APPLICATION_GRAPH.md -> [[build_graph]]`
- `diagrams/automation/DEPLOYMENT_GRAPH.md -> [[build_graph]]`
- `diagrams/automation/KNOWLEDGE_GRAPH.md -> [[build_graph]]`
- `diagrams/automation/DEPENDENCY_GRAPH.md -> [[build_graph]]`

### Missing sections (sample)
- None

### Duplicate page stems
- `README`: README.md, tools/README.md, excalidraw/README.md, canvas/README.md, diagrams/automation/README.md
- `DEPLOYMENT`: DEPLOYMENT.md, diagrams/flows/DEPLOYMENT.md
- `INDEX`: INDEX.md, canvas/INDEX.md
- `CRM`: CRM.md, applications/CRM.md
- `KNOWLEDGE_GRAPH`: KNOWLEDGE_GRAPH.md, diagrams/automation/KNOWLEDGE_GRAPH.md
- `AUTO_MARKETPLACE`: sprints/AUTO_MARKETPLACE.md, applications/AUTO_MARKETPLACE.md
- `PORT_ERP`: sprints/PORT_ERP.md, applications/PORT_ERP.md
- `DRONE_PLATFORM`: sprints/DRONE_PLATFORM.md, applications/DRONE_PLATFORM.md
- `AGENT_GRAPH`: diagrams/AGENT_GRAPH.md, diagrams/automation/AGENT_GRAPH.md
- `APPLICATION_GRAPH`: diagrams/APPLICATION_GRAPH.md, diagrams/automation/APPLICATION_GRAPH.md

### Missing diagrams
- None

### Missing APIs docs
- None

### Missing architecture references (soft)
- None

## Relationships
[[INDEX]] · [[standards/DOCUMENTATION_STANDARDS]]

## Responsibilities
Detect documentation defects before they spread.

## Interfaces
`python3 knowledge/tools/check_links.py`

## REST APIs
Validates presence of API registry documentation only

## Events
validation_completed

## Future roadmap
Auto-fix stubs for broken links in Knowledge 1.3

## References
Wiki link regex scan

## Related pages
[[DASHBOARD]] · [[automation/DOCUMENTATION_ASSISTANT]]
