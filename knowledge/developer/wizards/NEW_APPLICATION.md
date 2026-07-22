---
title: New Application Wizard
aliases:
  - New Application Wizard
tags:
  - wizard
  - developer
  - knowledge-2.0
generated: 2026-07-22
sprint: Knowledge 2.0
version: 2.0.0
---
# New Application Wizard

## Overview
Wizard — New Application Wizard.

## Architecture
Part of Enterprise Development Infrastructure (Knowledge 2.0).

## Components
- 1. Create `applications/<app_name>/`
- 2. Add config, manifest, application facade, shared store
- 3. Add `integrations/platform_bridge.py` + `ecosystem_bridge.py`
- 4. Register routes via app `api/register.py` (mount in api/server only as glue)
- 5. Add `knowledge/applications/<APP>.md` + registry entry
- 6. Run Knowledge update tools

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
