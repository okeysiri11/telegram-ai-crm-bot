# Viewport Engine

Sprint **29.4** / Platform Builder **v1.11.0** / Viewport Engine **1.0**

Smart viewport — render only visible objects.

## Features

- Viewport Detection
- Object Culling
- Lazy Rendering
- Dynamic Loading

## Layers

Background · Buildings · Departments · AI · Documents · Connections · Effects · Notifications

## Priority bands

- **High** — Visible AI, Running Tasks, Live Conversations
- **Medium** — Documents, Knowledge, Workflow
- **Low** — Archived Objects, Completed Tasks

## API

`GET /api/platform-builder/v1/rendering/viewport?x=0&y=0&width=800&height=600&zoom=1.0`

## Layout

- Backend: `applications/platform_builder/rendering/engine.py` (`ViewportEngine`, `LayerSystem`)
- Knowledge: `knowledge/viewport/`
- Tests: `tests/test_viewport_29_4.py`
