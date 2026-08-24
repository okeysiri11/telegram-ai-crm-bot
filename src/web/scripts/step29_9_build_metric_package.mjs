/**
 * STEP 29.9 — build the REBUILT_METRIC Odessa package.
 *
 * Root cause (see docs/STEP_29_9_SOURCE_PIPELINE_FORENSICS.md): the vendor
 * FBX (Odessa.fbx, TurboCG 2022) authors every coordinate in METERS but its
 * header declares CENTIMETERS (UnitScaleFactor=1). Blender honored the
 * header, so every imported object carries scale 0.01 and the whole city —
 * buildings, roads, placement, heights — is uniformly 1/100 in world space.
 * The geometry itself survived the entire STEP 06–14 export pipeline
 * bit-identical (proven by welded-component distribution equality between
 * Odessa.fbx, Odessa_MASTER.glb and the runtime tiles).
 *
 * The rebuild is therefore a pure unit-interpretation fix, applied per node:
 *
 *     world  = T + R · (0.01 · v)          (broken: 1 unit = 100 m)
 *     world' = 100·T + R · v = 100 · world (metric: 1 unit = 1 m)
 *
 * i.e. translation ×100, scale → 1. Geometry buffers are copied byte-for-byte
 * (accessor min/max stay valid because vertex data is untouched). All 1,833
 * nodes across the 45 GLBs are flat scene roots with uniform ~0.01 scale and
 * no matrices (verified by scripts/step29_9_node_census.mjs), so this
 * transform is exact, deterministic and reversible.
 *
 * Output: src/web/public/assets/odessa_metric/** + odessa_manifest.json with
 * bounds ×100, urls under /assets/odessa_metric/, packageFormat
 * "blender_web_v1_metric".
 *
 * Usage: node scripts/step29_9_build_metric_package.mjs
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const srcDir = path.resolve(here, "../public/assets/odessa");
const outDir = path.resolve(here, "../public/assets/odessa_metric");
const SCALE = 100;

function listGlbs(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...listGlbs(p));
    else if (e.name.endsWith(".glb")) out.push(p);
  }
  return out.sort();
}

function patchGlb(srcFile, outFile) {
  const buf = fs.readFileSync(srcFile);
  if (buf.readUInt32LE(0) !== 0x46546c67) throw new Error("not glb: " + srcFile);
  const totalLen = buf.readUInt32LE(8);
  const jsonLen = buf.readUInt32LE(12);
  if (buf.readUInt32LE(16) !== 0x4e4f534a) throw new Error("no JSON chunk: " + srcFile);
  const json = JSON.parse(buf.subarray(20, 20 + jsonLen).toString("utf8"));
  const rest = buf.subarray(20 + jsonLen, totalLen); // BIN chunk(s), byte-identical

  let patched = 0;
  for (const node of json.nodes ?? []) {
    if (node.matrix) throw new Error(`unexpected matrix node in ${srcFile}: ${node.name}`);
    if (node.children?.length) throw new Error(`unexpected nested node in ${srcFile}: ${node.name}`);
    if (node.scale) {
      const s = node.scale;
      if (s.some((v) => Math.abs(v - 0.01) > 1e-6)) {
        throw new Error(`unexpected scale in ${srcFile}: ${node.name} [${s}]`);
      }
      /* preserve the exact authored ratio (some scales are 0.00999999884…) */
      node.scale = s.map((v) => v * SCALE);
      if (node.scale.every((v) => Math.abs(v - 1) < 1e-5)) delete node.scale;
      patched += 1;
    }
    if (node.translation) {
      node.translation = node.translation.map((v) => v * SCALE);
    }
  }
  json.asset ??= {};
  json.asset.extras = {
    ...(json.asset.extras ?? {}),
    odessaMetricRebuild: {
      step: "29.9",
      unit: "meter",
      appliedWorldScale: SCALE,
      source: path.basename(srcFile),
    },
  };

  let jsonOut = Buffer.from(JSON.stringify(json), "utf8");
  const pad = (4 - (jsonOut.length % 4)) % 4;
  if (pad) jsonOut = Buffer.concat([jsonOut, Buffer.alloc(pad, 0x20)]);

  const header = Buffer.alloc(12);
  header.writeUInt32LE(0x46546c67, 0);
  header.writeUInt32LE(2, 4);
  header.writeUInt32LE(12 + 8 + jsonOut.length + rest.length, 8);
  const jsonHeader = Buffer.alloc(8);
  jsonHeader.writeUInt32LE(jsonOut.length, 0);
  jsonHeader.writeUInt32LE(0x4e4f534a, 4);

  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, Buffer.concat([header, jsonHeader, jsonOut, rest]));
  return patched;
}

const glbs = listGlbs(srcDir);
if (glbs.length !== 45) throw new Error(`expected 45 GLBs, found ${glbs.length}`);

let totalPatched = 0;
for (const file of glbs) {
  const rel = path.relative(srcDir, file);
  totalPatched += patchGlb(file, path.join(outDir, rel));
  console.log(`patched ${rel}`);
}

/* ---- manifest: bounds ×100, urls to /assets/odessa_metric, metric format ---- */
const manifest = JSON.parse(fs.readFileSync(path.join(srcDir, "odessa_manifest.json"), "utf8"));
manifest.packageFormat = "blender_web_v1_metric";
manifest.name = (manifest.name ?? "odessa") + " (metric rebuild STEP 29.9)";
manifest.notes = [
  ...(Array.isArray(manifest.notes) ? manifest.notes : manifest.notes ? [manifest.notes] : []),
  "STEP 29.9: unit-interpretation rebuild. Vendor FBX declares cm but authors meters;" +
    " node scale 0.01 removed, translations x100. 1 world unit = 1 meter. Geometry buffers byte-identical to the Blender export.",
];
if (manifest.cityBounds) {
  for (const k of Object.keys(manifest.cityBounds)) manifest.cityBounds[k] *= SCALE;
}
for (const asset of manifest.assets ?? []) {
  if (asset.bounds) for (const k of Object.keys(asset.bounds)) asset.bounds[k] *= SCALE;
  if (typeof asset.url === "string") asset.url = asset.url.replace("/assets/odessa/", "/assets/odessa_metric/");
}
fs.writeFileSync(path.join(outDir, "odessa_manifest.json"), JSON.stringify(manifest, null, 1));

console.log(`\nREBUILT_METRIC complete: ${glbs.length} GLBs, ${totalPatched} nodes unit-corrected -> ${outDir}`);
