# Visual Behavior Engine

Sprint **29.3** / Platform Builder **v1.10.0** / Visual Behavior Engine **1.0**

Controls how platform objects visually behave.

**Business logic is NOT allowed.** The engine reacts only to events from the Visual Event Bus.

## Module

Platform Builder → Visual Behavior Engine (`/platform-builder/visual-behavior`)

API: `/api/platform-builder/v1/visual-behavior/*`

## Object state

Every object exposes:

- Visual State
- Behavior State
- Animation State
- Transition State

## Behaviors

Idle · Working · Thinking · Learning · Searching · Analyzing · Collaborating · Reviewing · Waiting · Completed · Offline

## Transitions

Idle → Working → Thinking → Collaborating → Completed → Idle

## Layout

- Backend: `applications/platform_builder/visual_behavior/`
- Frontend: `src/web/platform-builder/visual-behavior/`
- Knowledge: `knowledge/visual_behavior/`
- Related: [ANIMATION_FRAMEWORK.md](./ANIMATION_FRAMEWORK.md)
- Tests: `tests/test_visual_behavior_29_3.py`
