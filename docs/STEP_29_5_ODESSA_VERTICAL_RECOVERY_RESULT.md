# STEP 29.5 — Odessa Source Vertical-Scale Recovery and Base-Mesh Cleanup

Date: 2026-08-23
Scope: `src/web/src/enterprise-city/odessa3d/` only. No calibration. No STEP 30. No source re-export.

---

## Phase 1 — Scale transform proven

Offline audit (`src/web/scripts/step29_5_height_audit.mjs`) traced the complete
transform chain for both reference meshes:

### WEB_height_199 (`TILE_04_04.glb`)

| Level | Value |
| --- | --- |
| Raw geometry AABB (local x, y, z) | 37.136 × 35.9 × **199.0** (local z ∈ [−199, 0]) |
| Mesh node scale | **0.01, 0.01, 0.01** (uniform) |
| Mesh node rotation | quaternion (0.7071, 0, 0, 0.7071) = +90° about X → local −Z maps to world +Y |
| Parent scale | none (mesh node is a scene-root node; flat hierarchy) |
| GLB root scale | none |
| Runtime loader scale | none (asset groups attach at identity) |
| Final world height | **1.9900 m** (y 0 → 1.99) |

### WEB_height_95 (`TILE_05_02.glb`)

| Level | Value |
| --- | --- |
| Raw geometry AABB (local x, y, z) | 2329.9 × 2791.0 × **95.0** (local z ∈ [−95, 0]) |
| Mesh node scale | **0.01, 0.01, 0.01** (uniform) |
| Mesh node rotation | +90° about X (local −Z → world +Y) |
| Final world height | **0.9500 m** |

### Root cause

**VERTICAL 0.01 INTRODUCED BY: mesh node scale (uniform 0.01) applied to
mixed-unit geometry.** The source geometry authored the horizontal axes in
**centimeters** (WEB_height_95 footprint: 2330 × 2791 raw → 23.3 × 27.9 m, a
plausible building) but the vertical axis in **meters** (raw span exactly
equals the encoded height: 199, 95, …). The exporter's single uniform 0.01
node scale converts cm→m correctly for X/Z and erroneously divides the
already-in-meters vertical by 100. It is not geometry-vertex corruption, not a
parent/GLB-root scale, and not a runtime loader scale.

## Phase 2 — Sample height validation

43 height-encoded meshes audited (all `WEB_height_N` in all 45 GLBs), covering
every requested band: 5–15 m: 13, 15–30 m: 7, 30–60 m: 8, 60–100 m: 4,
100+ m: 1 (WEB_height_199), plus sub-5 m samples.

| Metric | Value |
| --- | --- |
| Median ratio rendered/encoded | **0.010001** |
| Min / max ratio (raw name parse) | 0.00005 / 0.013 |
| Ratio after decimal-name parsing (`height_2_5` = 2.5 m) | 0.0100 within ±0.3 % for all extrusions |

The two apparent outliers are explained, not defects: `WEB_height_2_1` is a
genuinely flat polygon (h = 0.0001 m, a ground marking), and `_5`/`_6` suffixes
are decimal heights (2.5 m, 2.6 m) that match 0.01 exactly once parsed.

**VERTICAL_SCALE_DEFECT_CONFIRMED = YES**

## Phase 3 — Transform domain analysis

Classes audited from the STEP 29.4 inventory + this audit:

| Class | Authored Y | Blanket root ×100 result | Verdict |
| --- | --- | --- | --- |
| BUILDING / EXTRUSION | base at y≈0, height = relative extrusion (meters encoded, /100 rendered) | correct heights | must scale |
| GROUND / ROAD / LANDUSE / NATURAL / LEISURE / LABEL | authored layer ordering, ±1–5 mm around y=0 | spacing becomes **0.1–0.5 m** visible steps | must NOT scale |
| WATER | y = 0 (sea level) | stays 0 but coastal landuse at −0.002 would sink 0.2 m below it | must NOT scale |
| BASE (`WEB_base`) | y = −0.005 backing quad | sinks to −0.5 m (visible trench at coastline) | must NOT scale |
| Elevated flat structures (piers/decks/roofs at y 0.1–0.4) | absolute elevation, also /100 | move to intended 10–40 m | must scale (position) |

