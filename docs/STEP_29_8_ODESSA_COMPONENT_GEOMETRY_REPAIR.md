# STEP 29.8 — Odessa 3D Component-Level Geometry Repair

Merged-mesh decomposition + selective building recovery. Follows STEP 29.4
(z-fighting), 29.5 (broad vertical recovery), 29.6 (selective recovery),
29.7 (runtime forensics + mixed-domain skip).

---

## WHY 29.7 STILL LOOKED WRONG

STEP 29.7 proved the defect lives INSIDE merged vertex buffers and responded
by skipping whole-mesh recovery for every mixed-domain mesh (verdict
`skip-mixed-domain`). That was safe but blunt, with two consequences:

1. **Flattened real buildings inside mixed meshes stayed flat.** The 108
   mixed-domain meshes also contain cm-domain buildings with correct ≥ 2 m
   footprints whose heights were crushed ×100 by the exporter — the same
   proven 29.5 defect. Whole-mesh skip abandoned them, so large districts
   kept looking flat.
2. **Any environment still executing the pre-29.7 bundle renders the needle
   forest.** The 29.7 runtime forensics measured 0 needle components in the
   shipped pipeline, so a Safari session still showing "a forest of vertical
   needles" is either running a stale bundle (hard refresh + restarted dev
   server/build required) or showing the flat city misread at grazing
   angles. STEP 29.8 removes the ambiguity by repairing at the component
   level and adding component-level dev instrumentation.

The correct operation level is the connected component, not the mesh —
exactly what this step implements.

## NEW FORENSIC EVIDENCE (Phase 1–3 probes)

Scripts: `src/web/scripts/step29_8_placement_probe.mjs`,
`step29_8_shape_probe.mjs`, `step29_8_cluster_probe.mjs`.

**Miniature components (the needle source) have DESTROYED placement:**

| mesh | minis | median NN spacing | intended footprint (×100) | density |
|---|---|---|---|---|
| HEAVY_BUILDING_CHUNK_01_02_SUB_00_01 | 35,133 | 0.22 m | 15.4 m | 1.2 m²/component |
| WEB_build (TILE_04_00_REST_BATCH_01) | 8,460 | 0.59 m | 52.1 m | 26.7 m²/component |
| WEB_buildin100 (TILE_03_01) | 749 | 0.55 m | 42.1 m | 265 m²/component |

- Nearest-neighbor spacing 0.2–0.6 m vs intended 15–50 m footprints ⇒
  **in-place per-component ×100 mathematically guarantees mass overlap**.
- Cluster analysis (link 1 m): agglomerations of 1,000–5,500 minis spanning
  25–77 m with cluster spacing ~3.5 m ⇒ **per-cluster expansion overlaps
  too**; whole-mesh XYZ ×100 would inflate a 577 m strip to 57.7 km ⇒ absurd.
- Shape probe: minis are simple 16–32-vertex boxes, aspect ~1.2, ground-
  standing (baseY ≈ 0), non-chain layout (not fences — genuinely buildings,
  atlas/collapsed placement).

**Conclusion:** no affine transform about any pivot (component, cluster, or
mesh) can reconstruct the miniature districts. Their real-scale layout was
destroyed at export. Per the Phase 5 rule they are classified
**SOURCE_ANOMALY** and left bit-identical (≤ 0.25 m tall — microscopic,
never needles). Recovering them requires a source re-export, not a runtime
transform.

**What IS provably repairable:** cm-domain flattened buildings baked into
the same buffers — footprint ≥ 2 m per side, pre-height ≤ 3 m, ground
contact, post-height 2.5–250 m, aspect < 8. A world-Y ×100 stretch about
each component's own base grows them in place; X/Z stay bit-identical, so
neighbors cannot overlap.

## IMPLEMENTATION

- `src/web/src/enterprise-city/odessa3d/componentRepair.ts` (new):
  - `decomposeGeometry` — union-find over the index buffer + 1 mm-quantized
    position weld (integer spatial hash), world AABB per component.
  - `repairBuildingComponents` — Phase 2 classification per component
    (REPAIRED / MINIATURE / FLAT / UNCERTAIN), Phase 3/4 in-place vertex
    rewrite via the conjugated matrix `M⁻¹ · T(base) · S_y(100) · T(−base) · M`
    (positions) and its inverse-transpose (normals, renormalized) — correct
    under the real GLB node transform (−90° X rotation, uniform 0.01 scale).
    Indices, UVs, material groups, and every other vertex are untouched.
  - Phase 5 guards + per-component rollback (`SOURCE_ANOMALY` on failure);
    absolute needle guard (width < 1 m ∧ height > 10 m ⇒ reject).
  - Idempotence marker `userData.odessaComponentRepair` (version, counts);
    exact-reversal backups + per-vertex class labels in a module `WeakMap`
    (clone/JSON-safe); `revertComponentRepair` restores bit-identical state.
  - `ComponentColorOverlay` — dev vertex-color overlay (repaired green,
    anomalies red, uncertain yellow, unchanged gray).
- Extraction strategy (Phase 4): the PREFERRED in-place method — corrected
  replacement values written into the original `BufferGeometry` attributes
  for proven components only. No mesh splitting, no re-indexing, no
  duplicate triangles possible (triangle count invariant tested).
- `odessaVerticalDomains.generated.ts` regenerated: verdict renamed
  `skip-mixed-domain` → `repair-components`; same 108/42 split. Consumed by
  `verticalRecovery.decide` (mesh-level skip) and by `scenePrep`, which runs
  `applySceneComponentRepair` right after vertical recovery.
