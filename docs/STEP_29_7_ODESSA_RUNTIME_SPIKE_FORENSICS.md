# STEP 29.7 — ODESSA RUNTIME SPIKE FORENSICS + TRANSFORM-CHAIN CORRECTION

Status: COMPLETE (numerical/runtime harness acceptance green; Safari visual sign-off pending manual check — tooling provided).
Scope: forensic root cause of the runtime needle forest that survived STEP 29.6, evidence-based fix, permanent idempotence markers, DEV spike tooling, tests.
Constraints respected: no calibration, no georeference change, no global rescale, no clipping/culling of symptoms, no source GLB modified, STEP 29.4 depth-bias preserved, X/Z mathematically untouched.

---

## OFFLINE SPIKE COUNT (STEP 29.6 simulation)

**0** — the 29.6 offline simulation and the 29.6 per-mesh needle guard both reported zero pathological spike meshes. That claim was *correct at mesh level* and still wrong visually.

## RUNTIME SPIKE COUNT BEFORE (29.7 real-loader forensics, 29.6 code)

Measured by a new harness that reproduces the ACTUAL runtime end to end — real GLB bytes → real `THREE.GLTFLoader.parse` → real `prepareParsedScene` (recovery + decal layering + perf pass) → identity attach (verified: the production attach path adds no transforms) → `Box3` on final `matrixWorld`:

- Mesh-level runtime spike suspects (`h>15 ∧ (foot<2 ∨ ratio>8)`, plus `h>50∧foot<5`, near-zero footprint, degenerate scale): **0**
- **Sub-mesh ground-standing needle features inside recovered meshes: 128,642** (welded connected components; 452,488 before flat-shading vertex welding), concentrated in **105 of the 148 recovered meshes**.

That is the Safari needle forest. It is not a mesh — it is baked *inside* merged meshes.

## WHY 29.6 MISSED THEM

The mixed unit domain exists at **vertex level**, not only at mesh level. Merged building meshes (`HEAVY_BUILDING_CHUNK_*`, `WEB_build`, many `WEB_buildingNN`) bake thousands of individual buildings into one vertex buffer. A large share of those baked buildings were authored in the all-meters domain: **correct cm-domain placement across the tile, but 1/100-scale local geometry** (median 0.172 m tall × 0.154 m wide = intended ~17 m × 15 m buildings). Example: `HEAVY_BUILDING_CHUNK_01_02_SUB_00_01` = 53,589 welded components → 35,133 miniatures, only 23 real cm-domain buildings.

The mesh's aggregate AABB is therefore completely healthy (footprint = the placement spread, pre-height ≤ 3 m), so every per-mesh classifier — 29.6 offline *and* any runtime per-mesh box check — mathematically cannot see the defect. Scaling such a mesh ×100 vertically produces correct heights with 1/100 footprints: tens of thousands of 15–95 m needles standing on the ground.

`WEB_height_95` is the same anomaly in miniature: it is **not a building** — it is exactly two welded components, each **95 m tall × 0.12 m wide**, 30 m apart. Its "plausible" 23 m aggregate footprint is the spread between the two poles, which defeated the 29.6 needle guard.

## EXACT TRANSFORM STAGE CAUSING SPIKES

`applyWorldYScale` (the recovery conjugation) — applied exactly once, with mathematically correct results per mesh. The spike is introduced at that stage **only because the vertex data under it is per-component mixed-domain**; no transform-chain bug exists:

- RAW: miniature component 0.17 m tall / 0.15 m wide (inside a healthy-looking merged buffer)
- NODE (rot +90°X, uniform scale 0.01): unchanged proportions
- PARENT/TILE/ROOT: identity (verified in forensics rows: all parent scales `[1,1,1]`)
- RECOVERY ×100 (world-Y conjugation): 17 m tall / 0.15 m wide → **needle**
- FINAL matrixWorld: needle rendered

