# STEP 29.6 — Odessa Vertical-Spike Root Cause + Selective Height Recovery

Date: 2026-08-23
Scope: `src/web/src/enterprise-city/odessa3d/` only. No calibration. No STEP 30. No source GLB change. No camera hacks. No arbitrary visual multipliers. No global clamping.

---

## ROOT CAUSE OF SPIKES (exact evidence)

The offline inventory (`src/web/scripts/step29_6_spike_audit.mjs`, full data in
`scripts/step29_6_inventory.json`) simulated the STEP 29.5 broad rule over all
1,835 meshes in the 45 GLBs. It recovered 228 meshes; the spike population is
exactly identifiable:

**The source package contains TWO vertical-unit domains, and the STEP 29.5
rule ("everything outside the ground-decal band gets Y ×100") could not tell
them apart:**

1. **cm-horizontal / m-vertical domain (the majority, correctly ×100):**
   e.g. `WEB_height_95` raw 2330 × 2791 × 95 → 23.3 × 27.9 m footprint,
   0.95 m flattened height. Recovery ×100 is correct for these.
2. **all-meters domain (the spike makers):** these meshes are authored in
   meters on EVERY axis, so the exporter's uniform 0.01 scale shrinks them
   100× in all dimensions and their world footprint is sub-2 m. Examples:
   - `WEB_plane_1…35` (raw ≈ 32 × 33 × 9.2 m): 35 copies across tiles →
     each became a 9–14 m tall × 0.4 m wide needle after ×100.
   - 22 `WEB_building*` meshes with footprints 0.05–1.6 m (e.g.
     `WEB_building38` raw 4.95 × 5.2 × 30 → 5 cm footprint, 30 m spike).
   - 9 encoded towers, including `WEB_height_199` (footprint 0.37 m → a
     199 m hairline) and `WEB_height_75` (footprint 0.09 m → 75 m needle).
   - `WEB_rivers` (h = 0.021 m, 1 mm above the decal threshold) was extruded
     into a 2 m wall along every river — the visible "curtains".

Recovering only the vertical of an all-meters mesh **mathematically must**
produce a needle (X/Z are frozen and stay 100× too small). These meshes cannot
be fixed at runtime without touching X/Z, so they are excluded and reported.

## NUMBER OF MESHES INCORRECTLY ×100 SCALED (by STEP 29.5)

**78 of 228** recovered meshes had no valid evidence for ×100:
- 41 all-meters anomalies (needle guard: sub-2 m world footprint),
- 37 without any unit-domain evidence (35 `WEB_plane_*`, `WEB_rivers`,
  `WEB_power_subs`).

## UNIT/FACTOR CLUSTERS (Phase 2 — measured, not assumed)

`requiredFactor = encodedHeight / preRecoveryWorldHeight` for all 48
measurable `WEB_height_N` meshes:

| Cluster | Count |
| --- | --- |
| ~1 (already correct) | 0 |
| ~10 | 0 |
| ~100 | 47 |
| other | 1 (`WEB_height_2_1`: a flat polygon carrying a height name — broken encode, excluded) |

There are **no** already-correct and no ×10 encoded buildings in the package —
but the all-meters horizontal anomaly (invisible to a vertical-only factor
test) is what produced the spikes.

## SELECTIVE RECOVERY RULE (exact implementation)

`verticalRecovery.ts`, mode constant `ODESSA_VERTICAL_RECOVERY_MODE = "selective"`
(modes: `off` / `selective` / `legacy`, where legacy = the STEP 29.5 broad rule
kept only for dev A/B):

1. Ground-decal band (h ≤ 20 mm and |centerY| ≤ 60 mm) → never touched
   (STEP 29.4 GPU polygon-offset stack preserved).
2. **Encoded meshes** (`WEB_height_N`, decimal forms parsed):
   `factor = encodedHeight / measured pre-recovery world height` — the source
   data decides the factor. Skip if factor ≈ 1 (±5 %), skip if factor outside
   [0.5, 150] or encoded > 500 m (broken encode), **skip and flag as spike
   suspect if world footprint < 2 m** (all-meters anomaly — no real building
   has a sub-2 m footprint).
3. **Building-family meshes** (`WEB_build*`, `HEAVY_BUILDING_CHUNK*`): the
   proven pipeline factor ×100, only when flattened (h ≤ 3 m), footprint
   ≥ 2 m, and result ≤ 500 m.
4. **Everything else** (planes, rivers, roads, water, landuse, labels, base,
   unknown): NOT recovered — no objective evidence for the unit domain.
   Correctness over forcing every object into 3D.

