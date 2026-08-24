/**
 * STEP 29.8 — regression tests for component-level geometry repair.
 *
 * Synthetic merged mesh reproducing the measured source defect: one vertex
 * buffer baking a flattened cm-domain building (repairable), a destroyed-
 * placement miniature (SOURCE_ANOMALY, untouched), a flat ground decal and
 * an already-correct metric building.
 */

import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

import {
  COMPONENT_CLASS,
  COMPONENT_REPAIR_FACTOR,
  ComponentColorOverlay,
  applySceneComponentRepair,
  decomposeGeometry,
  getComponentRepairData,
  repairBuildingComponents,
  repairedBoxIsPathological,
  revertComponentRepair,
  setSceneComponentRepairEnabled,
} from "./componentRepair";
import { classifyRuntimeSpike } from "./verticalRecovery";
import { applyGroundDecalLayering } from "./renderDebugTools";

/* ------------------------------------------------------------------ */
/* Fixture: merged buffer with four known components                    */
/* ------------------------------------------------------------------ */

function boxAt(w: number, h: number, d: number, x: number, z: number): THREE.BufferGeometry {
  const g = new THREE.BoxGeometry(w, h, d);
  g.translate(x, h / 2, z); // base on the ground
  return g;
}

function flatDecalAt(size: number, x: number, z: number): THREE.BufferGeometry {
  const g = new THREE.PlaneGeometry(size, size);
  g.rotateX(-Math.PI / 2);
  g.translate(x, 0.001, z);
  return g;
}

/**
 * Component 0: flattened cm-domain building 10×8 m, crushed to 0.18 m (→ 18 m).
 * Component 1: destroyed-placement miniature 0.2×0.15×0.2 m.
 * Component 2: flat ground decal 20×20 m.
 * Component 3: already-correct metric building 12×25×10 m.
 */
function makeMergedCityMesh(): THREE.Mesh {
  const merged = mergeGeometries(
    [boxAt(10, 0.18, 8, 0, 0), boxAt(0.2, 0.15, 0.2, 30, 5), flatDecalAt(20, 60, 0), boxAt(12, 25, 10, 90, 0)],
    true,
  )!;
  const mesh = new THREE.Mesh(merged, new THREE.MeshStandardMaterial({ name: "cityMat" }));
  mesh.name = "WEB_building_synthetic";
  mesh.userData.odessaMixedDomain = true;
  mesh.updateMatrixWorld(true);
  return mesh;
}

function worldBoxOfVerts(mesh: THREE.Mesh, filter: (x: number, y: number, z: number) => boolean): THREE.Box3 {
  const pos = mesh.geometry.getAttribute("position");
  const box = new THREE.Box3();
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    if (!filter(v.x, v.y, v.z)) continue;
    box.expandByPoint(v.applyMatrix4(mesh.matrixWorld));
  }
  return box;
}

