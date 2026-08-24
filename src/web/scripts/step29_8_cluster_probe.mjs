/**
 * STEP 29.8 — cluster-structure probe.
 * If miniature components form compact separated clusters (compressed city
 * blocks placed at true block positions), per-cluster ×100 expansion about
 * the cluster centroid can reconstruct the district. If they form one
 * contiguous mass, the placement domain was destroyed at export.
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
    ];
const LINK = Number(process.env.LINK ?? 1.0); // meters, cluster link distance

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
    const geo = mesh.geometry;
    const pos = geo.getAttribute("position");
    const n = pos.count;
    if (n < 10000) return;
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
    const minis = [];
    for (const b of boxes.values()) {
      const h = b.max.y - b.min.y;
      const foot = Math.max(b.max.x - b.min.x, b.max.z - b.min.z);
      if (h > 0.025 && h <= 3 && foot < 1.5) {
        minis.push({ cx: (b.min.x + b.max.x) / 2, cz: (b.min.z + b.max.z) / 2 });
      }
    }
    if (minis.length < 100) return;

    /* grid-linked clustering (link distance LINK meters) */
    const cell = LINK;
    const grid = new Map();
    minis.forEach((c, i) => {
      const k = `${Math.floor(c.cx / cell)},${Math.floor(c.cz / cell)}`;
      if (!grid.has(k)) grid.set(k, []);
      grid.get(k).push(i);
    });
    const cparent = new Int32Array(minis.length);
    for (let i = 0; i < minis.length; i++) cparent[i] = i;
    const cfind = (a) => {
      while (cparent[a] !== a) {
        cparent[a] = cparent[cparent[a]];
        a = cparent[a];
      }
      return a;
    };
    const cunion = (a, b) => {
      const ra = cfind(a), rb = cfind(b);
      if (ra !== rb) cparent[rb] = ra;
    };
    for (const [k, list] of grid) {
      const [gx, gz] = k.split(",").map(Number);
      for (let dx = 0; dx <= 1; dx++) for (let dz = -1; dz <= 1; dz++) {
        if (dx === 0 && dz < 1) continue;
        const other = grid.get(`${gx + dx},${gz + dz}`);
        if (!other) continue;
        for (const i of list) for (const j of other) {
          if (Math.hypot(minis[j].cx - minis[i].cx, minis[j].cz - minis[i].cz) <= LINK) cunion(i, j);
        }
      }
      for (let a = 0; a < list.length; a++) for (let b = a + 1; b < list.length; b++) cunion(list[a], list[b]);
    }
    const clusters = new Map();
    minis.forEach((c, i) => {
      const r = cfind(i);
      if (!clusters.has(r)) clusters.set(r, { n: 0, box: new THREE.Box3() });
      const cl = clusters.get(r);
      cl.n += 1;
      cl.box.expandByPoint(new THREE.Vector3(c.cx, 0, c.cz));
    });
    const rows = [...clusters.values()].sort((a, b) => b.n - a.n);
    const sizes = rows.map((r) => r.n);
    const diams = rows.map((r) => Math.max(r.box.max.x - r.box.min.x, r.box.max.z - r.box.min.z));
    console.log(`\n${rel} :: ${mesh.name} — minis=${minis.length} link=${LINK} m`);
    console.log(`  clusters: ${rows.length}`);
    console.log(`  sizes: max=${sizes[0]} top5=[${sizes.slice(0, 5).join(", ")}] med=${median(sizes)}`);
    console.log(`  in-top-cluster share: ${(sizes[0] / minis.length * 100).toFixed(1)} %`);
    console.log(`  cluster diameters: top5=[${diams.slice(0, 5).map((d) => d.toFixed(1)).join(", ")}] med=${median(diams).toFixed(2)} m`);
    /* would per-cluster ×100 fit? diameter×100 must not exceed ~300 m and
     * clusters must be sparse relative to that */
    const centers = rows.filter((r) => r.n >= 3).map((r) => ({ x: (r.box.min.x + r.box.max.x) / 2, z: (r.box.min.z + r.box.max.z) / 2 }));
    let nn = [];
    for (let i = 0; i < Math.min(centers.length, 400); i++) {
      let best = Infinity;
      for (let j = 0; j < centers.length; j++) {
        if (i === j) continue;
        const d = Math.hypot(centers[j].x - centers[i].x, centers[j].z - centers[i].z);
        if (d < best) best = d;
      }
      nn.push(best);
    }
    console.log(`  cluster-center NN spacing: med=${median(nn).toFixed(1)} m (clusters with ≥3 minis: ${centers.length})`);
  });
  scene.traverse((o) => o.isMesh && o.geometry?.dispose());
}