Correction applied as before: world-space Y-only scale about the ground plane
y = 0 (the export's own scaling origin), conjugated into the mesh local matrix
(`local' = parentWorld⁻¹ · diag(1, factor, 1) · parentWorld · local`); no
vertex rewritten, idempotent, reversible.

### Selective result over the real package (offline simulation)

| Decision | Meshes |
| --- | --- |
| recovered (all factor ~100, measured per mesh) | 150 |
| decal band untouched | 1,607 |
| needle guard (all-meters anomalies, flagged) | 41 |
| no evidence, left unchanged | 37 |

Heights after recovery: **max 95.0 m, median 22.0 m, P95 59.4 m, P99 85.0 m.
Remaining pathological spike meshes: 0.**

## WEB_height_199 / WEB_height_95

| Mesh | Before | Expected | After | Note |
| --- | --- | --- | --- | --- |
| `WEB_height_199` | 1.99 m | 199 m | **1.99 m (excluded, spike suspect)** | Documented source anomaly: footprint 0.37 m (raw 37 × 36 × 199 all-meters). Recovery would create a 199 m × 0.37 m hairline spike; X/Z are frozen so it cannot be widened at runtime. Fixable only by source re-export. |
| `WEB_height_95` | 0.95 m | 95 m | **95.00 m (error 0.000 %)** | cm-domain footprint 23.3 × 27.9 m — recovered with measured factor 100. |

Encoded samples (10 low-rise ≤ 15 m, medium 15–40 m, high-rise > 40 m, all
that pass the guard): every one lands at **error 0.000 %** (see Phase 6 output
of the audit script). All recovered meshes satisfy
`abs(rendered − encoded)/encoded ≤ 1 %`.

## Phase 3 — dev-only spike tooling (not in production UI; the whole debug panel is dev-gated)

- **ALT/OPTION+click inspector** now additionally prints: mesh footprint, the
  vertical-recovery decision actually applied (factor, pre/post heights,
  reason) and the spike-suspect flag, alongside the existing GLB object/
  parent-chain/material/bounds output.
- **SPIKES ONLY** toggle: renders only meshes flagged as pathological
  (needle-guard suspects).
- **REC: SELECTIVE / LEGACY / OFF** three-way toggle: reverts and re-applies
  the chosen mode on the loaded city (original node TRS is never touched, so
  the comparison is exact), then refreshes bounds and clip planes.
- Diagnostics panel shows mode, corrected-mesh count, spike-suspect count and
  live city height.

## FINAL REPORT

| Field | Value |
| --- | --- |
| ROOT CAUSE OF SPIKES | STEP 29.5's broad band rule ×100-scaled 78 meshes from a second, all-meters unit domain (sub-2 m world footprints) plus near-band flat layers; vertical-only recovery of an all-meters mesh necessarily produces a needle |
| NUMBER OF MESHES INCORRECTLY ×100 SCALED | 78 (41 all-meters anomalies + 37 no-evidence) |
| UNIT/FACTOR CLUSTERS | ~1: 0 · ~10: 0 · ~100: 47 · other: 1 broken encode (see table above) |
| SELECTIVE RECOVERY RULE | Evidence-based (see exact implementation above); source data decides the factor per mesh |
| WEB_height_199 | 1.99 m → expected 199 m → excluded as documented all-meters source anomaly (footprint 0.37 m) |
| WEB_height_95 | 0.95 m → expected 95 m → **95.00 m** |
| MAX HEIGHT AFTER FIX | 95.0 m (median 22.0 m, P95 59.4 m, P99 85.0 m) |
| SPIKE GEOMETRY REMAINING | **NO** (0 pathological meshes in selective simulation; suspects stay at pre-recovery size) |
| X/Z UNCHANGED | **YES** (Y-row-only scale matrix; verified to numerical precision by test) |
| STEP 29.4 Z-FIGHTING FIX PRESERVED | **YES** (decal band untouched, GPU depth-bias only; tested) |
| TESTS | **PASS** — 271/271 enterprise-city (12 vertical-recovery tests covering all 10 required assertions + needle guard + tile seams) |
| BUILD | **PASS** (`vite build`) |
| SAFE FOR MANUAL SAFARI VALIDATION | **YES** |
| SAFE TO CALIBRATE | **NO** |

Phase 8 test coverage mapping: (1) encoded 199 m fixture with plausible
footprint renders ≈199 m; (2) encoded 95 m renders ≈95 m; (3) already-correct
building detected at factor ≈1 and untouched; (4) ×0.01 and partial ×0.1
buildings recovered by measured factor; (5) non-building meshes (plane, pier,
rivers) not recovered merely for being outside the band; (6) X/Z exact;
(7) base grounded; (8) decal separation stays GPU depth-bias; (9) idempotent;
(10) legacy mode toggleable and fully revertible without touching source GLBs.

STOP AFTER STEP 29.6. STEP 30 not started. GPS not calibrated.
