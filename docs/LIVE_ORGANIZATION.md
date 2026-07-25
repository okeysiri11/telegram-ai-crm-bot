# Live Organization

Sprint **29.2** / Platform Builder **v1.9.0** / Live Organization **1.0**

Real-time visualization of the AI Organization hierarchy, relationships, workload, and activity — driven by the Visual Event Bus and Visual Layer.

## Components

| Component | Role |
| --- | --- |
| Live Organization Map | Hierarchy + connections with camera controls |
| Relationship Engine | Department, collaboration, knowledge, workflow, task links |
| Workload Engine | Load, queue, response time, availability, utilization, balance |
| Visual Event Bus | Subscribe / publish / poll — auto UI refresh |
| Animation Layer | Animation + AI City Movement / Position / Visual Object APIs |

## Event channels

AI Events · Workflow Events · Task Events · Knowledge Events · Organization Events · Registry Events

## AI City foundation

Movement API · Animation API · Position API · Visual Object API (positioning/movement planned until AI City runtime).

## Layout

- Docs: [AI_TEAM_MAP.md](./AI_TEAM_MAP.md)
- Knowledge: `knowledge/operations/live_organization/`
- Tests: `tests/test_live_organization_29_2.py`
