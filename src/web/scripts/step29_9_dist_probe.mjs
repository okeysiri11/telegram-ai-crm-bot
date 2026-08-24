/**
 * STEP 29.9 — raw footprint/height/spacing distribution of one mesh's welded
 * components, in RAW units (no unit assumptions). Detects bimodal (mixed
 * cm/m) domains vs clean unimodal authoring.
 *
 * Usage: node --max-old-space-size=6500 scripts/step29_9_dist_probe.mjs <file> <exactMeshName>
 */

import fs from "node:fs";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

globalThis.document ??= {
  createElementNS: () => ({ style: {}, addEventListener() {}, removeEventListener() {} }),
  createElement: () => ({ style: {}, getContext: () => null, addEventListener() {}, removeEventListener() {} }),
};
globalThis.self ??= globalThis;
globalThis.window ??= globalThis;

const [file, meshName] = process.argv.slice(2);

async function load(fp) {
  const buf = fs.readFileSync(fp);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  if (fp.toLowerCase().endsWith(".glb")) {
    return new Promise((res, rej) => new GLTFLoader().parse(ab, "", (g) => res(g.scene), rej));
  }
  const { FBXLoader } = await import("three/examples/jsm/loaders/FBXLoader.js");
  return new FBXLoader().parse(ab, "");
}

const scene = await load(file);
scene.updateMatrixWorld(true);
let mesh = null;
scene.traverse((o) => {
  if (o.isMesh && (o.name === meshName || (!mesh && o.name.includes(meshName)))) mesh = mesh?.name === meshName ? mesh : o;
});
if (!mesh) throw new Error(`mesh not found: ${meshName}`);
const geo = mesh.geometry;
const pos = geo.getAttribute("position");
console.log(`${meshName}: verts=${pos.count.toLocaleString()}`);

const n = pos.count;
const parent = new Int32Array(n);
for (let i = 0; i < n; i++) parent[i] = i;
const find = (a) => {
  while (parent[a] !== a) {
    parent[a] = parent[parent[a]];
    a = parent[a];
  }
  return a;
};
const union = (a, b) => {
  const ra = find(a), rb = find(b);
  if (ra !== rb) parent[rb] = ra;
};
const index = geo.getIndex();
if (index) for (let i = 0; i < index.count; i += 3) { const a = index.getX(i); union(a, index.getX(i + 1)); union(a, index.getX(i + 2)); }
else for (let i = 0; i + 2 < n; i += 3) { union(i, i + 1); union(i, i + 2); }
const weld = new Map();
for (let i = 0; i < n; i++) {
  const key = `${Math.round(pos.getX(i) * 100)},${Math.round(pos.getY(i) * 100)},${Math.round(pos.getZ(i) * 100)}`;
  const first = weld.get(key);
  if (first === undefined) weld.set(key, i);
  else union(first, i);
}
/* RAW LOCAL boxes (no matrixWorld!) — pure authored units */
const boxes = new Map();
for (let i = 0; i < n; i++) {
  const r = find(i);
  let b = boxes.get(r);
  if (!b) { b = new THREE.Box3(); boxes.set(r, b); }
  b.expandByPoint(new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i)));
}
const comps = [...boxes.values()].map((b) => ({
  fx: b.max.x - b.min.x,
  fy: b.max.y - b.min.y,
  fz: b.max.z - b.min.z,
  cx: (b.min.x + b.max.x) / 2,
  cy: (b.min.y + b.max.y) / 2,
  cz: (b.min.z + b.max.z) / 2,
}));
const q = (arr, p) => {
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor(s.length * p))];
};
const axes = ["fx", "fy", "fz"];
console.log(`components=${comps.length}`);
for (const ax of axes) {
  const vals = comps.map((c) => c[ax]);
  console.log(
    `${ax} raw: p5=${q(vals, 0.05).toFixed(2)} p25=${q(vals, 0.25).toFixed(2)} med=${q(vals, 0.5).toFixed(2)} p75=${q(vals, 0.75).toFixed(2)} p95=${q(vals, 0.95).toFixed(2)} max=${q(vals, 1).toFixed(2)}`,
  );
}
/* footprint histogram (log buckets) to expose bimodality */
const foot = comps.map((c) => Math.max(c.fx, c.fz)).filter((f) => f > 0);
const buckets = new Map();
for (const f of foot) {
  const b = Math.floor(Math.log10(f) * 2) / 2; // half-decade buckets
  buckets.set(b, (buckets.get(b) ?? 0) + 1);
}
console.log("footprint(max of fx,fz) log10 half-decade histogram:");
for (const [b, c] of [...buckets.entries()].sort((a, z) => a[0] - z[0])) {
  console.log(`  10^${b.toFixed(1)}–10^${(b + 0.5).toFixed(1)} raw units: ${c}`);
}
/* nearest-neighbor centroid spacing, raw units (sampled) */
const sample = comps.filter((_, i) => i % Math.max(1, Math.floor(comps.length / 300)) === 0);
const nn = sample.map((c) => {
  let best = Infinity;
  for (const o of comps) {
    if (o === c) continue;
    const d = Math.hypot(o.cx - c.cx, o.cz - c.cz);
    if (d < best) best = d;
  }
  return best;
});
console.log(
  `NN spacing raw: p10=${q(nn, 0.1).toFixed(2)} med=${q(nn, 0.5).toFixed(2)} p90=${q(nn, 0.9).toFixed(2)}`,
);
/* mesh-level raw bounds */
geo.computeBoundingBox();
const bb = geo.boundingBox;
console.log(
  `mesh raw box: x[${bb.min.x.toFixed(1)},${bb.max.x.toFixed(1)}] y[${bb.min.y.toFixed(2)},${bb.max.y.toFixed(2)}] z[${bb.min.z.toFixed(1)},${bb.max.z.toFixed(1)}]`,
);
