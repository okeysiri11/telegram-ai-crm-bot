/**
 * STEP 29.7 — per-mesh vertex-domain table generator.
 *
 * For every mesh that the selective vertical recovery would correct
 * (building-family or encoded, flattened, plausible footprint), performs
 * welded connected-component analysis of the REAL parsed geometry and counts
 * components that would become runtime needles after the mesh's recovery
 * factor (world height > 15 m with footprint < 2 m or aspect > 8).
 *
 * Output: public/assets/odessa/odessa_vertical_domains.json — consumed by
 * verticalRecovery.ts at load time. Deterministic: derived only from source
 * GLB bytes. Regenerate with:
 *   node scripts/step29_7_build_domain_table.mjs
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const assetsDir = path.resolve(here, "../public/assets/odessa");

/* Mirror of the runtime selective rule constants (verticalRecovery.ts). */
const DECAL_MAX_HEIGHT = 0.02;
const DECAL_BAND_Y = 0.06;
const ALREADY_CORRECT_HEIGHT_M = 3;
const MIN_PLAUSIBLE_FOOTPRINT_M = 2;
const FACTOR = 100;

function listGlbs(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...listGlbs(p));
    else if (e.name.endsWith(".glb")) out.push(p);
  }
  return out;
}

function parseGlb(file) {
  const buf = fs.readFileSync(file);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  return new Promise((resolve, reject) => new GLTFLoader().parse(ab, "", (g) => resolve(g.scene), reject));
}

function encodedHeight(name) {
  const m = name.match(/height_(\d+)(?:_(\d+))?/i);
  if (!m) return null;
  const v = Number(m[2] != null && /^\d+$/.test(m[2]) ? `${m[1]}.${m[2]}` : m[1]);
  return Number.isFinite(v) && v > 0 ? v : null;
}
const isBuildingFamily = (name) => /(^|_)build/i.test(name) || /^HEAVY_BUILDING_CHUNK/i.test(name);

function analyzeMesh(mesh, factor) {
  const geo = mesh.geometry;
  const pos = geo.getAttribute("position");
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
  let needles = 0, healthy = 0, flat = 0, other = 0, repairable = 0, miniature = 0;
  for (const b of boxes.values()) {
    const h = (b.max.y - b.min.y) * factor;
    const base = b.min.y * factor; // world base after recovery (scale about y=0)
    const foot = Math.max(b.max.x - b.min.x, b.max.z - b.min.z);
    const footMin = Math.min(b.max.x - b.min.x, b.max.z - b.min.z);
    const hPre = b.max.y - b.min.y;
    if (h < 1) { flat += 1; continue; }
    /* ground-standing needles only: rooftop masts/antennas (base high above
     * ground) are legitimate thin structures, not miniature-domain defects */
    if (h > 15 && base < 5 && (foot < 2 || h / Math.max(foot, 0.01) > 8)) needles += 1;
    else if (foot >= 2) healthy += 1;
    else other += 1;
    /* STEP 29.8 component-level statistics */
    if (footMin >= 2 && hPre > 0.02 && hPre <= 3 && Math.abs(b.min.y) <= 0.5 && h >= 2.5 && h <= 250 && h / Math.max(foot, 0.01) < 8) repairable += 1;
    else if (foot < 1.5 && hPre > 0.025 && hPre <= 3) miniature += 1;
  }
  return { components: boxes.size, needles, healthy, flat, other, repairable, miniature };
}