Conclusion: source Y has **mixed semantics** — relative extrusion for
buildings, mm layer ordering for the decal stack, absolute (also /100)
elevation for elevated flat structures. A blanket root Y×100 fails checks 3
and 4 of the phase (decal spacing and water/coast). Therefore the correction
is class-scoped: **scale world Y ×100 about the y=0 plane for every mesh
outside the ground-decal band** (band = height ≤ 20 mm AND |center-Y| ≤ 60 mm,
the same classifier as the STEP 29.4 decal fix); the decal band, water, labels
and base are untouched. Because every tile is scaled about the same world
plane with the same rule, tiles cannot separate vertically (verified by test).

## Phase 4 — Implementation

New module `src/web/src/enterprise-city/odessa3d/verticalRecovery.ts`:

- Feature flag: `ODESSA_VERTICAL_RECOVERY_ENABLED = true` (single constant),
  factor `ODESSA_VERTICAL_RECOVERY_FACTOR = 100`.
- `applyOdessaVerticalScaleRecovery(root)` conjugates each qualifying mesh's
  local matrix with a world-space Y-only scale:
  `local' = parentWorld⁻¹ · diag(1, 100, 1) · parentWorld · local`.
  The correction lives entirely at the transform level — **no vertex is
  rewritten**, no geometry buffer touched, and the scale matrix only affects
  the Y row, so world X/Z coordinates are mathematically identical.
- Idempotent (guarded by `userData.odessaVerticalRecovery`), reversible
  (`revertOdessaVerticalScaleRecovery` recomposes the untouched original node
  TRS), deterministic (same classifier, same plane, every load).
- Safety rails: meshes already taller than 3 m or that would exceed 500 m are
  skipped (nothing in the flattened source exceeds 1.99 m).
- Hooked into `scenePrep.prepareParsedScene` **before** the STEP 29.4 decal
  layering; runs per parsed asset before attach.
- Runtime visibility: `artifactDebug.verticalRecovery` diagnostics
  (enabled/factor/corrected mesh count/live city height) shown in the dev
  panel ("VERTICAL RECOVERY" row).

## Phase 5 — WEB_base decision

**Decision: keep `WEB_base` visible. It is required.**

- `WEB_base` is the ground-fill backing quad under the whole tile; the OSM
  landuse/ground layers above it do not guarantee full coverage. Hiding it
  would let the sky/fog background show through coverage gaps — a worse
  artifact (holes in the earth).
- The "giant gray slab" symptom had two causes, both now fixed: the city was
  100× too flat (nothing occluded the ground at low angles — fixed by this
  step) and the decal stack z-fought (fixed by STEP 29.4 polygon-offset
  ranking, where `WEB_base` at −5 mm gets the lowest rank and renders behind
  every other layer deterministically).
- The exact-identity dev toggle from STEP 29.4 (`setBasePlaneHidden`, matches
  the single mesh named `WEB_base` only) is preserved for A/B verification.
  No generic "hide large meshes" rule exists. Source GLB untouched; picking
  behavior unchanged.

## Phase 6 — Z-fighting fix preserved

- Recovery never touches the decal band, so the authored 1–5 mm ordering does
  **not** become 10–50 cm; layer separation remains GPU polygon-offset
  (depth-only), independent of physical city scale.
- Order of operations: vertical recovery first, then decal layering; ranks are
  computed from unchanged decal Y positions. Regression test
  "preserves the STEP 29.4 decal z-fighting fix after recovery" verifies base
  < landuse ordering and that recovered buildings are never depth-biased.

## Phase 7 — Tile seams