- Dev modes (Phase 8), gated to the dev panel:
  - `COMP COLORS` — show repaired / unchanged / source-anomaly / uncertain
    components by color (per-component visibility inside one merged buffer
    is impossible without splitting geometry; color encoding covers the
    SHOW-x modes on actual rendered meshes).
  - `ORIGINAL GEOM` — ORIGINAL / REPAIRED A/B toggle (exact revert/reapply).
  - `SPIKES ONLY` / `HIDE SPIKES` / `SPIKES RED` (29.6/29.7) remain the
    needle-suspect modes.
  - ALT+click now prints component class, mesh repair tag, and for repaired
    components: component id, original/corrected bounds, scale factor XYZ,
    pivot, final world dimensions.
- Cost: repair runs once per flagged mesh (108 of 1,835) during the existing
  prep phase; dominated by union-find + weld over up to 860 k vertices for
  the two biggest heavy chunks. The full 45-file Node harness (parse + prep
  + verification decomposition) completes in ~24 s.

## NUMBERS (full production pipeline, real GLBs — `verticalRecovery.runtime.test.ts`)

```
MERGED MESHES CONTAINING MIXED COMPONENT DOMAINS:  108 (of 150 building-family meshes)
TOTAL COMPONENTS ANALYZED:                          459,801 (in repair meshes)
MINIATURE BUILDING COMPONENTS (SOURCE_ANOMALY):     197,710 — placement destroyed at export
CORRECTED COMPONENTS:                               130 (offline prediction: 130 — exact match)
GUARD ROLLBACKS (post-repair):                      0
NEEDLES BEFORE (whole-mesh recovery, simulated):    128,642
NEEDLES AFTER (component-level, measured):          0
RUNTIME MESH-LEVEL SPIKE SUSPECTS:                  0
MODIFIED VERTEX COUNT:                              36,662
UNMODIFIED VERTEX COUNT (repair meshes):            6,372,704 of 6,409,366
MAX WORLD HEIGHT:                                   23.96 m   P99: 14.0 m
WEB_height_95 / WEB_height_199:                     0.95 m / 1.99 m (SOURCE_ANOMALY — corrupted
                                                    footprints, stay flat by design)
```

## ARCHITECTURAL DECISIONS

1. **Miniatures are NOT scaled** (rejected: per-component XYZ ×100, per-
   cluster ×100, whole-mesh ×100) — placement forensics proves every variant
   produces mass overlap; the honest verdict is SOURCE_ANOMALY + re-export.
2. **Aspect guard tightened to 8 (from the nominal Phase 5 "< 10")** to
   coincide with the runtime needle classifier; the first forensics run
   showed 40 marginal 21 m towers on 2.2–2.5 m footprints in the 8–10 gap —
   they now stay unrepaired rather than risk needle appearance.
3. **In-place attribute rewrite over mesh splitting** — lower risk: index,
   UVs, groups, draw order untouched; bit-identical X/Z everywhere
   (only Y of proven components changes).
4. **Backups/labels in a WeakMap, not userData** — `Object3D.userData` is
   JSON-cloned by three.js `copy()`; typed arrays there would bloat or break
   clones.

## VALIDATION

- X/Z OF UNRELATED GEOMETRY PRESERVED: **YES** (bit-identical, tested)
- WATER/COAST PRESERVED: **YES** (repair touches only flagged building
  meshes; water/roads/labels never flagged — tested)
- Z-FIGHTING (29.4) PRESERVED: **YES** (polygonOffset layering untouched —
  tested)
- 29.7 RUNTIME SAFETY / IDEMPOTENCE PRESERVED: **YES** (298 enterprise-city
  tests green, incl. all 29.5/29.6/29.7 suites)
- TESTS: **PASS** — 19 new STEP 29.8 tests (`componentRepair.test.ts`)
  covering all 16 required regressions incl. welded decomposition,
  base-pivot scaling, bit-identity, UV/normal/index/group preservation,
  miniature SOURCE_ANOMALY, river/road untouched, guard rollback, duplicate-
  triangle invariant, final-world dimensions, zero needle components,
  idempotence + exact reversal, 29.4 decal layering, real-GLB-transform
  conjugation. Full enterprise-city suite: 298 passed / 1 skipped.
- BUILD: **PASS** (`vite build`); typecheck shows only pre-existing,
  unrelated errors (node typings in test files etc.).
- SAFARI VISUAL VALIDATION: **PENDING MANUAL RUN** — hard-refresh Safari
  (⌥⌘E then ⌘R, or restart the dev server / rebuild `dist`) so the new
  bundle is actually executed, then check: overview, low horizon, 45° orbit,
  top-down, center, port/coast, outer districts, previously needle-heavy
  areas. Expected: no needle forest (0 needle components measured), repaired
  buildings 2.5–24 m with real footprints, miniature districts remain flat
  (source data destroyed — cannot be restored at runtime).
- SAFE TO CALIBRATE: **YES from the rendering side** — geometry is stable,
  X/Z untouched, georeference code untouched. Note the residual product
  limitation below before investing in visual polish.

## RESIDUAL SOURCE LIMITATION (requires re-export, not runtime work)

197,710 of ~198k building components in the mixed meshes are miniatures with
destroyed placement. They stay invisible (≤ 0.25 m). Districts dominated by
them will look flat until the source pipeline (STEP 13 chunk merge / tile
export) is fixed to bake buildings at metric scale with true placement.
The 130 repaired + 104 whole-mesh-recovered buildings plus the already-
correct stock are the maximum honestly recoverable from the current GLBs.

STOP AFTER STEP 29.8 — STEP 30 not started, no calibration performed.
