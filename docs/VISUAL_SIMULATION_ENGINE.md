# Visual Simulation Engine

Sprint **29.7** / Platform Builder **v1.14.0** / Simulation Engine **1.0**

Visualizes real platform activity.

**Never creates fake events.** Every simulation originates from the Visual Event Bus.

## Module

Platform Builder → Visual Simulation Engine (`/platform-builder/simulation`)

API: `/api/platform-builder/v1/simulation/*`

## Components

- Simulation Engine
- Simulation Registry
- Simulation Timeline
- Simulation Controller

## Integrations

Visual Event Bus · Visual Behavior Engine · Visual Rendering Engine · Visual Layer

## Timeline controls

Pause · Resume · Speed Control · Step Forward · Replay Buffer Interface (future)

## Layout

- Backend: `applications/platform_builder/simulation/`
- Frontend: `src/web/platform-builder/simulation/`
- Knowledge: `knowledge/simulation/`
- Related: [LIVE_ENTERPRISE_SIMULATION.md](./LIVE_ENTERPRISE_SIMULATION.md)
- Tests: `tests/test_visual_simulation_29_7.py`
