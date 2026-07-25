# Visual Director Engine

Sprint **29.8** / Platform Builder **v1.15.0** / Director Engine **1.0**

Coordinates all visual activity across the platform.

**Does not generate business events.** Orchestrates how visual events are presented.

## Module

Platform Builder → Visual Director Engine (`/platform-builder/director`)

API: `/api/platform-builder/v1/director/*`

## Components

- Director Engine
- Scene Director
- Focus Manager
- Attention Manager
- Priority Manager

## Coordinated engines

Behavior · Simulation · Rendering · Theme · LOD

## Layout

- Backend: `applications/platform_builder/director/`
- Frontend: `src/web/platform-builder/director/`
- Knowledge: `knowledge/director/`
- Related: [SCENE_ORCHESTRATION.md](./SCENE_ORCHESTRATION.md)
- Tests: `tests/test_visual_director_29_8.py`
