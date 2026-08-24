/**
 * STEP 29.4 Phase 2/5 — offline Odessa GLB mesh inventory.
 *
 * Parses the JSON chunk of every GLB in public/assets/odessa (no geometry
 * decode; POSITION accessor min/max gives exact local AABBs), composes world
 * transforms through the node hierarchy, and flags suspicious large/flat/
 * coplanar/duplicate meshes.
 *
 * Usage: node scripts/step29_4_glb_inventory.mjs [--json out.json]
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const assetsDir = path.resolve(here, "../public/assets/odessa");
const manifest = JSON.parse(fs.readFileSync(path.join(assetsDir, "odessa_manifest.json"), "utf8"));

function readGlbJson(file) {
  const buf = fs.readFileSync(file);
  if (buf.readUInt32LE(0) !== 0x46546c67) throw new Error(`not glb: ${file}`);
  const jsonLen = buf.readUInt32LE(12);
  if (buf.readUInt32LE(16) !== 0x4e4f534a) throw new Error(`first chunk not JSON: ${file}`);
  return JSON.parse(buf.subarray(20, 20 + jsonLen).toString("utf8"));
}

/* --- minimal mat4 (column-major, glTF convention) --- */
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
  const m = [
    (1 - (yy + zz)) * s[0], (xy + wz) * s[0], (xz - wy) * s[0], 0,
    (xy - wz) * s[1], (1 - (xx + zz)) * s[1], (yz + wx) * s[1], 0,
    (xz + wy) * s[2], (yz - wx) * s[2], (1 - (xx + yy)) * s[2], 0,
    t[0], t[1], t[2], 1,
  ];
  return m;
}
function applyPoint(m, p) {
  return [
    m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
    m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
    m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14],
  ];
}
function worldAabb(m, min, max) {
  const corners = [];
  for (const x of [min[0], max[0]])
    for (const y of [min[1], max[1]])
      for (const z of [min[2], max[2]]) corners.push(applyPoint(m, [x, y, z]));
  const lo = [Infinity, Infinity, Infinity];
  const hi = [-Infinity, -Infinity, -Infinity];
  for (const c of corners)
    for (let i = 0; i < 3; i++) {
      lo[i] = Math.min(lo[i], c[i]);
      hi[i] = Math.max(hi[i], c[i]);
    }
  return { min: lo, max: hi };
}

function inventoryFile(file, rel) {
  const g = readGlbJson(file);
  const nodes = g.nodes ?? [];
  const meshes = g.meshes ?? [];
  const accessors = g.accessors ?? [];
  const materials = g.materials ?? [];
  const sceneIdx = g.scene ?? 0;
  const rootIds = g.scenes?.[sceneIdx]?.nodes ?? [];
  const rows = [];

  function walk(idx, parentMat, parentPath) {
    const node = nodes[idx];
    if (!node) return;
    const local = node.matrix ? node.matrix.slice() : fromTRS(node.translation, node.rotation, node.scale);
    const world = mul(parentMat, local);
    const name = node.name || `node_${idx}`;
    const pathStr = parentPath ? `${parentPath}/${name}` : name;
    if (node.mesh != null) {
      const mesh = meshes[node.mesh];
      for (let pi = 0; pi < (mesh.primitives ?? []).length; pi++) {
        const prim = mesh.primitives[pi];
        const posAcc = accessors[prim.attributes?.POSITION];
        if (!posAcc?.min || !posAcc?.max) continue;
        const idxAcc = prim.indices != null ? accessors[prim.indices] : null;
        const tris = idxAcc ? idxAcc.count / 3 : posAcc.count / 3;
        const mat = prim.material != null ? materials[prim.material] : null;
        const wb = worldAabb(world, posAcc.min, posAcc.max);
        rows.push({
          file: rel,
          object: name,
          parentPath: pathStr,
          meshIndex: node.mesh,
          primitive: pi,
          material: mat?.name ?? "(default)",
          materialIndex: prim.material ?? -1,
          alphaMode: mat?.alphaMode ?? "OPAQUE",
          doubleSided: !!mat?.doubleSided,
          baseColor: mat?.pbrMetallicRoughness?.baseColorFactor ?? null,
          metallic: mat?.pbrMetallicRoughness?.metallicFactor ?? 1,
          roughness: mat?.pbrMetallicRoughness?.roughnessFactor ?? 1,
          hasBaseColorTex: mat?.pbrMetallicRoughness?.baseColorTexture != null,
          vertices: posAcc.count,
          triangles: Math.round(tris),
          localMin: posAcc.min,
          localMax: posAcc.max,
          worldMin: wb.min.map((v) => +v.toFixed(3)),
          worldMax: wb.max.map((v) => +v.toFixed(3)),
          translation: node.translation ?? [0, 0, 0],
          rotation: node.rotation ?? [0, 0, 0, 1],
          scale: node.scale ?? [1, 1, 1],
        });
      }
    }
    for (const c of node.children ?? []) walk(c, world, pathStr);
  }
  for (const r of rootIds) walk(r, I4(), "");
  return rows;
}

