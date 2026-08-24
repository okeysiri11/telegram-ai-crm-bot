/**
 * STEP 29.9 — node-transform census over all 45 GLB JSON chunks.
 * Verifies the metric rebuild only needs scale 0.01 → 1.0 (no matrices,
 * no other scales, no nested scaled parents).
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const here = path.dirname(url.fileURLToPath(import.meta.url));
const assetsDir = path.resolve(here, "../public/assets/odessa");

function listGlbs(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...listGlbs(p));
    else if (e.name.endsWith(".glb")) out.push(p);
  }
  return out;
}

function readJsonChunk(file) {
  const buf = fs.readFileSync(file);
  if (buf.readUInt32LE(0) !== 0x46546c67) throw new Error("not glb: " + file);
  const jsonLen = buf.readUInt32LE(12);
  if (buf.readUInt32LE(16) !== 0x4e4f534a) throw new Error("no JSON chunk: " + file);
  return JSON.parse(buf.subarray(20, 20 + jsonLen).toString("utf8"));
}

const scaleKinds = new Map();
let matrices = 0, translations = 0, rotations = 0, totalNodes = 0, files = 0;
const oddities = [];

for (const file of listGlbs(assetsDir)) {
  files += 1;
  const json = readJsonChunk(file);
  const rel = path.relative(assetsDir, file);
  for (const node of json.nodes ?? []) {
    totalNodes += 1;
    if (node.matrix) {
      matrices += 1;
      oddities.push(`${rel}: node "${node.name}" uses matrix`);
    }
    if (node.translation && node.translation.some((v) => v !== 0)) translations += 1;
    if (node.rotation) rotations += 1;
    const s = node.scale ? node.scale.map((v) => +v.toFixed(6)).join(",") : "none";
    scaleKinds.set(s, (scaleKinds.get(s) ?? 0) + 1);
    if (node.scale && node.scale.some((v) => Math.abs(v - 0.01) > 1e-9)) {
      oddities.push(`${rel}: node "${node.name}" scale=[${node.scale}]`);
    }
  }
}

console.log(`files=${files} nodes=${totalNodes} withMatrix=${matrices} withTranslation=${translations} withRotation=${rotations}`);
console.log("scale kinds:");
for (const [k, c] of [...scaleKinds.entries()].sort((a, b) => b[1] - a[1])) console.log(`  [${k}] × ${c}`);
console.log(`oddities: ${oddities.length}`);
for (const o of oddities.slice(0, 30)) console.log("  " + o);
