# Plugin SDK


---
[[INDEX]] · [[PLATFORM_CORE]] · [[ARCHITECTURE]] · [[API_REFERENCE]]


## Overview
`platform_plugin_sdk` (**1.0.0**) and `platform_plugins` / `platform_tools` (Sprint **3.3**) provide the extension surface for tools and plugins without modifying Core internals.

## Architecture
Plugins register capabilities consumed by agents and workflows. Management bootstrap may initialize the plugin manager on API startup (`api/server.py`).

## Components
- Plugin SDK package
- Plugin manager / tool framework
- Certification docs: `docs/PLUGIN_SDK.md`, `docs/TOOLS.md`, `docs/CERTIFICATION_SDK.md`

## Relationships
- Used by [[AI_AGENTS]] and [[WORKFLOW_ENGINE]]
- Applications should prefer tools/plugins over forking Core
- Ties to [[SECURITY]] for trust boundaries

## APIs
SDK Python APIs; plugin lifecycle via platform management/plugin manager. See [[API_REFERENCE]].

## Future roadmap
Curated plugin marketplace for vertical connectors ([[ROADMAP]]).
