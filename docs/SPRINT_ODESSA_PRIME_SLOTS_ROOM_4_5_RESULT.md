# Odessa Prime Casino — Phase 4.5 Sit-down physical cabinet play

**Date:** 2026-09-08

Seated play mode over the accepted Phase 4.4A hall. Routes, demo engine, and hall art are unchanged.

## What shipped

- Hall click uses a ~720ms approach (140ms if `prefers-reduced-motion`).
- `/casino/slots/:machineId` renders `SeatedSlotCabinet`: the same PNG cabinet, live screen overlay, lower touchscreen meters, deck controls, physical SPIN. No chair in the foreground.
- `SlotReels` presents 5×3 columns with staggered strip animation while the existing engine result stays authoritative.

## Architectural decisions

- Presentation-only seated view. Rejected a second engine and WebGL.
- Keep `/casino/slots/:machineId` so existing tests and history stay valid.
