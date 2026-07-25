# Visual LOD Engine

Sprint **29.4** / Platform Builder **v1.11.0** / Visual LOD Engine **1.0**

Level of Detail automatically changes based on zoom.

## Levels

| Level | Content |
|-------|---------|
| L0 | Organizations |
| L1 | Departments |
| L2 | AI Teams |
| L3 | AI Specialists |
| L4 | Documents · Tasks · Connections · Animations |

## Zoom bands

- L0: `0.0` – `0.35`
- L1: `0.35` – `0.55`
- L2: `0.55` – `0.75`
- L3: `0.75` – `0.9`
- L4: `0.9`+

## API

`GET /api/platform-builder/v1/rendering/lod?zoom=1.0`

## Layout

- Backend: `applications/platform_builder/rendering/engine.py` (`LODEngine`)
- Knowledge: `knowledge/lod/`
- Tests: `tests/test_visual_lod_29_4.py`