/* --- collect all GLBs referenced by manifest, plus any stray GLBs on disk --- */
const glbFiles = [];
(function scan(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) scan(p);
    else if (e.name.endsWith(".glb")) glbFiles.push(p);
  }
})(assetsDir);

const manifestUrls = new Set((manifest.assets ?? []).map((a) => path.basename(a.url)));
const allRows = [];
const perFile = [];
for (const f of glbFiles.sort()) {
  const rel = path.relative(assetsDir, f);
  const rows = inventoryFile(f, rel);
  const tris = rows.reduce((s, r) => s + r.triangles, 0);
  perFile.push({
    file: rel,
    inManifest: manifestUrls.has(path.basename(f)),
    meshPrimitives: rows.length,
    triangles: tris,
    sizeMb: +(fs.statSync(f).size / 1e6).toFixed(1),
  });
  allRows.push(...rows);
}

/* --- city bounds from all world AABBs --- */
const city = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
for (const r of allRows)
  for (let i = 0; i < 3; i++) {
    city.min[i] = Math.min(city.min[i], r.worldMin[i]);
    city.max[i] = Math.max(city.max[i], r.worldMax[i]);
  }
const cityW = city.max[0] - city.min[0];
const cityD = city.max[2] - city.min[2];

/* --- suspicion flags --- */
for (const r of allRows) {
  const w = r.worldMax[0] - r.worldMin[0];
  const h = r.worldMax[1] - r.worldMin[1];
  const d = r.worldMax[2] - r.worldMin[2];
  const flags = [];
  if (w > cityW * 0.5 && d > cityD * 0.5) flags.push("CITY_WIDE_FOOTPRINT");
  else if (w > cityW * 0.25 && d > cityD * 0.25) flags.push("QUARTER_CITY_FOOTPRINT");
  if (h < 0.02 * Math.max(w, d) && Math.max(w, d) > 100) flags.push("FLAT_SLAB");
  if (r.worldMin[1] < -5) flags.push("EXTENDS_BELOW_CITY");
  if (r.worldMin[1] <= 0.05 && r.worldMax[1] >= -0.05 && Math.max(w, d) > 100) flags.push("AT_SEA_LEVEL");
  if (r.doubleSided && Math.max(w, d) > 100) flags.push("LARGE_DOUBLE_SIDED");
  if (r.alphaMode !== "OPAQUE" && Math.max(w, d) > 100) flags.push("LARGE_TRANSPARENT");
  r.footprint = { w: +w.toFixed(1), h: +h.toFixed(2), d: +d.toFixed(1) };
  r.flags = flags;
}