const table = {};
const stats = [];
const files = listGlbs(assetsDir);
for (const file of files) {
  const rel = path.relative(assetsDir, file);
  const scene = await parseGlb(file);
  scene.updateMatrixWorld(true);
  const meshes = [];
  scene.traverse((o) => o.isMesh && meshes.push(o));
  for (const mesh of meshes) {
    if (!mesh.geometry?.boundingBox) mesh.geometry.computeBoundingBox();
    const box = mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);
    const h = box.max.y - box.min.y;
    const centerY = (box.max.y + box.min.y) / 2;
    const foot = Math.max(box.max.x - box.min.x, box.max.z - box.min.z);
    const enc = encodedHeight(mesh.name);
    const isDecal = h <= DECAL_MAX_HEIGHT && Math.abs(centerY) <= DECAL_BAND_Y;
    const wouldRecover =
      !isDecal &&
      foot >= MIN_PLAUSIBLE_FOOTPRINT_M &&
      ((enc != null && h > 1e-4 && Math.abs(enc / h - 1) > 0.05 && enc / h >= 0.5 && enc / h <= 150) ||
        (enc == null && isBuildingFamily(mesh.name) && h <= ALREADY_CORRECT_HEIGHT_M));
    if (!wouldRecover) continue;
    const factor = enc != null ? enc / h : FACTOR;
    const a = analyzeMesh(mesh, factor);
    if (!a) continue;
    /* STEP 29.8: mixed-domain meshes are no longer merely skipped — their
     * proven cm-domain flattened building components get vertex-level repair */
    const verdict = a.needles === 0 ? "recover" : "repair-components";
    /* runtime key: mesh name + vertex count (file name not available at prep
     * time); on collision keep the conservative repair verdict */
    const key = `${mesh.name}|${mesh.geometry.getAttribute("position").count}`;
    if (table[key] !== "repair-components") table[key] = verdict;
    stats.push({ key, file: rel, ...a, verdict });
  }
  scene.traverse((o) => o.isMesh && o.geometry?.dispose());
}

const skip = stats.filter((s) => s.verdict !== "recover");
const keep = stats.filter((s) => s.verdict === "recover");
console.log(`analyzed recoverable meshes: ${stats.length}`);
console.log(`verdict recover: ${keep.length}`);
console.log(`verdict repair-components: ${skip.length}`);
console.log(`total needle components avoided: ${skip.reduce((s, x) => s + x.needles, 0)}`);
console.log(`repairable flattened cm-domain components in repair meshes: ${skip.reduce((s, x) => s + x.repairable, 0)}`);
console.log(`miniature (SOURCE_ANOMALY) components in repair meshes: ${skip.reduce((s, x) => s + x.miniature, 0)}`);
console.log(`healthy components kept via whole-mesh recovery: ${keep.reduce((s, x) => s + x.healthy, 0)}`);
console.log("\nrepair-components distribution (repairable/miniature):");
skip.sort((a, b) => b.repairable - a.repairable);
for (const s of skip.slice(0, 20)) console.log(`  ${s.key.padEnd(70)} repairable=${String(s.repairable).padStart(5)} miniature=${String(s.miniature).padStart(6)}`);

const sortedKeys = Object.keys(table).sort();
const lines = sortedKeys.map((k) => `  ${JSON.stringify(k)}: ${JSON.stringify(table[k])},`);
const ts = `/**
 * GENERATED by scripts/step29_7_build_domain_table.mjs — DO NOT EDIT.
 *
 * STEP 29.7/29.8 per-mesh vertex unit-domain verdicts, derived from welded
 * connected-component analysis of the source Odessa GLBs.
 *
 * "repair-components": the mesh bakes mixed unit domains at vertex level —
 * miniature (all-meters) features whose real-scale placement was destroyed
 * at export (SOURCE_ANOMALY, left bit-identical) plus cm-domain flattened
 * buildings that ARE recoverable per component. These meshes are excluded
 * from whole-mesh vertical recovery and handed to the STEP 29.8
 * component-level repair (componentRepair.ts).
 *
 * "recover": component analysis found zero ground-standing needle features;
 * the mesh is safe for the whole-mesh selective vertical recovery.
 *
 * Key: \`\${meshName}|\${positionVertexCount}\`.
 */

export type VerticalDomainVerdict = "recover" | "repair-components";

export const ODESSA_VERTICAL_DOMAIN_VERDICTS: Record<string, VerticalDomainVerdict> = {
${lines.join("\n")}
};
`;
fs.writeFileSync(path.resolve(here, "../src/enterprise-city/odessa3d/odessaVerticalDomains.generated.ts"), ts);
console.log("\nwrote src/enterprise-city/odessa3d/odessaVerticalDomains.generated.ts");
