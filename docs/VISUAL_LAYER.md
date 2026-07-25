# Visual Layer

Sprint **29.1** / Platform Builder **v1.8.0** / Visual Layer **1.0**

Projection layer that maps Logical Layer state into Visual State for the AI Operations Center and future AI City.

## Contract

Every projected object includes:

| Field | Purpose |
| --- | --- |
| `logical_id` | Stable logical identity |
| `visual_id` | Visualization identity (`viz_<type>_<id>`) |
| `object_type` | Kind of platform object |
| `current_state` | Live status vocabulary |
| `logical_state` | Phase / readiness for visualization |
| `visual_state` | Animation, glow, planned position/movement |
| `status` | Registry/lifecycle status |
| `relationships` | Links to other objects |
| `lifecycle` | Lifecycle phase |

## Live statuses

Idle · Working · Thinking · Learning · Analyzing · Collaborating · Waiting · Completed · Offline

## AI City foundation

Interfaces prepared for:

- Visual Layer
- Animated Objects
- Future Positioning
- Future Movement
- Future Live Organization

Positioning and movement remain planned (`planned: true`) until AI City runtime.

## API

- `GET /api/platform-builder/v1/operations/visual-layer`
- `GET /api/platform-builder/v1/operations/visual-ids`
- `GET /api/platform-builder/v1/operations/ai-city`

## Layout

- Backend: `applications/platform_builder/operations_center/engine.py` (`VisualLayer`)
- Knowledge: `knowledge/visual_layer/`
- Related: [AI_OPERATIONS_CENTER.md](./AI_OPERATIONS_CENTER.md)
- Tests: `tests/test_visual_layer_29_1.py`
