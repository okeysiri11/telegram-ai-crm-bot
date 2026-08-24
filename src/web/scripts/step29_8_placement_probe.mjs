/**
 * STEP 29.8 — placement-domain forensics for miniature building components.
 *
 * Decides the correct repair pivot semantics: if miniature components are
 * placed at real city coordinates (nearest-neighbor spacing ~10s of meters),
 * per-component ×100 scaling about each component's own pivot reconstructs
 * the district. If placements are compressed too, in-place scaling would
 * overlap everything and the repair must anchor differently.
 *
 * Usage: node scripts/step29_8_placement_probe.mjs [glbRelPath ...]
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const assetsDir = path.resolve(here, "../public/assets/odessa");
const targets = process.argv.slice(2).length
  ? process.argv.slice(2)
  : [
      "HEAVY_BUILDING_CHUNKS_STEP13/HEAVY_BUILDING_CHUNK_01_02_SUB_00_01.glb",
      "FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_01.glb",
      "TILE_03_01.glb",
      "TILE_05_02.glb",
    ];

function parseGlb(file) {
  const buf = fs.readFileSync(file);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  return new Promise((resolve, reject) => new GLTFLoader().parse(ab, "", (g) => resolve(g.scene), reject));
}

function components(mesh) {
  const geo = mesh.geometry;
  const pos = geo.getAttribute("position");
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
    const key = `${Math.round(pos.getX(i) * 1000)},${Math.round(pos.getY(i) * 1000)},${Math.round(pos.getZ(i) * 1000)}`;
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
  return [...boxes.values()];
}

for (const rel of targets) {
  const scene = await parseGlb(path.resolve(assetsDir, rel));
  scene.updateMatrixWorld(true);
  scene.traverse((mesh) => {
    if (!mesh.isMesh) return;
    const comps = components(mesh);
    /* miniature building components: implausible footprint, mini height */
    const minis = comps
      .map((b) => ({
        cx: (b.min.x + b.max.x) / 2,
        cz: (b.min.z + b.max.z) / 2,
        h: b.max.y - b.min.y,
        foot: Math.max(b.max.x - b.min.x, b.max.z - b.min.z),
        baseY: b.min.y,
      }))
      .filter((c) => c.h > 0.025 && c.h <= 3 && c.foot > 0.01 && c.foot < 1.5);
    if (minis.length < 5) return;

    /* nearest-neighbor centroid distance via spatial hash grid (cell 4 m) */
    const cell = 4;
    const grid = new Map();
    minis.forEach((c, i) => {
      const k = `${Math.floor(c.cx / cell)},${Math.floor(c.cz / cell)}`;
      (grid.get(k) ?? grid.set(k, []).get(k)).push(i);
    });
    const nn = [];
    for (let i = 0; i < minis.length; i++) {
      const c = minis[i];
      let best = Infinity;
      const gx = Math.floor(c.cx / cell), gz = Math.floor(c.cz / cell);
      for (let r = 0; r <= 64; r++) { /* expand rings until a guaranteed nearest */
        for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) {
          if (Math.max(Math.abs(dx), Math.abs(dz)) !== r) continue;
          const list = grid.get(`${gx + dx},${gz + dz}`);
          if (!list) continue;
          for (const j of list) {
            if (j === i) continue;
            const d = Math.hypot(minis[j].cx - c.cx, minis[j].cz - c.cz);
            if (d < best) best = d;
          }
        }
        if (best < r * cell) break; /* ring guarantees no closer point outside */
      }
      if (best < Infinity) nn.push(best);
    }
    nn.sort((a, b) => a - b);
    const q = (p) => nn[Math.floor(nn.length * p)] ?? NaN;

    const spread = new THREE.Box3();
    for (const c of minis) spread.expandByPoint(new THREE.Vector3(c.cx, 0, c.cz));
    const areaM2 = Math.max(0.01, (spread.max.x - spread.min.x) * (spread.max.z - spread.min.z));

    console.log(`\n${rel} :: ${mesh.name}`);
    console.log(`  miniature components: ${minis.length}`);
    console.log(`  centroid NN distance: med=${q(0.5).toFixed(2)} m  p10=${q(0.1).toFixed(2)}  p90=${q(0.9).toFixed(2)}`);
    console.log(`  spread: ${(spread.max.x - spread.min.x).toFixed(0)} × ${(spread.max.z - spread.min.z).toFixed(0)} m → density ${(areaM2 / minis.length).toFixed(1)} m²/component`);
    console.log(`  mini foot: med=${median(minis.map((c) => c.foot)).toFixed(3)} m · mini h: med=${median(minis.map((c) => c.h)).toFixed(3)} m · baseY med=${median(minis.map((c) => c.baseY)).toFixed(4)}`);
    /* verdict hint: after ×100 the footprint becomes foot×100. If NN spacing
     * is already ≥ that, in-place scaling cannot systematically overlap. */
    const med = q(0.5), footAfter = median(minis.map((c) => c.foot)) * 100;
    console.log(`  → footprint after ×100: ${footAfter.toFixed(1)} m vs NN spacing ${med.toFixed(1)} m → ${med >= footAfter * 0.7 ? "REAL-WORLD PLACEMENT (per-component repair viable)" : "COMPRESSED PLACEMENT (in-place ×100 would overlap)"}`);
  });
  scene.traverse((o) => o.isMesh && o.geometry?.dispose());
}

function median(arr) {
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)] ?? NaN;
}
