/**
 * STEP 29.8 — what ARE the miniature components?
 * Measures per-component vertex/triangle complexity, footprint aspect,
 * layout linearity (fence-like bands vs building blocks), and compares
 * against the healthy (cm-domain) components in the same meshes.
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
      "TILE_05_02.glb",
    ];

function parseGlb(file) {
  const buf = fs.readFileSync(file);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  return new Promise((resolve, reject) => new GLTFLoader().parse(ab, "", (g) => resolve(g.scene), reject));
}

const median = (arr) => {
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)] ?? NaN;
};

for (const rel of targets) {
  const scene = await parseGlb(path.resolve(assetsDir, rel));
  scene.updateMatrixWorld(true);
  scene.traverse((mesh) => {
    if (!mesh.isMesh) return;
    if (!/build|height/i.test(mesh.name)) return;
    const geo = mesh.geometry;
    const pos = geo.getAttribute("position");
    const n = pos.count;
    if (n < 1000 && !/height/i.test(mesh.name)) return;
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
    const data = new Map(); // root -> {box, verts}
    const v = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      const r = find(i);
      let d = data.get(r);
      if (!d) { d = { box: new THREE.Box3(), verts: 0 }; data.set(r, d); }
      v.fromBufferAttribute(pos, i).applyMatrix4(mesh.matrixWorld);
      d.box.expandByPoint(v);
      d.verts += 1;
    }
    const minis = [];
    const healthy = [];
    for (const d of data.values()) {
      const b = d.box;
      const h = b.max.y - b.min.y;
      const fx = b.max.x - b.min.x, fz = b.max.z - b.min.z;
      const foot = Math.max(fx, fz), footMin = Math.min(fx, fz);
      const row = { h, foot, footMin, aspect: foot / Math.max(footMin, 1e-6), verts: d.verts, cx: (b.min.x + b.max.x) / 2, cz: (b.min.z + b.max.z) / 2 };
      if (h > 0.025 && h <= 3 && foot < 1.5) minis.push(row);
      else if (h > 0.02 && foot >= 2) healthy.push(row);
    }
    if (minis.length < 5) return;
    console.log(`\n${rel} :: ${mesh.name} — minis=${minis.length} healthy=${healthy.length}`);
    console.log(`  MINI  verts: med=${median(minis.map((c) => c.verts))} p90=${[...minis.map((c) => c.verts)].sort((a, b) => a - b)[Math.floor(minis.length * 0.9)]}  ` +
      `foot med=${median(minis.map((c) => c.foot)).toFixed(3)}  footMin med=${median(minis.map((c) => c.footMin)).toFixed(3)}  aspect med=${median(minis.map((c) => c.aspect)).toFixed(2)}`);
    if (healthy.length) {
      console.log(`  HEALTHY verts: med=${median(healthy.map((c) => c.verts))}  foot med=${median(healthy.map((c) => c.foot)).toFixed(1)}  aspect med=${median(healthy.map((c) => c.aspect)).toFixed(2)}`);
    }
    /* linearity probe: fit direction dispersion in local neighborhoods —
     * fences form 1D chains: for each mini, angle between vectors to two
     * nearest neighbors ≈ 180°. Sample 400. */
    const sample = minis.filter((_, i) => i % Math.max(1, Math.floor(minis.length / 400)) === 0);
    let chainish = 0;
    for (const c of sample) {
      let d1 = Infinity, d2 = Infinity, n1 = null, n2 = null;
      for (const o of minis) {
        if (o === c) continue;
        const d = Math.hypot(o.cx - c.cx, o.cz - c.cz);
        if (d < d1) { d2 = d1; n2 = n1; d1 = d; n1 = o; }
        else if (d < d2) { d2 = d; n2 = o; }
      }
      if (!n1 || !n2 || d2 > 3) continue;
      const a1 = Math.atan2(n1.cz - c.cz, n1.cx - c.cx);
      const a2 = Math.atan2(n2.cz - c.cz, n2.cx - c.cx);
      let da = Math.abs(a1 - a2) % (2 * Math.PI);
      if (da > Math.PI) da = 2 * Math.PI - da;
      if (da > (150 * Math.PI) / 180) chainish += 1;
    }
    console.log(`  layout: ${chainish}/${sample.length} sampled minis have collinear (chain-like) nearest neighbors`);
  });
  scene.traverse((o) => o.isMesh && o.geometry?.dispose());
}