/* --- duplicates: same file-agnostic name OR same world AABB (within 0.5m) + same tri count --- */
const byKey = new Map();
for (const r of allRows) {
  const key = `${r.triangles}|${r.worldMin.map((v) => Math.round(v * 2)).join(",")}|${r.worldMax.map((v) => Math.round(v * 2)).join(",")}`;
  if (!byKey.has(key)) byKey.set(key, []);
  byKey.get(key).push(r);
}
const duplicates = [...byKey.values()].filter((g) => g.length > 1);

/* --- coplanar large flat meshes: FLAT_SLAB rows whose Y bands overlap within 0.5m and XZ overlap > 50% --- */
const flats = allRows.filter((r) => r.flags.includes("FLAT_SLAB"));
const coplanar = [];
for (let i = 0; i < flats.length; i++)
  for (let j = i + 1; j < flats.length; j++) {
    const a = flats[i], b = flats[j];
    const yGap = Math.abs((a.worldMin[1] + a.worldMax[1]) / 2 - (b.worldMin[1] + b.worldMax[1]) / 2);
    if (yGap > 0.5) continue;
    const ox = Math.min(a.worldMax[0], b.worldMax[0]) - Math.max(a.worldMin[0], b.worldMin[0]);
    const oz = Math.min(a.worldMax[2], b.worldMax[2]) - Math.max(a.worldMin[2], b.worldMin[2]);
    if (ox <= 0 || oz <= 0) continue;
    const overlapArea = ox * oz;
    const aArea = a.footprint.w * a.footprint.d;
    const bArea = b.footprint.w * b.footprint.d;
    const frac = overlapArea / Math.min(aArea, bArea);
    if (frac > 0.5) coplanar.push({ a: `${a.file}:${a.object}`, b: `${b.file}:${b.object}`, yGap: +yGap.toFixed(3), overlapFrac: +frac.toFixed(2) });
  }

const suspicious = allRows.filter((r) => r.flags.length > 0);
suspicious.sort((a, b) => (b.footprint.w * b.footprint.d) - (a.footprint.w * a.footprint.d));

const out = {
  generatedAt: new Date().toISOString(),
  cityBoundsComputed: city,
  manifestCityBounds: manifest.cityBounds,
  files: perFile,
  totals: {
    files: perFile.length,
    meshPrimitives: allRows.length,
    triangles: allRows.reduce((s, r) => s + r.triangles, 0),
  },
  suspicious,
  duplicateGroups: duplicates.map((g) => g.map((r) => `${r.file}:${r.parentPath} tris=${r.triangles} y=[${r.worldMin[1]},${r.worldMax[1]}]`)),
  coplanar,
};

const jsonArg = process.argv.indexOf("--json");
const jsonOut = jsonArg > -1 ? process.argv[jsonArg + 1] : path.resolve(here, "step29_4_inventory.json");
fs.writeFileSync(jsonOut, JSON.stringify(out, null, 1));

console.log(`files=${out.totals.files} meshPrimitives=${out.totals.meshPrimitives} tris=${out.totals.triangles}`);
console.log(`computed city bounds: min=${city.min.map((v) => v.toFixed(1))} max=${city.max.map((v) => v.toFixed(1))}`);
console.log(`manifest city bounds Y: [${manifest.cityBounds.minY}, ${manifest.cityBounds.maxY}]`);
console.log(`suspicious=${suspicious.length} duplicateGroups=${duplicates.length} coplanarPairs=${coplanar.length}`);
console.log("--- top suspicious ---");
for (const r of suspicious.slice(0, 40)) {
  console.log(
    `${r.flags.join("+")} | ${r.file} :: ${r.object} | mat=${r.material} ds=${r.doubleSided} alpha=${r.alphaMode} | ` +
    `fp=${r.footprint.w}x${r.footprint.d} h=${r.footprint.h} y=[${r.worldMin[1]}, ${r.worldMax[1]}] tris=${r.triangles}`,
  );
}
console.log(`json written: ${jsonOut}`);
