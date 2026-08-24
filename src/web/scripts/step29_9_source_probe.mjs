/**
 * STEP 29.9 Phase 1 — probe a pre-merge source model for the miniature
 * building defect. Works on GLB (GLTFLoader) or FBX (FBXLoader).
 *
 * Usage:
 *   node --max-old-space-size=12000 scripts/step29_9_source_probe.mjs <file> [nameFilter]
 *
 * Reports per building-capable mesh: node scale chain, raw + world bounds,
 * welded connected-component domain census (healthy / miniature / flat), and
 * miniature placement spacing — the same forensics used in STEP 29.8, so
 * results are directly comparable with the current 45-GLB package.
 */

import fs from "node:fs";
import path from "node:path";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const file = process.argv[2];
const nameFilter = process.argv[3] ? new RegExp(process.argv[3], "i") : null;
if (!file) throw new Error("usage: step29_9_source_probe.mjs <file.glb|file.fbx> [nameFilter]");

/* minimal DOM stubs so loaders don't crash on texture references in node */
globalThis.document ??= {
  createElementNS: () => ({ style: {}, addEventListener() {}, removeEventListener() {} }),
  createElement: () => ({ style: {}, getContext: () => null, addEventListener() {}, removeEventListener() {} }),
};
globalThis.self ??= globalThis;
globalThis.window ??= globalThis;
globalThis.URL.createObjectURL ??= () => "blob:stub";

async function load(fp) {
  const buf = fs.readFileSync(fp);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  if (fp.toLowerCase().endsWith(".glb") || fp.toLowerCase().endsWith(".gltf")) {
    return new Promise((res, rej) => new GLTFLoader().parse(ab, "", (g) => res(g.scene), rej));
  }
  const { FBXLoader } = await import("three/examples/jsm/loaders/FBXLoader.js");
  return new FBXLoader().parse(ab, "");
}

const median = (arr) => {
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)] ?? NaN;
};

function analyzeMesh(mesh) {
  const geo = mesh.geometry;
  const pos = geo?.getAttribute("position");
  if (!pos) return null;
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
  /* weld by raw position quantized relative to raw extent (unit-agnostic) */
  const weld = new Map();
  for (let i = 0; i < n; i++) {
    const key = `${Math.round(pos.getX(i) * 100)},${Math.round(pos.getY(i) * 100)},${Math.round(pos.getZ(i) * 100)}`;
    const first = weld.get(key);
    if (first === undefined) weld.set(key, i);
    else union(first, i);
  }
  const boxes = new Map();
  const v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    const r = find(i);
    let b = boxes.get(r);
    if (!b) { b = new THREE.Box3(); boxes.set(r, b); }
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.matrixWorld);
    b.expandByPoint(v);
  }
  let healthy = 0, mini = 0, flat = 0, other = 0;
  const minis = [];
  const healthyHeights = [];
  for (const b of boxes.values()) {
    const h = b.max.y - b.min.y;
    const foot = Math.max(b.max.x - b.min.x, b.max.z - b.min.z);
    if (h <= 0.02) flat += 1;
    else if (foot >= 2 && h > 2.5) { healthy += 1; healthyHeights.push(h); }
    else if (foot < 1.5 && h > 0.025 && h <= 3) { mini += 1; minis.push({ cx: (b.min.x + b.max.x) / 2, cz: (b.min.z + b.max.z) / 2, foot, h }); }
    else other += 1;
  }
  /* miniature spacing (sampled) */
  let nnMed = NaN;
  if (minis.length > 20) {
    const sample = minis.filter((_, i) => i % Math.max(1, Math.floor(minis.length / 300)) === 0);
    const nn = sample.map((c) => {
      let best = Infinity;
      for (const o of minis) {
        if (o === c) continue;
        const d = Math.hypot(o.cx - c.cx, o.cz - c.cz);
        if (d < best) best = d;
      }
      return best;
    });
    nnMed = median(nn);
  }
  return {
    components: boxes.size,
    healthy,
    mini,
    flat,
    other,
    healthyHMed: +median(healthyHeights).toFixed(2) || 0,
    miniFootMed: minis.length ? +median(minis.map((m) => m.foot)).toFixed(3) : 0,
    miniHMed: minis.length ? +median(minis.map((m) => m.h)).toFixed(3) : 0,
    miniNNMed: +nnMed.toFixed(2),
  };
}

const scene = await load(file);
scene.updateMatrixWorld(true);

const meshes = [];
scene.traverse((o) => o.isMesh && meshes.push(o));
console.log(`${path.basename(file)}: ${meshes.length} meshes`);

meshes.sort((a, b) => (b.geometry?.getAttribute("position")?.count ?? 0) - (a.geometry?.getAttribute("position")?.count ?? 0));

for (const mesh of meshes) {
  const pos = mesh.geometry?.getAttribute("position");
  if (!pos) continue;
  const interesting = nameFilter ? nameFilter.test(mesh.name) : /build|height/i.test(mesh.name);
  if (!interesting && pos.count < 200000) continue;
  mesh.updateWorldMatrix(true, false);
  const s = new THREE.Vector3();
  mesh.matrixWorld.decompose(new THREE.Vector3(), new THREE.Quaternion(), s);
  const wb = new THREE.Box3().setFromBufferAttribute(pos).applyMatrix4(mesh.matrixWorld);
  console.log(`\n=== ${mesh.name} · verts=${pos.count.toLocaleString()} · worldScale=(${s.x.toFixed(4)},${s.y.toFixed(4)},${s.z.toFixed(4)})`);
  console.log(`    world box: x[${wb.min.x.toFixed(1)},${wb.max.x.toFixed(1)}] y[${wb.min.y.toFixed(2)},${wb.max.y.toFixed(2)}] z[${wb.min.z.toFixed(1)},${wb.max.z.toFixed(1)}]`);
  if (pos.count > 3_000_000) {
    console.log("    (component analysis skipped: too many vertices)");
    continue;
  }
  const a = analyzeMesh(mesh);
  if (!a) continue;
  console.log(
    `    components=${a.components.toLocaleString()} healthy(foot≥2,h>2.5)=${a.healthy} ` +
      `mini(foot<1.5,h0.025-3)=${a.mini} flat=${a.flat} other=${a.other}`,
  );
  console.log(
    `    healthy h med=${a.healthyHMed} m · mini foot med=${a.miniFootMed} m · mini h med=${a.miniHMed} m · mini NN spacing med=${a.miniNNMed} m`,
  );
}
