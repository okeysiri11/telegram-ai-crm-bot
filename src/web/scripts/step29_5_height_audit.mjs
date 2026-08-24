/**
 * STEP 29.5 Phase 1/2 — vertical-scale defect proof.
 *
 * For every mesh whose name encodes a height (WEB_height_N) and for the two
 * reference meshes from STEP 29.4, prints the full transform chain (raw
 * geometry AABB, node scale, parent scales, world scale) and the
 * encoded-vs-rendered height ratio.
 *
 * Usage: node scripts/step29_5_height_audit.mjs
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const assetsDir = path.resolve(here, "../public/assets/odessa");

function readGlbJson(file) {
  const buf = fs.readFileSync(file);
  const jsonLen = buf.readUInt32LE(12);
  return JSON.parse(buf.subarray(20, 20 + jsonLen).toString("utf8"));
}

const I4 = () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
function mul(a, b) {
  const o = new Array(16).fill(0);
  for (let c = 0; c < 4; c++)
    for (let r = 0; r < 4; r++)
      for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return o;
}
function fromTRS(t = [0, 0, 0], q = [0, 0, 0, 1], s = [1, 1, 1]) {
  const [x, y, z, w] = q;
  const x2 = x + x, y2 = y + y, z2 = z + z;
  const xx = x * x2, xy = x * y2, xz = x * z2;
  const yy = y * y2, yz = y * z2, zz = z * z2;
  const wx = w * x2, wy = w * y2, wz = w * z2;
  return [
    (1 - (yy + zz)) * s[0], (xy + wz) * s[0], (xz - wy) * s[0], 0,
    (xy - wz) * s[1], (1 - (xx + zz)) * s[1], (yz + wx) * s[1], 0,
    (xz + wy) * s[2], (yz - wx) * s[2], (1 - (xx + yy)) * s[2], 0,
    t[0], t[1], t[2], 1,
  ];
}
function applyPoint(m, p) {
  return [
    m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
    m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
    m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14],
  ];
}
function worldSpanY(m, min, max) {
  let lo = Infinity, hi = -Infinity;
  for (const x of [min[0], max[0]])
    for (const y of [min[1], max[1]])
      for (const z of [min[2], max[2]]) {
        const wy = applyPoint(m, [x, y, z])[1];
        lo = Math.min(lo, wy);
        hi = Math.max(hi, wy);
      }
  return { lo, hi, h: hi - lo };
}

const rows = [];
function walkFile(file, rel) {
  const g = readGlbJson(file);
  const nodes = g.nodes ?? [];
  const meshes = g.meshes ?? [];
  const acc = g.accessors ?? [];
  const roots = g.scenes?.[g.scene ?? 0]?.nodes ?? [];

  function walk(idx, parentMat, chain) {
    const node = nodes[idx];
    if (!node) return;
    const local = node.matrix ? node.matrix.slice() : fromTRS(node.translation, node.rotation, node.scale);
    const world = mul(parentMat, local);
    const entry = {
      name: node.name || `node_${idx}`,
      scale: node.scale ?? [1, 1, 1],
      rotation: node.rotation ?? [0, 0, 0, 1],
      translation: node.translation ?? [0, 0, 0],
    };
    const nextChain = [...chain, entry];
    if (node.mesh != null) {
      for (const prim of meshes[node.mesh].primitives ?? []) {
        const pos = acc[prim.attributes?.POSITION];
        if (!pos?.min || !pos?.max) continue;
        const span = worldSpanY(world, pos.min, pos.max);
        rows.push({
          file: rel,
          name: entry.name,
          chain: nextChain,
          rawMin: pos.min,
          rawMax: pos.max,
          worldH: span.h,
          worldY0: span.lo,
          worldY1: span.hi,
        });
      }
    }
    for (const c of node.children ?? []) walk(c, world, nextChain);
  }
  for (const r of roots) walk(r, I4(), []);
}

(function scan(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) scan(p);
    else if (e.name.endsWith(".glb")) walkFile(p, path.relative(assetsDir, p));
  }
})(assetsDir);

/* --- Phase 1: full transform chain for the two reference meshes --- */
console.log("=== PHASE 1 — transform chains ===");
for (const ref of ["WEB_height_199", "WEB_height_95"]) {
  const r = rows.find((x) => x.name === ref);
  if (!r) {
    console.log(`${ref}: NOT FOUND`);
    continue;
  }
  const rawSpan = [0, 1, 2].map((i) => +(r.rawMax[i] - r.rawMin[i]).toFixed(3));
  console.log(`\n${ref} (${r.file})`);
  console.log(`  raw geometry AABB span (local x,y,z): ${rawSpan.join(" , ")}`);
  console.log(`  raw local min: ${r.rawMin.map((v) => +v.toFixed(2)).join(",")}  max: ${r.rawMax.map((v) => +v.toFixed(2)).join(",")}`);
  for (const [i, n] of r.chain.entries()) {
    console.log(
      `  node[${i}] ${n.name}: scale=${n.scale.map((v) => +v.toFixed(6)).join(",")} ` +
        `rot=${n.rotation.map((v) => +v.toFixed(4)).join(",")} t=${n.translation.map((v) => +v.toFixed(2)).join(",")}`,
    );
  }
  console.log(`  final world height: ${r.worldH.toFixed(4)} m  (y ${r.worldY0.toFixed(4)} → ${r.worldY1.toFixed(4)})`);
}

