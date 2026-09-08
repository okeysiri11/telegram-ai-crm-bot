# Odessa Prime Casino — Phase 4.4A Approved Physical Slots Hall

**Date:** 2026-09-08

Continues the uncommitted Phase 4.3 image-first hall. Routes, demo engine, and Odessa Gold are unchanged. Photoreal cabinet/hall/chair renders produced earlier in the sprint were chroma-keyed and swapped into the existing public paths — they were **not** regenerated.

## What this phase finishes

- Replace Phase 4.3 CSS-bake placeholders with processed photoreal cutouts (transparent PNG cabinets + JPEG hall + chair).
- Per-machine screen overlay geometry in `cabinetGeometry.generated.ts`.
- Six physical Odessa Prime chairs in front of the row.
- Hall identity plaque: ODESSA PRIME CASINO / SIX WORLDS. ONE DESTINATION.
- Viewport lock and live reel overlays kept.

## Architectural decisions

- Keep the Phase 4.3 contract: one image per cabinet + one live screen overlay. Rejected WebGL for this phase.
- Screen rects are per `id` because the six renders do not share one bezel layout. Variant fallbacks remain.
- Hall background is JPEG (`hall-bg.jpg`) because the 2560×1440 PNG was >5 MB.
