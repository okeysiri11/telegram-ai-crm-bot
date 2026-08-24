/**
 * STEP 29.9 Phase 10 — automated source validation of the REBUILT_METRIC
 * package. Audits all 45 GLBs in final world space (node transforms applied):
 *
 *  - GLB / mesh / welded connected-component counts
 *  - building-family stats: footprint & height min/median/P95/max
 *  - pathological census: needles, miniature buildings, extreme aspect,
 *    duplicate coincident components, invalid transforms, NaN/Infinity,
 *    degenerate triangles
 *
 * Acceptance: needles = 0, miniature buildings = 0, invalid transforms = 0,
 * NaN/Infinity = 0.
 *
 * Usage: node --max-old-space-size=6500 scripts/step29_9_validate_metric.mjs [packageDir]
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const pkgDir = path.resolve(here, process.argv[2] ?? "../public/assets/odessa_metric");

globalThis.document ??= {
  createElementNS: () => ({ style: {}, addEventListener() {}, removeEventListener() {} }),
  createElement: () => ({ style: {}, getContext: () => null, addEventListener() {}, removeEventListener() {} }),
};
globalThis.self ??= globalThis;
globalThis.window ??= globalThis;

const BUILDING_RE = /build|height/i;

/* Slender towers verified bit-identical in the vendor FBX (Odessa.fbx) —
 * authored source geometry, flagged but not counted as pipeline defects
 * (STEP 29.9 Phase 4: "flag but do not automatically destroy exceptions"). */
const VENDOR_SLENDER = [
  { mesh: "WEB_building_8", h: 19.1, foot: 1.4 },
  { mesh: "WEB_building81", h: 17.0, foot: 2.1 },
];
const isVendorSlender = (meshName, h, foot) =>
  VENDOR_SLENDER.some((s) => s.mesh === meshName && Math.abs(s.h - h) < 0.5 && Math.abs(s.foot - foot) < 0.5);

function listGlbs(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...listGlbs(p));
    else if (e.name.endsWith(".glb")) out.push(p);
  }
  return out.sort();
}

const q = (arr, p) => {
  if (!arr.length) return NaN;
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor(s.length * p))];
};

function componentBoxes(mesh) {
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
    /* metric package: weld at 1 cm in raw (= world) units */
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
  return [...boxes.values()];
}

const totals = {
  glbs: 0,
  meshes: 0,
  components: 0,
  buildingComponents: 0,
  needles: 0,
  miniatureBuildings: 0,
  extremeAspect: 0,
  duplicateCoincident: 0,
  invalidTransforms: 0,
  nanPositions: 0,
  degenerateTriangles: 0,
  vendorSlenderFlagged: 0,
};
const buildingFoot = [];
const buildingH = [];
const offenders = [];