All 45 tiles are corrected by the same rule about the same world y=0 plane;
horizontal node transforms are untouched (verified by test: identical building
at a tile border in two tiles lands at identical world Y; `position.x/z`
unchanged). No coastline/port displacement is possible because X/Z are
mathematically unchanged and water/base are not scaled. Visual confirmation of
seams is part of the required manual Safari pass below.

## Phase 8 — Camera recalculation

No stale values are retained: city bounds are recomputed live from mesh world
matrices (`refreshGlobalBounds` → `Box3.expandByObject`), which now include the
corrected heights; camera fit, orbit min/max distance and the STEP 29.2
adaptive near/far clip all derive from those live bounds (re-synced on every
orbit interaction). The manifest's stale `maxY = 1.99` only participates in a
union and is dominated by the corrected geometry. Georeference untouched.

## Phase 10 — Numerical validation

41 corrected `WEB_height_N` samples (decal-band flats excluded — recovery does
not touch them by design):

| Metric | Value |
| --- | --- |
| Median absolute error (corrected vs encoded) | **0.000 %** |
| Maximum error | 0.210 % (WEB_height_2) |
| WEB_height_199 | 199.00 m (0.000 %) |
| WEB_height_95 | 95.00 m (0.000 %) |

## Phase 11 — Regression

- New tests (`verticalRecovery.test.ts`, 8 tests): flag/factor, encoded height
  restored with exact X/Z world extents, decal band untouched (base, water,
  landuse, labels), idempotency, reversibility, cross-tile seam consistency +
  horizontal transforms unchanged, elevated flat structures moved to intended
  elevation, already-tall meshes skipped, STEP 29.4 decal fix preserved.
- `npx vitest run src/enterprise-city` → **21 files, 267 tests, all pass**.
- Production build `npx vite build` → **pass**.
- Calibration/georeference code untouched (no geospatial module imports in
  `verticalRecovery.ts`; correction is Y-row-only by construction).

---

## FINAL REPORT

| Field | Value |
| --- | --- |
| VERTICAL_SCALE_DEFECT_CONFIRMED | **YES** (43 samples, median ratio 0.010001) |
| ROOT CAUSE TRANSFORM | Mesh-node uniform scale 0.01 over mixed-unit geometry (horizontal cm, vertical meters on local −Z, node rotated +90° X) |
| ORIGINAL HEIGHT RATIO | rendered = encoded × 0.01 |
| CORRECTION FACTOR | ×100, world-Y only, about y=0 |
| CORRECTION DOMAIN | All meshes outside the ground-decal band (buildings/extrusions/elevated structures); decal stack, water, labels, base excluded |
| SOURCE GLB MODIFIED | **NO** |
| WEB_BASE — HIDDEN | **NO** (required ground backing; documented above; exact-identity dev toggle preserved) |
| WEB_BASE — PICKING PRESERVED | YES |
| X/Z MODIFIED | **NO** (Y-row-only scale matrix; verified to numerical precision by test) |
| GEOREFERENCE MODIFIED | **NO** |
| CALIBRATION MODIFIED | **NO** |
| Z_FIGHTING FIX PRESERVED | YES (GPU polygon-offset, scale-independent; tested) |
| TILE SEAMS | None possible by construction (same plane/rule for all 45 tiles; tested); manual visual pass pending |
| WATER LEVEL | Unchanged (y=0, in excluded decal band) |
| BUILDING HEIGHT VALIDATION | 41 samples corrected to encoded heights |
| MEDIAN HEIGHT ERROR | **0.000 %** (max 0.210 %) |
| TESTS | PASS (267/267 enterprise-city; 8 new) |
| BUILD | PASS (`vite build`) |
| MANUAL SAFARI VALIDATION REQUIRED | **YES** — views A–I of Phase 9 (top-down, 45°, low oblique, horizon, downtown, port, coastline, tall buildings, 360° orbit) |
| SAFE TO CALIBRATE | **NO** |

STOP AFTER STEP 29.5. STEP 30 not started.
