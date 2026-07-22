# Knowledge Tools

## Overview
Documentation tooling for Sprint Knowledge 1.1.

## Architecture
`generate_docs.py` reads `../data/ecosystem_registry.json` and writes registries, statistics, agents, hubs, changelog, and release notes.

## Components
- `generate_docs.py` — main generator
- `../data/ecosystem_registry.json` — source of truth

## Relationships
[[automation/DOCUMENTATION_AUTOMATION]] · [[standards/DOCUMENTATION_STANDARDS]]

## Responsibilities
Regenerate living Markdown after sprints without touching application code.

## Interfaces
```bash
python3 knowledge/tools/generate_docs.py
```

## REST APIs
N/A

## Events
Manual or CI-triggered documentation regeneration.

## Future roadmap
Knowledge 1.2 read-only manifest scanners.

## References
[[registries/SPRINT_REGISTRY]]

## Related pages
[[INDEX]] · [[CHANGELOG]]