describe("STEP 29.8 component-level geometry repair", () => {
  it("1. decomposes a merged buffer into welded connected components", () => {
    const mesh = makeMergedCityMesh();
    const d = decomposeGeometry(mesh)!;
    expect(d.boxes.size).toBe(4);
    const heights = [...d.boxes.values()].map((b) => +(b.max.y - b.min.y).toFixed(3)).sort((a, b) => a - b);
    expect(heights).toEqual([0, 0.15, 0.18, 25]);
  });

  it("2. repairs the flattened building about its own base pivot (ground contact + centroid preserved)", () => {
    const mesh = makeMergedCityMesh();
    const tag = repairBuildingComponents(mesh)!;
    expect(tag.repairedComponents).toBe(1);
    const box = worldBoxOfVerts(mesh, (x) => x < 20);
    expect(box.max.y - box.min.y).toBeCloseTo(0.18 * COMPONENT_REPAIR_FACTOR, 4);
    expect(box.min.y).toBeCloseTo(0, 5); // ground contact preserved
    expect((box.min.x + box.max.x) / 2).toBeCloseTo(0, 5); // world centroid preserved
    expect(box.max.x - box.min.x).toBeCloseTo(10, 5); // footprint untouched
    expect(box.max.z - box.min.z).toBeCloseTo(8, 5);
  });

  it("3. leaves every vertex of unaffected components bit-identical", () => {
    const mesh = makeMergedCityMesh();
    const pos = mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
    const before = Float32Array.from(pos.array as Float32Array);
    repairBuildingComponents(mesh);
    const after = pos.array as Float32Array;
    for (let i = 0; i < pos.count; i++) {
      if (before[i * 3] < 20) continue; // repaired building lives near x=0
      expect(after[i * 3]).toBe(before[i * 3]);
      expect(after[i * 3 + 1]).toBe(before[i * 3 + 1]);
      expect(after[i * 3 + 2]).toBe(before[i * 3 + 2]);
    }
    /* and X/Z of the repaired component too — only Y may change */
    for (let i = 0; i < pos.count; i++) {
      expect(after[i * 3]).toBe(before[i * 3]);
      expect(after[i * 3 + 2]).toBe(before[i * 3 + 2]);
    }
  });

  it("4. preserves UVs exactly", () => {
    const mesh = makeMergedCityMesh();
    const uv = mesh.geometry.getAttribute("uv") as THREE.BufferAttribute;
    const before = Float32Array.from(uv.array as Float32Array);
    repairBuildingComponents(mesh);
    expect(Array.from(uv.array as Float32Array)).toEqual(Array.from(before));
  });

  it("5. keeps normals unit-length and geometrically valid after repair", () => {
    const mesh = makeMergedCityMesh();
    repairBuildingComponents(mesh);
    const nrm = mesh.geometry.getAttribute("normal") as THREE.BufferAttribute;
    const pos = mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
    const n = new THREE.Vector3();
    for (let i = 0; i < nrm.count; i++) {
      n.fromBufferAttribute(nrm, i);
      expect(n.length()).toBeCloseTo(1, 5);
      /* roof of the repaired building must still face straight up */
      if (pos.getX(i) < 20 && pos.getY(i) > 17) {
        if (Math.abs(n.y) > 0.5) expect(n.y).toBeCloseTo(1, 4);
      }
    }
  });

  it("6. keeps the index buffer valid and untouched", () => {
    const mesh = makeMergedCityMesh();
    const index = mesh.geometry.getIndex()!;
    const before = Array.from(index.array);
    repairBuildingComponents(mesh);
    expect(Array.from(index.array)).toEqual(before);
    const vertCount = mesh.geometry.getAttribute("position").count;
    for (const i of index.array) expect(i).toBeLessThan(vertCount);
  });

  it("7. preserves material groups exactly", () => {
    const mesh = makeMergedCityMesh();
    const before = mesh.geometry.groups.map((g) => ({ ...g }));
    const material = mesh.material;
    repairBuildingComponents(mesh);
    expect(mesh.geometry.groups).toEqual(before);
    expect(mesh.material).toBe(material); // materials never touched
  });

  it("8. destroyed-placement miniatures are SOURCE_ANOMALY: counted, never scaled", () => {
    /* Forensic evidence (docs/STEP_29_8): miniature nearest-neighbor spacing
     * is 0.2–0.6 m against intended 15–50 m footprints — no pivot exists that
     * restores them without mass overlap, so XYZ recovery is rejected. */
    const mesh = makeMergedCityMesh();
    const pos = mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
    const before = Float32Array.from(pos.array as Float32Array);
    const tag = repairBuildingComponents(mesh)!;
    expect(tag.miniatureComponents).toBe(1);
    const after = pos.array as Float32Array;
    for (let i = 0; i < pos.count; i++) {
      if (before[i * 3] < 25 || before[i * 3] > 35) continue; // miniature at x≈30
      expect(after[i * 3]).toBe(before[i * 3]);
      expect(after[i * 3 + 1]).toBe(before[i * 3 + 1]);
      expect(after[i * 3 + 2]).toBe(before[i * 3 + 2]);
    }
    const mini = worldBoxOfVerts(mesh, (x) => x > 25 && x < 35);
    expect(mini.max.y - mini.min.y).toBeCloseTo(0.15, 5);
  });

  it("9. already-correct metric buildings stay unchanged", () => {
    const mesh = makeMergedCityMesh();
    repairBuildingComponents(mesh);
    const tall = worldBoxOfVerts(mesh, (x) => x > 80);
    expect(tall.max.y - tall.min.y).toBeCloseTo(25, 5);
  });

  it("10. rivers/roads (not flagged repair-components) are never processed", () => {
    const river = new THREE.Mesh(boxAt(600, 0.01, 4, 0, 0), new THREE.MeshStandardMaterial());
    river.name = "WEB_rivers";
    const root = new THREE.Group();
    root.add(river);
    root.updateMatrixWorld(true);
    const before = Float32Array.from(river.geometry.getAttribute("position").array as Float32Array);
    const result = applySceneComponentRepair(root);
    expect(result.meshesRepaired).toBe(0);
    expect(river.userData.odessaComponentRepair).toBeUndefined();
    expect(Array.from(river.geometry.getAttribute("position").array as Float32Array)).toEqual(Array.from(before));
  });

  it("11. plausibility guards flag pathological repaired boxes for rollback", () => {
    const box = (w: number, h: number, d: number) =>
      new THREE.Box3(new THREE.Vector3(0, 0, 0), new THREE.Vector3(w, h, d));
    expect(repairedBoxIsPathological(box(0.5, 20, 0.5))).toBe(true); // needle: <1 m wide, >10 m tall
    expect(repairedBoxIsPathological(box(3, 40, 3))).toBe(true); // ratio ≥ 10
    expect(repairedBoxIsPathological(box(10, 300, 10))).toBe(true); // > 250 m
    expect(repairedBoxIsPathological(box(10, 1, 8))).toBe(true); // < 2.5 m
    expect(repairedBoxIsPathological(box(10, 18, 8))).toBe(false); // healthy building
  });

  it("12. never duplicates triangles (triangle count invariant)", () => {
    const mesh = makeMergedCityMesh();
    const trisBefore = mesh.geometry.getIndex()!.count / 3;
    repairBuildingComponents(mesh);
    expect(mesh.geometry.getIndex()!.count / 3).toBe(trisBefore);
    expect(mesh.geometry.getAttribute("position").count).toBe(mesh.geometry.getAttribute("normal").count);
  });

  it("13. reports exact final-world component dimensions (ALT+click contract)", () => {
    const mesh = makeMergedCityMesh();
    repairBuildingComponents(mesh);
    const data = getComponentRepairData(mesh)!;
    expect(data.repaired).toHaveLength(1);
    const r = data.repaired[0];
    expect(r.scale).toEqual([1, COMPONENT_REPAIR_FACTOR, 1]);
    expect(r.postBox.max[1] - r.postBox.min[1]).toBeCloseTo(18, 4);
    expect(r.postBox.max[0] - r.postBox.min[0]).toBeCloseTo(10, 4);
    expect(r.postBox.max[2] - r.postBox.min[2]).toBeCloseTo(8, 4);
    expect(r.pivotBaseY).toBeCloseTo(0, 5);
  });

  it("14. produces zero pathological needle components in final world space", () => {
    const mesh = makeMergedCityMesh();
    repairBuildingComponents(mesh);
    const d = decomposeGeometry(mesh)!;
    let needles = 0;
    for (const b of d.boxes.values()) {
      const h = b.max.y - b.min.y;
      if (h < 1) continue;
      if (classifyRuntimeSpike(b) != null && b.min.y < 5) needles += 1;
    }
    expect(needles).toBe(0);
  });

  it("15. is idempotent and exactly reversible across reload/remount", () => {
    const mesh = makeMergedCityMesh();
    const pos = mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
    const original = Float32Array.from(pos.array as Float32Array);

    const tag1 = repairBuildingComponents(mesh)!;
    const afterOnce = Float32Array.from(pos.array as Float32Array);
    const tag2 = repairBuildingComponents(mesh)!; // StrictMode/tile-reload re-entry
    expect(tag2).toBe(tag1);
    expect(Array.from(pos.array as Float32Array)).toEqual(Array.from(afterOnce));

    /* ORIGINAL / REPAIRED dev A/B: exact bit-level reversal */
    expect(revertComponentRepair(mesh)).toBe(true);
    expect(Array.from(pos.array as Float32Array)).toEqual(Array.from(original));

    /* re-apply converges to the same repaired state */
    const root = new THREE.Group();
    root.add(mesh);
    setSceneComponentRepairEnabled(root, true);
    expect(Array.from(pos.array as Float32Array)).toEqual(Array.from(afterOnce));
  });

  it("16. preserves the STEP 29.4 z-fighting decal layering", () => {
    const root = new THREE.Group();
    const mesh = makeMergedCityMesh();
    const decal = new THREE.Mesh(flatDecalAt(100, 0, -200), new THREE.MeshStandardMaterial({ name: "roadDecal" }));
    decal.name = "WEB_roads";
    root.add(mesh, decal);
    root.updateMatrixWorld(true);
    const layering = applyGroundDecalLayering(root);
    expect(layering.decalMeshes).toBeGreaterThan(0);
    const mat = decal.material as THREE.MeshStandardMaterial;
    const offsetBefore = { po: mat.polygonOffset, f: mat.polygonOffsetFactor, u: mat.polygonOffsetUnits };
    applySceneComponentRepair(root);
    expect(mat.polygonOffset).toBe(offsetBefore.po);
    expect(mat.polygonOffsetFactor).toBe(offsetBefore.f);
    expect(mat.polygonOffsetUnits).toBe(offsetBefore.u);
    expect(decal.userData.odessaDecalApplied).not.toBeUndefined();
  });

  it("repairs correctly under the real GLB transform (rotation −90°X, uniform 0.01 scale)", () => {
    /* geometry authored Z-up in raw centimeter-domain units */
    const g = new THREE.BoxGeometry(1000, 800, 18); // 10 m × 8 m × 0.18 m world
    g.translate(0, 0, 9); // base at raw z=0
    const mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial());
    mesh.name = "WEB_building_rot";
    mesh.userData.odessaMixedDomain = true;
    mesh.rotation.x = -Math.PI / 2;
    mesh.scale.setScalar(0.01);
    const root = new THREE.Group();
    root.add(mesh);
    root.updateMatrixWorld(true);

    const preWorld = new THREE.Box3().setFromObject(mesh);
    expect(preWorld.max.y - preWorld.min.y).toBeCloseTo(0.18, 3);

    const tag = repairBuildingComponents(mesh)!;
    expect(tag.repairedComponents).toBe(1);
    mesh.updateMatrixWorld(true);
    const postWorld = new THREE.Box3().setFromObject(mesh);
    expect(postWorld.max.y - postWorld.min.y).toBeCloseTo(18, 3);
    expect(postWorld.min.y).toBeCloseTo(0, 3);
    expect(postWorld.max.x - postWorld.min.x).toBeCloseTo(10, 3);
    expect(postWorld.max.z - postWorld.min.z).toBeCloseTo(8, 3);
  });

  it("dev color overlay applies and restores materials/colors exactly", () => {
    const mesh = makeMergedCityMesh();
    repairBuildingComponents(mesh);
    const root = new THREE.Group();
    root.add(mesh);
    const original = mesh.material;
    const overlay = new ComponentColorOverlay();
    overlay.apply(root, true);
    expect((mesh.material as THREE.Material).name).toBe("odessaComponentOverlay");
    expect(mesh.geometry.getAttribute("color")).toBeDefined();
    overlay.apply(root, false);
    expect(mesh.material).toBe(original);
    expect(mesh.geometry.getAttribute("color")).toBeUndefined();
    overlay.dispose();
  });

  it("component classes label repaired vs miniature vertices for ALT+click", () => {
    const mesh = makeMergedCityMesh();
    repairBuildingComponents(mesh);
    const data = getComponentRepairData(mesh)!;
    const pos = mesh.geometry.getAttribute("position") as THREE.BufferAttribute;
    let repaired = 0;
    let miniature = 0;
    for (let i = 0; i < pos.count; i++) {
      if (data.classes[i] === COMPONENT_CLASS.REPAIRED) repaired += 1;
      if (data.classes[i] === COMPONENT_CLASS.MINIATURE) miniature += 1;
    }
    expect(repaired).toBe(24); // one box, 24 vertices
    expect(miniature).toBe(24);
  });
});
