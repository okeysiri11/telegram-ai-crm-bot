// @vitest-environment node
/**
 * STEP 29.7 — RUNTIME spike forensics.
 *
 * Unlike the STEP 29.6 offline simulation (which composed transforms from the
 * glTF JSON), this harness reproduces the ACTUAL runtime path end to end:
 * real GLB bytes → real THREE.GLTFLoader.parse → real prepareParsedScene
 * (selective vertical recovery + decal layering + performance pass) → attach
 * under an identity city root (the production attach adds no transforms) →
 * Box3 measurement of final rendered world geometry.
 *
 * It additionally decomposes every recovered building-family mesh into
 * connected geometry components (via the index buffer) to find needle
 * features INSIDE merged meshes — invisible to per-mesh bounding boxes.
 *
 * Heavy (parses every source GLB, ~200 MB): gated behind
 * ODESSA_RUNTIME_FORENSICS=1. Run manually:
 *   ODESSA_RUNTIME_FORENSICS=1 npx vitest run verticalRecovery.runtime
 * Writes scripts/step29_7_runtime_report.json.
 */

import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { prepareParsedScene } from "./scenePrep";
import { classifyRuntimeSpike, type MeshRecoveryTag } from "./verticalRecovery";

const ENABLED = process.env.ODESSA_RUNTIME_FORENSICS === "1";
/* STEP 29.9: default the heavy harness at the rebuilt metric package.
 * Pass ODESSA_RUNTIME_PACKAGE=odessa to audit the legacy rollback tree. */
const assetsDir = path.resolve(
  __dirname,
  "../../../public/assets",
  process.env.ODESSA_RUNTIME_PACKAGE === "odessa" ? "odessa" : "odessa_metric",
);

function listGlbs(dir: string): string[] {
  const out: string[] = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...listGlbs(p));
    else if (e.name.endsWith(".glb")) out.push(p);
  }
  return out;
}

function parseGlb(file: string): Promise<THREE.Group> {
  const buf = fs.readFileSync(file);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  return new Promise((resolve, reject) => {
    new GLTFLoader().parse(ab, "", (gltf) => resolve(gltf.scene), reject);
  });
}

type MeshRow = {
  file: string;
  name: string;
  parentChain: string;
  preH: number;
  h: number;
  footMax: number;
  footMin: number;
  ratio: number;
  visible: boolean;
  scale: number[];
  parentScales: number[][];
  det: number;
  encoded: number | null;
  recovery: MeshRecoveryTag | null;
  spikeSuspect: boolean;
  mixedDomain: boolean;
  runtimeSpike: string | null;
};

function worldBoxOf(mesh: THREE.Mesh): THREE.Box3 | null {
  if (!mesh.geometry) return null;
  if (!mesh.geometry.boundingBox) mesh.geometry.computeBoundingBox();
  if (!mesh.geometry.boundingBox) return null;
  return mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);
}

/** Connected-component world AABBs of a mesh (union-find over triangles). */
function componentBoxes(mesh: THREE.Mesh, maxComponents = 200000): THREE.Box3[] {
  const geo = mesh.geometry;
  const pos = geo.getAttribute("position") as THREE.BufferAttribute | undefined;
  if (!pos) return [];
  const n = pos.count;
  if (n > 2_000_000) return []; // avoid pathological memory use
  const parent = new Int32Array(n);
  for (let i = 0; i < n; i++) parent[i] = i;
  const find = (a: number): number => {
    while (parent[a] !== a) {
      parent[a] = parent[parent[a]];
      a = parent[a];
    }
    return a;
  };
  const union = (a: number, b: number) => {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent[rb] = ra;
  };
  const index = geo.getIndex();
  if (index) {
    for (let i = 0; i < index.count; i += 3) {
      const a = index.getX(i);
      union(a, index.getX(i + 1));
      union(a, index.getX(i + 2));
    }
  } else {
    for (let i = 0; i < n; i += 3) {
      union(i, i + 1);
      union(i, i + 2);
    }
  }
  /* weld duplicated flat-shading vertices by raw position so a building's
   * faces form ONE component (same methodology as the domain-table generator) */
  const weld = new Map<string, number>();
  for (let i = 0; i < n; i++) {
    const key = `${Math.round(pos.getX(i) * 1000)},${Math.round(pos.getY(i) * 1000)},${Math.round(pos.getZ(i) * 1000)}`;
    const first = weld.get(key);
    if (first === undefined) weld.set(key, i);
    else union(first, i);
  }
  const boxes = new Map<number, THREE.Box3>();
  const v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    const r = find(i);
    let box = boxes.get(r);
    if (!box) {
      if (boxes.size >= maxComponents) return [];
      box = new THREE.Box3();
      boxes.set(r, box);
    }
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.matrixWorld);
    box.expandByPoint(v);
  }
  return [...boxes.values()];
}

