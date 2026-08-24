/**
 * Read-only metric GLB AABB extract. Does not modify assets.
 */
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const assetsDir = path.resolve(here, "../public/assets/odessa_metric");
const manifest = JSON.parse(fs.readFileSync(path.join(assetsDir, "odessa_manifest.json"), "utf8"));

function readGlbJson(file) {
  const buf = fs.readFileSync(file);
  if (buf.readUInt32LE(0) !== 0x46546c67) throw new Error(`not glb: ${file}`);
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
function applyPoint(m, p) {
  return [
    m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
    m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
    m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14],
  ];
}
function worldAabb(m, min, max) {
  const lo = [Infinity, Infinity, Infinity];
  const hi = [-Infinity, -Infinity, -Infinity];
  for (const x of [min[0], max[0]])
    for (const y of [min[1], max[1]])
      for (const z of [min[2], max[2]]) {
        const c = applyPoint(m, [x, y, z]);
        for (let i = 0; i < 3; i++) {
          lo[i] = Math.min(lo[i], c[i]);
          hi[i] = Math.max(hi[i], c[i]);
        }
      }
  return { min: lo, max: hi };
}

function classify(name) {
  const n = name.toLowerCase();
  if (n.includes("water") || n.includes("river")) return "water";
  if (n.includes("highway") || n.includes("route_") || n.includes("railway")) return "road";
  if (n.includes("build") || n.includes("heavy_building")) return "building";
  if (n.includes("coast") || n.includes("natural_s") || n.includes("beach")) return "coast";
  return "other";
}

function extractFile(file, rel) {
  const g = readGlbJson(file);
  const nodes = g.nodes ?? [];
  const meshes = g.meshes ?? [];
  const accessors = g.accessors ?? [];
  const rows = [];
  const walk = (idx, parentMat) => {
    const node = nodes[idx];
    if (!node) return;
    const local = node.matrix ? node.matrix.slice() : fromTRS(node.translation, node.rotation, node.scale);
    const world = mul(parentMat, local);
    if (node.mesh != null) {
      const mesh = meshes[node.mesh];
      for (const prim of mesh.primitives ?? []) {
        const posAcc = accessors[prim.attributes?.POSITION];
        if (!posAcc?.min || !posAcc?.max) continue;
        const wb = worldAabb(world, posAcc.min, posAcc.max);
        const dx = wb.max[0] - wb.min[0];
        const dy = wb.max[1] - wb.min[1];
        const dz = wb.max[2] - wb.min[2];
        rows.push({
          name: node.name || rel,
          file: rel,
          class: classify(node.name || ""),
          cx: +((wb.min[0] + wb.max[0]) / 2).toFixed(3),
          cy: +((wb.min[1] + wb.max[1]) / 2).toFixed(3),
          cz: +((wb.min[2] + wb.max[2]) / 2).toFixed(3),
          dx: +dx.toFixed(3),
          dy: +dy.toFixed(3),
          dz: +dz.toFixed(3),
        });
      }
    }
    for (const c of node.children ?? []) walk(c, world);
  };
  for (const r of g.scenes?.[g.scene ?? 0]?.nodes ?? []) walk(r, I4());
  return rows;
}

const rows = [];
for (const asset of manifest.assets ?? []) {
  const p = path.join(assetsDir, asset.path);
  if (!fs.existsSync(p)) continue;
  rows.push(...extractFile(p, asset.path));
}
const out = {
  package: "odessa_metric",
  count: rows.length,
  buildings: rows.filter((r) => r.class === "building").length,
  roads: rows.filter((r) => r.class === "road").length,
  water: rows.filter((r) => r.class === "water").length,
  rows,
};
const dest = path.resolve(here, "step30_5_model_signatures.json");
fs.writeFileSync(dest, JSON.stringify(out));
console.log(`wrote ${dest} n=${out.count} buildings=${out.buildings} roads=${out.roads} water=${out.water}`);