All Phase 4 hypotheses tested by the harness and unit tests: double recovery — no (userData guard, 0 duplicates); parent×100 + child×100 — no; matrix order error — no; StrictMode/remount/reload/LOD re-application — no (idempotence proven); pivot/mixed-axis errors — no; encoded height misread — no (`WEB_height_95` recovered to exactly 95.000 m world).

## WAS RECOVERY APPLIED MORE THAN ONCE

**NO.** Phase 5 markers (`userData.odessaVerticalRecovery = { version: 2, applied, factor, originalMatrix, sourceHeight, expectedHeight, reason }`) make double application impossible; tests cover remount, tile reload, LOD activation, strict-mode reapply. DUPLICATE RECOVERY COUNT: **0**.

## WERE PARENT SCALES INVOLVED

**NO** in the shipped scenes (all ancestor scales identity; mesh node scale uniform 0.01). Nevertheless the correction now derives the factor from the FINAL WORLD height and verifies it post-apply, so a scaled parent cannot break the invariant (test: parent Y×0.5 → factor 20 → final world 95 m).

## FIX (smallest correction at the responsible stage)

1. **Per-mesh vertex-domain table (generated from source evidence).**
   `scripts/step29_7_build_domain_table.mjs` parses every source GLB, welds flat-shading duplicate vertices, builds true connected components, and marks every mesh whose recovery would create ground-standing needle components (`h>15 m ∧ base<5 m ∧ (foot<2 m ∨ ratio>8)`; rooftop masts with high bases are legitimate and do not disqualify). Output: `src/web/src/enterprise-city/odessa3d/odessaVerticalDomains.generated.ts` (150 verdicts, deterministic, key `meshName|vertexCount`).
   `verticalRecovery.decide()` consults the table: **`skip-mixed-domain` meshes are left exactly as authored** (Phase 6: uncertain/unprovable → unchanged and listed) — 108 meshes, flagged `userData.odessaMixedDomain`, counted in diagnostics.
2. **FINAL-WORLD-height verification at the point of transform.** Every applied correction is re-measured after `updateWorldMatrix`; if the final world height misses the target (>1 % for encoded meshes) or the mesh classifies as a runtime spike (`classifyRuntimeSpike`), the correction is **reverted from the stored `originalMatrix`** and the mesh is flagged — a needle can no longer ship regardless of unforeseen runtime state.
3. **Phase 5 permanent markers + exact reversal** (`originalMatrix`), version 2.

No vertices rewritten, no source files touched, X/Z bit-exact (tests), WEB_base and 29.4 polygon-offset layering untouched.

## RUNTIME SPIKE COUNT AFTER

Re-run of the real-loader forensics over all 45 GLBs / 1,835 meshes (`ODESSA_RUNTIME_FORENSICS=1 npx vitest run verticalRecovery.runtime`):

- Mesh-level runtime spike suspects: **0**
- Ground-standing needle components inside recovered meshes: **0** (was 128,642)
- Recovered meshes: **42** (verified per-mesh against encoded/expected world heights)
- Mixed-domain meshes left as authored and listed: **108**

Report artifact: `src/web/scripts/step29_7_runtime_report.json` (full per-mesh rows).

## WEB_height_95 FINAL WORLD HEIGHT

**SOURCE_ANOMALY — left at authored 0.95 m; no needle created.** Component forensics proves the mesh is two 95 m × 0.12 m ground-standing poles with corrupt footprints (all-meters domain), not a 95 m building. Recovering it would create exactly the paper-thin 95 m towers the visual acceptance forbids. (The unit/harness fixtures verify that a *healthy* encoded 95 m building — plausible per-component footprint — recovers to 95.000 m final WORLD height within 1 %.)

## WEB_height_199 STATUS

**SOURCE_ANOMALY** (unchanged): all-meters domain, 0.66 m aggregate footprint; needle-guarded, stays at authored 1.99 m, flagged spike-suspect for the DEV tooling, no needle created.

## NUMERICAL ACCEPTANCE (Phase 8)

