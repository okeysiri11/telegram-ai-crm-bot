# STEP 30.5 — Alignment debug (top-down)

Companion to `STEP_30_5_ALIGNMENT_DEBUG.svg` and `STEP_30_5_MATCHES.json`.

This is an inspection overlay. It does **not** change city geometry, GLB, or STEP 29 repairs.

## Layers (SVG)

| Layer | Color | Meaning |
| --- | --- | --- |
| Model footprints | cyan / gray / blue | X/Z AABB from `odessa_metric` GLB accessors. City-wide batches are drawn faint. |
| OSM buildings | gray dots | Downtown Overpass buildings, preview-mapped with identity ENU (E=+X, N=−Z, scale=1). **Not a production lock.** |
| Accepted matches | green | Unique constellation correspondences (none on live Odessa). |
| Rejected matches | red | Size candidates that failed uniqueness or constellation. |
| Residual vectors | orange | Model world → predicted world from GPS (only after a solve). |
| Historical CHECK | magenta ring | Operator STEP 30.1 CHECK at (−1935.01, 20.66, 15514.82). Never in the solver. |

## Screenshot automation

No reliable Three.js top-down capture was available in this environment. The SVG is the automated top-down dataset.

## Live Odessa reading

The model is a set of **batched OSM class meshes**, not individual buildings. Most “buildings” span tens of kilometers. OSM downtown is a few kilometers of real footprints. Overlaying them under an identity ENU preview is for inspection only — it is not evidence of alignment.
