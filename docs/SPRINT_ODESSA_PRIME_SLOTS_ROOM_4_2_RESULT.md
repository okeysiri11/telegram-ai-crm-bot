# Odessa Prime Casino — Phase 4.2 Slots Hall Visual Correction

**Date:** 2026-09-05  
Visual pass over the Phase 4.1 card-like cabinets. Routes and demo engine unchanged.

## Corrections

- Compact casino header + secondary nav so six full cabinets fit one desktop viewport.
- Cabinet anatomy is a vertical machine stack: side walls, topper/jackpot, hooded reel screen, belly, sloped control deck, coin tray, chair SVG.
- Machines sit on a reserved floor band instead of stretching over the carpet.
- Reel symbols render in the hall before click.
- Floor, columns, chandelier wash, and depth machines stay visible under the row.
- Ultrawide side padding is removed on the slots hall so 1920×1080 uses the full aisle.

## Visual acceptance (1920×1080 Chromium screenshot)

1. Slot-machine row rather than six website cards: **YES**
2. Cabinet / topper / reels / control deck / chair identifiable on each machine: **YES**
3. Reel symbols visible before click: **YES**
4. Floor + depth + casino lighting: **YES**
5. All six machines fully visible with no document vertical scroll: **YES** (`scrollHeight === clientHeight === 1080`)

## Architectural decisions

- Extend the existing React + CSS `PhysicalSlotMachine` / `SlotsHall` path. No WebGL, no new package, no engine rewrite.
- Keep `/casino/slots/:machineId` and Odessa Gold routes unchanged.
