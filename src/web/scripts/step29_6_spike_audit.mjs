/**
 * STEP 29.6 Phase 1/2 — spike root-cause inventory.
 *
 * Simulates the STEP 29.5 broad recovery rule offline over every mesh in all
 * Odessa GLBs and reports:
 *  - which meshes the rule recovered (pre/post world heights, footprints),
 *  - statistical buckets A–F (encoded / building-like / decal / flat classes /
 *    unknown / pathological spikes),
 *  - requiredFactor clusters for every WEB_height_N mesh (Phase 2),
 *  - the exact population of needle/spike geometry created by ×100.
 *
 * Usage: node scripts/step29_6_spike_audit.mjs
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const assetsDir = path.resolve(here, "../public/assets/odessa");

/* Same thresholds as runtime (renderDebugTools / verticalRecovery). */
const DECAL_MAX_HEIGHT = 0.02;
const DECAL_BAND_Y = 0.06;
const ALREADY_CORRECT_HEIGHT_M = 3;
const MAX_RECOVERED_HEIGHT_M = 500;
const FACTOR = 100;

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
function worldBox(m, min, max) {
  const lo = [Infinity, Infinity, Infinity];
  const hi = [-Infinity, -Infinity, -Infinity];
  for (const x of [min[0], max[0]])
    for (const y of [min[1], max[1]])
      for (const z of [min[2], max[2]]) {
        const w = [
          m[0] * x + m[4] * y + m[8] * z + m[12],
          m[1] * x + m[5] * y + m[9] * z + m[13],
          m[2] * x + m[6] * y + m[10] * z + m[14],
        ];
        for (let i = 0; i < 3; i++) {
          lo[i] = Math.min(lo[i], w[i]);
          hi[i] = Math.max(hi[i], w[i]);
        }
      }
  return { lo, hi };
}

function encodedHeight(name) {
  const m = name.match(/height_(\d+)(?:_(\d+))?/);
  if (!m) return null;
  const v = Number(m[2] != null && /^\d+$/.test(m[2]) ? `${m[1]}.${m[2]}` : m[1]);
  return Number.isFinite(v) && v > 0 ? v : null;
}

function classify(name) {
  const n = name.toLowerCase();
  if (encodedHeight(name) != null) return "A_ENCODED_HEIGHT";
  if (/(^|_)(build|building)/.test(n)) return "B_BUILDING_LIKE";
  if (/base/.test(n)) return "D_BASE";
  if (/water|sea|coast/.test(n)) return "D_WATER";
  if (/road|highway|rail|bridge|path|footway/.test(n)) return "D_ROAD";
  if (/name|label|text/.test(n)) return "D_LABEL";
  if (/landuse|natural|leisure|amenity|boundary|barrier|man_made|power|aeroway/.test(n)) return "D_OSM_LAYER";
  return "E_UNKNOWN";
}