- RUNTIME SPIKE SUSPECTS BEFORE: 0 mesh-level / **128,642 sub-mesh needle features**
- RUNTIME SPIKE SUSPECTS AFTER: **0 / 0**
- MAX WORLD HEIGHT: **22.60 m** (`WEB_building91` — single welded component, 2.9 m footprint, aspect 7.7: a legitimate chimney-class structure)
- P95: **0.24 m** · P99: **10.47 m** (visible meshes; most of the city remains authored-flat — see honesty note)
- DUPLICATE RECOVERY COUNT: **0**

## DEV TOOLING (Phase 3)

Dev panel (`Odessa3DView`): `SPIKES ONLY`, **`HIDE SPIKES`**, **`SPIKES RED`** (flat-red override, restorable), **`EXPORT SPIKE JSON`** (downloads `collectRuntimeSpikeReport` over the ACTUAL rendered graph: uuid, parent chain, world box/dims, footprints, ratio, material, matrixWorld, determinant, object/parent scales, encoded height, recovery tag, classification). ALT+click now prints the full transform chain: raw geometry height, local bounds, object scale, every ancestor scale, matrixWorld, determinant, expected vs actual FINAL world height, and the exact recovery code path that touched (or skipped) the mesh. Diagnostics panel shows `mixed domain=N`.

## VISUAL SAFARI VALIDATION

**PENDING USER CONFIRMATION.** Every runtime-measurable criterion passes through the real-loader harness (0 needles at overview/any angle is a geometry fact, not a camera-dependent one). Checklist for the manual pass (dev server, hard-reload to drop stale bundles): overview / top-down / 45° / low horizon / center / port / outer districts → no needle forest, no paper-thin 100 m towers, no z-fighting stripes (29.4 fix intact), no gray-slab domination, water/coast intact. If any needle remains: `SPIKES RED` + ALT+click it and read `CODE PATH`, then `EXPORT SPIKE JSON`.

## HONESTY NOTE (city volume)

The 108 mixed-domain meshes contain most of the city's building stock; leaving them authored-flat is the only correct option that does not fabricate geometry (their footprints are 1/100 and X/Z are frozen). Full 3D volume for those districts requires a source re-export with consistent units — a source-data task, not a runtime transform task.

## TESTS

**PASS** — `verticalRecovery.test.ts` (19: selective rules, nested/scaled-parent world-height invariant, marker v2 + exact reversal, remount/reload/LOD/strict-mode idempotence, runtime classifier, mixed-domain table skip, post-check revert, spike report on rendered graph, X/Z exactness, 29.4 depth-bias) + gated real-GLB harness `verticalRecovery.runtime.test.ts`. Full enterprise-city suite: **279 passed, 1 skipped**. Lint (odessa3d scope): clean.

## BUILD

**PASS** — `npx vite build` (15.1 s).

## SAFE TO CALIBRATE

**YES** (after the Safari visual sign-off above): X/Z world coordinates are bit-exact through the whole 29.5→29.7 chain, georeference untouched, geometry stable under orbit, and recovery is idempotent across reload/remount/LOD.

## Architectural decisions

- **Generated per-mesh domain table over runtime component analysis**: welded union-find on 800 k-vertex chunks is too heavy for the load path; the verdicts depend only on source bytes, so they are precomputed deterministically (`step29_7_build_domain_table.mjs`) and bundled (~150 entries). Regenerate whenever the Odessa GLBs change.
- **Skip mixed-domain meshes rather than per-component vertex surgery**: rejected rewriting vertex buffers at runtime (violates the no-vertex-modification stance and risks flattening legitimate thin structures); per Phase 6, unprovable meshes stay unchanged and listed.
- **Post-apply FINAL-WORLD verification with revert**: the invariant is enforced where the transform is applied, so no future runtime state (parent scales, reload paths) can ship a needle silently.

STOP AFTER STEP 29.7. STEP 30 not started.