describe.runIf(ENABLED)("STEP 29.7 runtime spike forensics (real GLBs, real loader, real pipeline)", () => {
  it(
    "measures final rendered world geometry after the full production prep path",
    { timeout: 900_000 },
    async () => {
      const files = listGlbs(assetsDir);
      expect(files.length).toBeGreaterThan(0);

      const cityRoot = new THREE.Group();
      cityRoot.name = "odessaCityRoot";

      const rows: MeshRow[] = [];
      const componentNeedles: Array<{ file: string; mesh: string; count: number; samples: unknown[] }> = [];
      /* STEP 29.8 component repair accounting across the whole city */
      const repairTotals = {
        meshes: 0,
        totalComponents: 0,
        repairedComponents: 0,
        miniatureAnomalies: 0,
        guardReverts: 0,
        modifiedVertices: 0,
      };

      for (const file of files) {
        const rel = path.relative(assetsDir, file);
        const scene = await parseGlb(file);

        /* pre-recovery world heights, exactly as the loader produced them */
        scene.updateMatrixWorld(true);
        const preH = new Map<THREE.Mesh, number>();
        scene.traverse((o) => {
          const m = o as THREE.Mesh;
          if (!m.isMesh) return;
          const b = worldBoxOf(m);
          if (b) preH.set(m, b.max.y - b.min.y);
        });

        /* REAL production prep (recovery + decal layering + perf pass) */
        prepareParsedScene(scene, { enableShadows: false, maxAnisotropy: 1, assetId: rel, environmentQuality: "medium" });

        /* production attach: identity layer group under identity city root */
        cityRoot.add(scene);
        cityRoot.updateMatrixWorld(true);

        scene.traverse((o) => {
          const mesh = o as THREE.Mesh;
          if (!mesh.isMesh) return;
          const box = worldBoxOf(mesh);
          if (!box) return;
          const h = box.max.y - box.min.y;
          const fx = box.max.x - box.min.x;
          const fz = box.max.z - box.min.z;
          const footMax = Math.max(fx, fz);
          const chain: string[] = [];
          const parentScales: number[][] = [];
          let p: THREE.Object3D | null = mesh.parent;
          while (p) {
            chain.unshift(p.name || p.type);
            parentScales.unshift([p.scale.x, p.scale.y, p.scale.z]);
            p = p.parent;
          }
          const enc = mesh.name.match(/height_(\d+)(?:_(\d+))?/i);
          rows.push({
            file: rel,
            name: mesh.name,
            parentChain: chain.join("/"),
            preH: +(preH.get(mesh) ?? NaN).toFixed(4),
            h: +h.toFixed(4),
            footMax: +footMax.toFixed(3),
            footMin: +Math.min(fx, fz).toFixed(3),
            ratio: +(h / Math.max(footMax, 0.01)).toFixed(2),
            visible: mesh.visible,
            scale: [mesh.scale.x, mesh.scale.y, mesh.scale.z],
            parentScales,
            det: +mesh.matrixWorld.determinant().toFixed(6),
            encoded: enc ? Number(enc[2] ? `${enc[1]}.${enc[2]}` : enc[1]) : null,
            recovery: (mesh.userData.odessaVerticalRecovery as MeshRecoveryTag | undefined) ?? null,
            spikeSuspect: !!mesh.userData.odessaSpikeSuspect,
            mixedDomain: !!mesh.userData.odessaMixedDomain,
            runtimeSpike: classifyRuntimeSpike(box),
          });

          /* sub-mesh GROUND-STANDING needle features inside recovered AND
           * component-repaired building meshes (rooftop masts with a high
           * base are legitimate) — STEP 29.8 acceptance is component-level */
          if (
            mesh.userData.odessaVerticalRecovery ||
            mesh.userData.odessaComponentRepair ||
            /build|height/i.test(mesh.name)
          ) {
            const comps = componentBoxes(mesh);
            const needles = comps.filter((c) => {
              const ch = c.max.y - c.min.y;
              const cf = Math.max(c.max.x - c.min.x, c.max.z - c.min.z);
              return ch > 15 && c.min.y < 5 && (cf < 2 || ch / Math.max(cf, 0.01) > 8);
            });
            if (needles.length > 0) {
              componentNeedles.push({
                file: rel,
                mesh: mesh.name,
                count: needles.length,
                samples: needles.slice(0, 5).map((c) => ({
                  h: +(c.max.y - c.min.y).toFixed(2),
                  foot: +Math.max(c.max.x - c.min.x, c.max.z - c.min.z).toFixed(3),
                  at: [+c.min.x.toFixed(1), +c.min.y.toFixed(2), +c.min.z.toFixed(1)],
                })),
              });
            }
          }
        });

        scene.traverse((o) => {
          const m = o as THREE.Mesh;
          const tag = m.userData?.odessaComponentRepair as
            | {
                applied: boolean;
                totalComponents: number;
                repairedComponents: number;
                miniatureComponents: number;
                revertedComponents: number;
                modifiedVertices: number;
              }
            | undefined;
          if (!m.isMesh || !tag?.applied) return;
          repairTotals.meshes += 1;
          repairTotals.totalComponents += tag.totalComponents;
          repairTotals.repairedComponents += tag.repairedComponents;
          repairTotals.miniatureAnomalies += tag.miniatureComponents;
          repairTotals.guardReverts += tag.revertedComponents;
          repairTotals.modifiedVertices += tag.modifiedVertices;
        });

        /* keep memory bounded — measurements are recorded, graph can go */
        cityRoot.remove(scene);
        scene.traverse((o) => {
          const m = o as THREE.Mesh;
          if (m.isMesh) {
            m.geometry?.dispose();
          }
        });
      }

      const suspects = rows.filter((r) => r.runtimeSpike != null && r.visible);
      const recovered = rows.filter((r) => r.recovery != null);
      const mixedDomain = rows.filter((r) => r.mixedDomain);
      const heights = rows.filter((r) => r.visible).map((r) => r.h).sort((a, b) => a - b);
      const q = (p: number) => heights[Math.min(heights.length - 1, Math.floor(heights.length * p))];
      const h95 = rows.filter((r) => r.name === "WEB_height_95");
      const h199 = rows.filter((r) => r.name === "WEB_height_199");

      const summary = {
        files: files.length,
        meshes: rows.length,
        recovered: recovered.length,
        mixedDomainSkipped: mixedDomain.length,
        runtimeSpikeSuspects: suspects.length,
        componentNeedleMeshes: componentNeedles.length,
        componentNeedleTotal: componentNeedles.reduce((s, c) => s + c.count, 0),
        componentRepair: repairTotals,
        maxWorldHeight: heights[heights.length - 1],
        p95: q(0.95),
        p99: q(0.99),
        WEB_height_95: h95.map((r) => ({ h: r.h, recovery: r.recovery, spike: r.runtimeSpike })),
        WEB_height_199: h199.map((r) => ({ h: r.h, spikeSuspect: r.spikeSuspect, spike: r.runtimeSpike })),
      };
      // eslint-disable-next-line no-console
      console.log("RUNTIME FORENSICS SUMMARY:", JSON.stringify(summary, null, 2));
      // eslint-disable-next-line no-console
      console.log(
        "RUNTIME SUSPECTS:",
        JSON.stringify(
          suspects.slice(0, 50).map((s) => ({
            name: s.name,
            file: s.file,
            preH: s.preH,
            h: s.h,
            foot: s.footMax,
            ratio: s.ratio,
            kind: s.runtimeSpike,
            recovery: s.recovery,
          })),
          null,
          1,
        ),
      );
      // eslint-disable-next-line no-console
      console.log("COMPONENT NEEDLES:", JSON.stringify(componentNeedles.slice(0, 30), null, 1));

      fs.writeFileSync(
        path.resolve(__dirname, "../../../scripts/step29_7_runtime_report.json"),
        JSON.stringify({ summary, suspects, componentNeedles, rows }, null, 1),
      );

      /* STEP 29.9 metric package: production path applies NO recovery.
       * Buildings must already be metric (WEB_height_N ≈ N meters). */
      expect(suspects.length).toBe(0);
      expect(componentNeedles.reduce((s, c) => s + c.count, 0)).toBe(0);
      expect(repairTotals.meshes).toBe(0);
      expect(repairTotals.repairedComponents).toBe(0);
      for (const r of h95) expect(r.h).toBeGreaterThan(90);
      for (const r of h199) expect(r.h).toBeGreaterThan(190);
    },
  );
});