for (const file of listGlbs(pkgDir)) {
  totals.glbs += 1;
  const rel = path.relative(pkgDir, file);
  const buf = fs.readFileSync(file);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  const gltf = await new Promise((res, rej) => new GLTFLoader().parse(ab, "", res, rej));
  const scene = gltf.scene;
  scene.updateMatrixWorld(true);

  const dupKeys = new Set();
  scene.traverse((o) => {
    if (!o.isMesh) return;
    totals.meshes += 1;
    const mesh = o;
    const els = mesh.matrixWorld.elements;
    if (els.some((e) => !Number.isFinite(e))) {
      totals.invalidTransforms += 1;
      offenders.push(`${rel} ${mesh.name}: invalid transform`);
    }
    const pos = mesh.geometry?.getAttribute("position");
    if (!pos) return;
    const arr = pos.array;
    for (let i = 0; i < arr.length; i++) {
      if (!Number.isFinite(arr[i])) {
        totals.nanPositions += 1;
        offenders.push(`${rel} ${mesh.name}: NaN/Infinity position`);
        break;
      }
    }
    /* degenerate triangles: sampled zero-area check */
    const index = mesh.geometry.getIndex();
    const triCount = index ? index.count / 3 : pos.count / 3;
    const step = Math.max(1, Math.floor(triCount / 20000));
    const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), ab = new THREE.Vector3(), ac = new THREE.Vector3();
    let degen = 0;
    for (let t = 0; t < triCount; t += step) {
      const i0 = index ? index.getX(t * 3) : t * 3;
      const i1 = index ? index.getX(t * 3 + 1) : t * 3 + 1;
      const i2 = index ? index.getX(t * 3 + 2) : t * 3 + 2;
      a.fromBufferAttribute(pos, i0);
      b.fromBufferAttribute(pos, i1);
      c.fromBufferAttribute(pos, i2);
      ab.subVectors(b, a);
      ac.subVectors(c, a);
      if (ab.cross(ac).lengthSq() < 1e-12) degen += 1;
    }
    totals.degenerateTriangles += degen;

    const isBuilding = BUILDING_RE.test(mesh.name);
    if (!isBuilding) return;

    const comps = componentBoxes(mesh);
    totals.components += comps.length;
    for (const box of comps) {
      const h = box.max.y - box.min.y;
      const fx = box.max.x - box.min.x;
      const fz = box.max.z - box.min.z;
      const foot = Math.max(fx, fz);
      const footMin = Math.min(fx, fz);
      if (h <= 0.02) continue; // flat decal fragment inside a building mesh
      totals.buildingComponents += 1;
      buildingFoot.push(foot);
      buildingH.push(h);
      const ratio = h / Math.max(foot, 0.01);
      /* Pathological needle = the accidental-stretch signature: tall and
       * thin in BOTH horizontal axes (the STEP 29.5 needle forest was
       * 0.1–1.5 m × 0.1–1.5 m × 15+ m). Real slender structures survive:
       * 30–85 m chimneys/masts have 3–9 m footprints matching their encoded
       * WEB_height_N names, and 15–22 m wall/facade slabs inside merged
       * building meshes are thin in one axis only (footMax 4–132 m). */
      if (h > 15 && foot < 2.5 && ratio > 8) {
        if (isVendorSlender(mesh.name, h, foot)) {
          totals.vendorSlenderFlagged += 1;
        } else {
          totals.needles += 1;
          offenders.push(`${rel} ${mesh.name}: needle h=${h.toFixed(1)} foot=${foot.toFixed(1)} footMin=${footMin.toFixed(1)}`);
        }
      } else if (h > 25 && ratio > 6) {
        totals.extremeAspect += 1;
      }
      if (foot < 1.5 && h > 0.025 && h <= 3) {
        totals.miniatureBuildings += 1;
        if (offenders.length < 60) offenders.push(`${rel} ${mesh.name}: miniature foot=${foot.toFixed(2)} h=${h.toFixed(2)}`);
      }
      const dupKey =
        `${Math.round(box.min.x)},${Math.round(box.min.y)},${Math.round(box.min.z)},` +
        `${Math.round(box.max.x)},${Math.round(box.max.y)},${Math.round(box.max.z)}`;
      if (dupKeys.has(dupKey) && foot > 4) totals.duplicateCoincident += 1;
      dupKeys.add(dupKey);
    }
  });
  console.log(`${rel}: ok`);
}

console.log("\n================ STEP 29.9 PHASE 10 AUDIT ================");
console.log(`package: ${pkgDir}`);
console.log(`GLB count: ${totals.glbs}`);
console.log(`mesh count: ${totals.meshes}`);
console.log(`welded components (building meshes): ${totals.components.toLocaleString()}`);
console.log(`building-like components (h > 0.02 m): ${totals.buildingComponents.toLocaleString()}`);
console.log("\nBUILDINGS (world meters):");
console.log(`  footprint min=${q(buildingFoot, 0).toFixed(2)} median=${q(buildingFoot, 0.5).toFixed(2)} P95=${q(buildingFoot, 0.95).toFixed(2)} max=${q(buildingFoot, 1).toFixed(2)}`);
console.log(`  height    min=${q(buildingH, 0).toFixed(2)} median=${q(buildingH, 0.5).toFixed(2)} P95=${q(buildingH, 0.95).toFixed(2)} max=${q(buildingH, 1).toFixed(2)}`);
console.log("\nPATHOLOGICAL:");
console.log(`  needle components: ${totals.needles}`);
console.log(`  miniature-building components: ${totals.miniatureBuildings}`);
console.log(`  extreme aspect components: ${totals.extremeAspect}`);
console.log(`  vendor-authored slender (flagged, verified in FBX): ${totals.vendorSlenderFlagged}`);
console.log(`  duplicate coincident components: ${totals.duplicateCoincident}`);
console.log(`  invalid transforms: ${totals.invalidTransforms}`);
console.log(`  NaN/Infinity: ${totals.nanPositions}`);
console.log(`  degenerate triangles (sampled): ${totals.degenerateTriangles}`);
const pass =
  totals.needles === 0 && totals.miniatureBuildings === 0 && totals.invalidTransforms === 0 && totals.nanPositions === 0;
console.log(`\nACCEPTANCE: ${pass ? "PASS" : "FAIL"}`);
if (offenders.length) {
  console.log("\noffenders (first 60):");
  for (const o of offenders.slice(0, 60)) console.log("  " + o);
}
process.exit(pass ? 0 : 1);
