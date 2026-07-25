# Visual Rendering Engine

Sprint **29.4** / Platform Builder **v1.11.0** / Rendering Engine **1.0**

Efficiently displays every visual object in the platform.

**Business logic is NOT allowed.** All visual updates come from the Visual Event Bus and Visual Behavior Engine.

## Module

Platform Builder → Visual Rendering Engine (`/platform-builder/rendering`)

API: `/api/platform-builder/v1/rendering/*`

## Capabilities

- Render Queue
- Object Pool
- Layer Rendering
- Viewport Rendering
- Animation Rendering

## Design

- Enterprise Design System
- Dark Mode
- Responsive
- High Performance
- GPU Friendly

## Layout

- Backend: `applications/platform_builder/rendering/`
- Frontend: `src/web/platform-builder/rendering/`
- Knowledge: `knowledge/rendering/`
- Related: [VISUAL_LOD_ENGINE.md](./VISUAL_LOD_ENGINE.md), [VIEWPORT_ENGINE.md](./VIEWPORT_ENGINE.md)
- Tests: `tests/test_rendering_engine_29_4.py`