const rows = [];
function walkFile(file, rel) {
  const g = readGlbJson(file);
  const nodes = g.nodes ?? [];
  const meshes = g.meshes ?? [];
  const acc = g.accessors ?? [];
  const mats = g.materials ?? [];
  const roots = g.scenes?.[g.scene ?? 0]?.nodes ?? [];

  function walk(idx, parentMat, chain) {
    const node = nodes[idx];
    if (!node) return;
    const local = node.matrix ? node.matrix.slice() : fromTRS(node.translation, node.rotation, node.scale);
    const world = mul(parentMat, local);
    const name = node.name || `node_${idx}`;
    if (node.mesh != null) {
      for (const prim of meshes[node.mesh].primitives ?? []) {
        const pos = acc[prim.attributes?.POSITION];
        if (!pos?.min || !pos?.max) continue;
        const wb = worldBox(world, pos.min, pos.max);
        const h = wb.hi[1] - wb.lo[1];
        const fx = wb.hi[0] - wb.lo[0];
        const fz = wb.hi[2] - wb.lo[2];
        const centerY = (wb.hi[1] + wb.lo[1]) / 2;
        rows.push({
          file: rel,
          name,
          chain: [...chain, name].join(" / "),
          material: mats[prim.material]?.name ?? `mat_${prim.material}`,
          rawSpan: [0, 1, 2].map((i) => +(pos.max[i] - pos.min[i]).toFixed(3)),
          nodeScale: node.scale ?? [1, 1, 1],
          preH: h,
          preMinY: wb.lo[1],
          centerY,
          footprint: [+fx.toFixed(2), +fz.toFixed(2)],
          maxFoot: Math.max(fx, fz),
          encoded: encodedHeight(name),
          cls: classify(name),
        });
      }
    }
    for (const c of node.children ?? []) walk(c, world, [...chain, name]);
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

/* ---- simulate STEP 29.5 eligibility ---- */
for (const r of rows) {
  const isDecal = r.preH <= DECAL_MAX_HEIGHT && Math.abs(r.centerY) <= DECAL_BAND_Y;
  const tooTall = r.preH > ALREADY_CORRECT_HEIGHT_M || r.preH * FACTOR > MAX_RECOVERED_HEIGHT_M;
  r.recovered29_5 = !isDecal && !tooTall;
  r.postH = r.recovered29_5 ? r.preH * FACTOR : r.preH;
  r.spikeRatio = r.postH / Math.max(r.maxFoot, 0.01);
  /* pathological: tall + thin, or absurd aspect */
  r.pathological =
    r.recovered29_5 &&
    ((r.postH > 60 && r.maxFoot < 6) || (r.postH > 25 && r.spikeRatio > 25));
}

console.log(`total meshes: ${rows.length}`);
const recovered = rows.filter((r) => r.recovered29_5);
console.log(`meshes recovered by 29.5 broad rule: ${recovered.length}`);

/* ---- Phase 1 buckets ---- */
console.log("\n=== BUCKETS (of 29.5-recovered meshes) ===");
const byCls = {};
for (const r of recovered) (byCls[r.cls] ??= []).push(r);
for (const [cls, list] of Object.entries(byCls).sort()) {
  const heights = list.map((r) => r.postH).sort((a, b) => a - b);
  const med = heights[Math.floor(heights.length / 2)];
  const spikes = list.filter((r) => r.pathological).length;
  console.log(
    `${cls.padEnd(18)} n=${String(list.length).padStart(4)}  medianPostH=${med.toFixed(1).padStart(7)} m  maxPostH=${heights[heights.length - 1].toFixed(1).padStart(7)} m  pathological=${spikes}`,
  );
}

/* ---- Phase 2: requiredFactor clusters for ALL encoded meshes ---- */
console.log("\n=== PHASE 2 — requiredFactor clusters (all WEB_height_N) ===");
const enc = rows.filter((r) => r.encoded != null && r.preH > 1e-4);
const clusters = { "~1": 0, "~10": 0, "~100": 0, other: [] };
for (const r of enc) {
  const f = r.encoded / r.preH;
  if (f > 0.8 && f < 1.25) clusters["~1"] += 1;
  else if (f > 8 && f < 12.5) clusters["~10"] += 1;
  else if (f > 80 && f < 125) clusters["~100"] += 1;
  else clusters.other.push({ name: r.name, file: r.file, preH: +r.preH.toFixed(4), factor: +f.toFixed(2) });
}
console.log(`encoded meshes with measurable height: ${enc.length}`);
console.log(`factor ~1:   ${clusters["~1"]}`);
console.log(`factor ~10:  ${clusters["~10"]}`);
console.log(`factor ~100: ${clusters["~100"]}`);
console.log(`other:       ${clusters.other.length}`);
for (const o of clusters.other) console.log(`  OTHER: ${o.name} preH=${o.preH} factor=${o.factor} (${o.file})`);
const flatEnc = rows.filter((r) => r.encoded != null && r.preH <= 1e-4);
console.log(`encoded but flat (h≈0, unmeasurable): ${flatEnc.length}`);

/* ---- Phase 1F: pathological spikes ---- */
console.log("\n=== BUCKET F — pathological spike geometry after 29.5 ===");
const spikes = rows.filter((r) => r.pathological).sort((a, b) => b.spikeRatio - a.spikeRatio);
console.log(`pathological meshes: ${spikes.length}`);
for (const r of spikes.slice(0, 40)) {
  console.log(
    `${r.name.padEnd(34)} cls=${r.cls.padEnd(16)} preH=${r.preH.toFixed(3).padStart(7)} postH=${r.postH.toFixed(1).padStart(7)} foot=${r.maxFoot.toFixed(2).padStart(8)} ratio=${r.spikeRatio.toFixed(0).padStart(6)} rawSpan=${r.rawSpan.join("x")} (${r.file})`,
  );
}

/* ---- distribution of recovered non-encoded meshes by pre-height ---- */
console.log("\n=== recovered NON-encoded meshes: pre-height distribution ===");
const nonEnc = recovered.filter((r) => r.encoded == null);
const bands = [
  [0.02, 0.05],
  [0.05, 0.1],
  [0.1, 0.3],
  [0.3, 0.6],
  [0.6, 1],
  [1, 2],
  [2, 3],
];
for (const [lo, hi] of bands) {
  const list = nonEnc.filter((r) => r.preH > lo && r.preH <= hi);
  const path_ = list.filter((r) => r.pathological).length;
  console.log(`preH ${String(lo).padStart(4)}–${String(hi).padEnd(4)} m → post ${lo * 100}–${hi * 100} m: n=${String(list.length).padStart(4)} pathological=${path_}`);
}

/* name prefix summary of pathological */
console.log("\n=== pathological by name prefix ===");
const prefixCount = {};
for (const r of spikes) {
  const p = r.name.replace(/[\d_]+$/, "").slice(0, 30);
  prefixCount[p] = (prefixCount[p] ?? 0) + 1;
}
for (const [p, n] of Object.entries(prefixCount).sort((a, b) => b[1] - a[1]).slice(0, 30)) console.log(`${p.padEnd(32)} ${n}`);

/* ---- Phase 6: simulate the STEP 29.6 SELECTIVE rule ---- */
console.log("\n=== PHASE 6 — SELECTIVE rule simulation ===");
const MIN_FOOT = 2;
const MAX_FACTOR = 150;
const MIN_FACTOR = 0.5;
function selectiveDecision(r) {
  const isDecal = r.preH <= DECAL_MAX_HEIGHT && Math.abs(r.centerY) <= DECAL_BAND_Y;
  if (isDecal) return { kind: "decal-band" };
  if (r.encoded != null) {
    if (r.preH < 1e-4) return { kind: "broken-encode" };
    const f = r.encoded / r.preH;
    if (Math.abs(f - 1) <= 0.05) return { kind: "already-correct" };
    if (f > MAX_FACTOR || f < MIN_FACTOR) return { kind: "broken-encode" };
    if (r.maxFoot < MIN_FOOT) return { kind: "needle-guard" };
    if (r.encoded > MAX_RECOVERED_HEIGHT_M) return { kind: "broken-encode" };
    return { kind: "apply", factor: f, reason: "encoded" };
  }
  const isBuilding = /(^|_)build/i.test(r.name) || /^HEAVY_BUILDING_CHUNK/i.test(r.name);
  if (isBuilding) {
    if (r.preH > ALREADY_CORRECT_HEIGHT_M) return { kind: "already-tall" };
    if (r.maxFoot < MIN_FOOT) return { kind: "needle-guard" };
    if (r.preH * FACTOR > MAX_RECOVERED_HEIGHT_M) return { kind: "already-tall" };
    return { kind: "apply", factor: FACTOR, reason: "building-family" };
  }
  return { kind: "no-evidence" };
}
const counts = {};
const applied = [];
for (const r of rows) {
  const d = selectiveDecision(r);
  counts[d.kind] = (counts[d.kind] ?? 0) + 1;
  if (d.kind === "apply") applied.push({ ...r, selFactor: d.factor, selPostH: r.preH * d.factor, reason: d.reason });
}
console.log("decision counts:", JSON.stringify(counts));
const fc = { "~1": 0, "~10": 0, "~100": 0, other: 0 };
for (const a of applied) {
  if (a.selFactor > 0.95 && a.selFactor < 1.05) fc["~1"] += 1;
  else if (a.selFactor > 8 && a.selFactor < 12.5) fc["~10"] += 1;
  else if (a.selFactor > 80 && a.selFactor < 125) fc["~100"] += 1;
  else fc.other += 1;
}
console.log("applied factor clusters:", JSON.stringify(fc));
const hs = applied.map((a) => a.selPostH).sort((a, b) => a - b);
const q = (p) => hs[Math.min(hs.length - 1, Math.floor(hs.length * p))];
console.log(
  `recovered=${applied.length} maxH=${hs[hs.length - 1]?.toFixed(1)} medianH=${q(0.5)?.toFixed(1)} P95=${q(0.95)?.toFixed(1)} P99=${q(0.99)?.toFixed(1)}`,
);
/* remaining spikes after selective rule? */
const remainingSpikes = applied.filter(
  (a) => (a.selPostH > 60 && a.maxFoot < 6) || (a.selPostH > 25 && a.selPostH / Math.max(a.maxFoot, 0.01) > 25),
);
console.log(`remaining pathological after selective: ${remainingSpikes.length}`);
for (const s of remainingSpikes) console.log("  REMAINING:", s.name, s.selPostH.toFixed(1), s.maxFoot.toFixed(2), s.file);
/* explicit low/medium/high samples */
console.log("\nencoded samples after selective (low ≤15 / med 15–40 / high >40):");
const encApplied = applied.filter((a) => a.reason === "encoded").sort((a, b) => a.encoded - b.encoded);
const low = encApplied.filter((a) => a.encoded <= 15).slice(0, 10);
const med = encApplied.filter((a) => a.encoded > 15 && a.encoded <= 40).slice(0, 10);
const high = encApplied.filter((a) => a.encoded > 40).slice(0, 10);
for (const list of [low, med, high]) {
  for (const a of list) {
    const err = (Math.abs(a.selPostH - a.encoded) / a.encoded) * 100;
    console.log(
      `  ${a.name.padEnd(20)} encoded=${String(a.encoded).padStart(5)} post=${a.selPostH.toFixed(2).padStart(8)} err=${err.toFixed(3)}%`,
    );
  }
}

fs.writeFileSync(path.resolve(here, "step29_6_inventory.json"), JSON.stringify(rows, null, 1));
console.log("\nwrote scripts/step29_6_inventory.json");