/* --- Phase 2: all height-encoded meshes --- */
console.log("\n=== PHASE 2 — WEB_height_N sample ===");
const heightRows = rows
  .filter((r) => /height_(\d+)/.test(r.name))
  .map((r) => {
    const encoded = Number(r.name.match(/height_(\d+)/)[1]);
    return { name: r.name, file: r.file, encoded, world: r.worldH, ratio: r.worldH / encoded };
  })
  .filter((r) => r.encoded > 0)
  .sort((a, b) => a.encoded - b.encoded);

for (const r of heightRows) {
  console.log(
    `${r.name.padEnd(20)} encoded=${String(r.encoded).padStart(4)} m  world=${r.world.toFixed(4).padStart(9)} m  ratio=${r.ratio.toFixed(5)}  (${r.file})`,
  );
}
const ratios = heightRows.map((r) => r.ratio).sort((a, b) => a - b);
const median = ratios.length ? ratios[Math.floor(ratios.length / 2)] : NaN;
console.log(`\nsamples=${heightRows.length} medianRatio=${median?.toFixed(6)} min=${ratios[0]?.toFixed(6)} max=${ratios[ratios.length - 1]?.toFixed(6)}`);
const bands = [
  [5, 15],
  [15, 30],
  [30, 60],
  [60, 100],
  [100, 10000],
];
for (const [lo, hi] of bands) {
  const n = heightRows.filter((r) => r.encoded >= lo && r.encoded < hi).length;
  console.log(`band ${lo}–${hi === 10000 ? "∞" : hi} m: ${n} samples`);
}
console.log(`\nVERTICAL_SCALE_DEFECT_CONFIRMED = ${ratios.length >= 5 && Math.abs(median - 0.01) < 0.002 ? "YES" : "CHECK"}`);

/* --- Phase 10: post-correction numerical validation (corrected = world × 100) --- */
console.log("\n=== PHASE 10 — corrected-height validation (×100, decal band excluded) ===");
const DECAL_MAX_HEIGHT = 0.02;
function trueEncoded(name) {
  /* WEB_height_2_5 → 2.5 ; WEB_height_3_m → 3 ; WEB_height_20_ → 20 */
  const m = name.match(/height_(\d+)(?:_(\d+))?/);
  if (!m) return NaN;
  return Number(m[2] != null ? `${m[1]}.${m[2]}` : m[1]);
}
const errors = [];
for (const r of rows.filter((x) => /height_\d/.test(x.name))) {
  const enc = trueEncoded(r.name);
  if (!enc) continue;
  if (r.worldH <= DECAL_MAX_HEIGHT) {
    console.log(`${r.name.padEnd(20)} SKIPPED (decal band, h=${r.worldH.toFixed(4)} m — recovery does not touch it)`);
    continue;
  }
  const corrected = r.worldH * 100;
  const errPct = (Math.abs(corrected - enc) / enc) * 100;
  errors.push(errPct);
  console.log(`${r.name.padEnd(20)} encoded=${enc.toString().padStart(6)} m  corrected=${corrected.toFixed(2).padStart(8)} m  error=${errPct.toFixed(3)}%`);
}
errors.sort((a, b) => a - b);
const medErr = errors[Math.floor(errors.length / 2)];
console.log(`\ncorrected samples=${errors.length}  MEDIAN ABS ERROR=${medErr.toFixed(3)}%  max=${errors[errors.length - 1].toFixed(3)}%`);
