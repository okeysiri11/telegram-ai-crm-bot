/**
 * STEP 29.7 — deep probe of one merged building chunk.
 * Parses the real GLB, welds vertices by position, builds connected
 * components, and characterizes needle vs healthy features BEFORE any
 * recovery (source truth) to prove the vertex-level mixed unit domain.
 *
 * Usage: node scripts/step29_7_chunk_probe.mjs [glbRelPath]
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const rel = process.argv[2] ?? "HEAVY_BUILDING_CHUNKS_STEP13/HEAVY_BUILDING_CHUNK_01_02_SUB_00_01.glb";
const file = path.resolve(here, "../public/assets/odessa", rel);

const buf = fs.readFileSync(file);
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);

new GLTFLoader().parse(ab, "", (gltf) => {
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse((o) => {
    if (!o.isMesh) return;
    const geo = o.geometry;
    const pos = geo.getAttribute("position");
    const index = geo.getIndex();
    console.log(`mesh=${o.name} verts=${pos.count} indexed=${!!index} tris=${(index ? index.count : pos.count) / 3}`);

    /* union-find with position welding (1 mm quantization in raw space) */
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
    if (index) for (let i = 0; i < index.count; i += 3) { const a = index.getX(i); union(a, index.getX(i + 1)); union(a, index.getX(i + 2)); }
    else for (let i = 0; i + 2 < n; i += 3) { union(i, i + 1); union(i, i + 2); }
    const weld = new Map();
    for (let i = 0; i < n; i++) {
      const key = `${Math.round(pos.getX(i) * 1000)},${Math.round(pos.getY(i) * 1000)},${Math.round(pos.getZ(i) * 1000)}`;
      const first = weld.get(key);
      if (first === undefined) weld.set(key, i);
      else union(first, i);
    }

    /* per-component world boxes */
    const boxes = new Map();
    const v = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      const r = find(i);
      let b = boxes.get(r);
      if (!b) { b = new THREE.Box3(); boxes.set(r, b); }
      v.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld);
      b.expandByPoint(v);
    }
    const comps = [...boxes.values()];
    console.log(`welded components: ${comps.length}`);

    /* classify at SOURCE scale (pre-recovery): a needle-after-×100 component
     * has pre h in (0.15, 5] m and footprint < 1.5 m; a cm-domain building
     * has pre h ≤ 3 m with footprint ≥ 2 m. */
    let needleLike = 0, healthy = 0, flat = 0, other = 0;
    const needleSpread = new THREE.Box3();
    let preHs = [], preFoots = [];
    for (const b of comps) {
      const h = b.max.y - b.min.y;
      const foot = Math.max(b.max.x - b.min.x, b.max.z - b.min.z);
      if (h < 0.01) { flat += 1; continue; }
      if (h > 0.12 && foot < 1.5) {
        needleLike += 1;
        needleSpread.union(b);
        if (preHs.length < 100000) { preHs.push(h); preFoots.push(foot); }
      } else if (foot >= 2) healthy += 1;
      else other += 1;
    }
    preHs.sort((a, b) => a - b);
    preFoots.sort((a, b) => a - b);
    const q = (arr, p) => arr[Math.floor(arr.length * p)] ?? NaN;
    console.log(`flat=${flat} healthy(cm-domain, foot≥2m)=${healthy} needle-like(h>0.12, foot<1.5)=${needleLike} other=${other}`);
    console.log(`needle pre-heights: med=${q(preHs, 0.5)?.toFixed(3)} p95=${q(preHs, 0.95)?.toFixed(3)} max=${preHs[preHs.length - 1]?.toFixed(3)}`);
    console.log(`needle pre-footprints: med=${q(preFoots, 0.5)?.toFixed(3)} p95=${q(preFoots, 0.95)?.toFixed(3)}`);
    console.log(`needle spread (world XZ): x ${needleSpread.min.x?.toFixed(0)}..${needleSpread.max.x?.toFixed(0)}  z ${needleSpread.min.z?.toFixed(0)}..${needleSpread.max.z?.toFixed(0)}`);
    /* ×100 projection: how many become runtime needles? */
    let becomeNeedles = 0;
    for (const b of comps) {
      const h = (b.max.y - b.min.y) * 100;
      const foot = Math.max(b.max.x - b.min.x, b.max.z - b.min.z);
      if (h > 15 && (foot < 2 || h / Math.max(foot, 0.01) > 8)) becomeNeedles += 1;
    }
    console.log(`components that become runtime needles after ×100: ${becomeNeedles}`);
  });
}, (e) => { console.error("parse failed", e); process.exit(1); });
