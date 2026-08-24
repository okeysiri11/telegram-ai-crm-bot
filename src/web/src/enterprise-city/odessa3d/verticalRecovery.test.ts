/**
 * STEP 29.5/29.6 — selective vertical-scale recovery regression tests.
 *
 * Test meshes replicate the real Odessa GLB node structure proven in the
 * STEP 29.5 Phase 1 audit: geometry vertical axis authored in meters on
 * local −Z, horizontal in cm, node rotation +90° about X (local −Z →
 * world +Y), uniform node scale 0.01. The all-meters anomaly domain
 * (STEP 29.6) uses meter-sized raw values on every axis.
 */

import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  ODESSA_VERTICAL_RECOVERY_FACTOR,
  ODESSA_VERTICAL_RECOVERY_MODE,
  VERTICAL_RECOVERY_VERSION,
  applyOdessaVerticalScaleRecovery,
  classifyRuntimeSpike,
  countVerticalRecoveredMeshes,
  isBuildingFamilyName,
  parseEncodedHeight,
  revertOdessaVerticalScaleRecovery,
  type MeshRecoveryTag,
} from "./verticalRecovery";
import { applyGroundDecalLayering, collectRuntimeSpikeReport, decalRankForY } from "./renderDebugTools";

/** Real source structure: raw cm footprint, raw meter height on −Z, rot +90°X, scale 0.01. */
function glbExtrusion(name: string, footprintRaw: number, heightRaw: number, tx = 0, tz = 0): THREE.Mesh {
  const geo = new THREE.BoxGeometry(footprintRaw, footprintRaw, heightRaw);
  geo.translate(0, 0, -heightRaw / 2); /* z ∈ [-heightRaw, 0] like WEB_height_199 */
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ name: `${name}_mat` }));
  mesh.name = name;
  mesh.quaternion.set(Math.SQRT1_2, 0, 0, Math.SQRT1_2);
  mesh.scale.setScalar(0.01);
  mesh.position.set(tx, 0, tz);
  return mesh;
}

function flatDecal(name: string, y: number, size = 600): THREE.Mesh {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(size, 0.0001, size), new THREE.MeshStandardMaterial({ name }));
  mesh.name = name;
  mesh.position.y = y;
  return mesh;
}

function worldBox(mesh: THREE.Mesh): THREE.Box3 {
  mesh.updateWorldMatrix(true, false);
  mesh.geometry.computeBoundingBox();
  return mesh.geometry.boundingBox!.clone().applyMatrix4(mesh.matrixWorld);
}

describe("STEP 29.6 selective vertical recovery", () => {
  it("production mode is selective with the proven ×100 pipeline factor", () => {
    expect(ODESSA_VERTICAL_RECOVERY_MODE).toBe("selective");
    expect(ODESSA_VERTICAL_RECOVERY_FACTOR).toBe(100);
    expect(parseEncodedHeight("WEB_height_2_5")).toBe(2.5);
    expect(parseEncodedHeight("WEB_height_3_m")).toBe(3);
    expect(parseEncodedHeight("WEB_road_primary")).toBeNull();
    expect(isBuildingFamilyName("HEAVY_BUILDING_CHUNK_00_00")).toBe(true);
    expect(isBuildingFamilyName("WEB_building42")).toBe(true);
    expect(isBuildingFamilyName("WEB_plane_15")).toBe(false);
  });

  it("encoded 199 m and 95 m buildings render at their encoded heights (source decides the factor)", () => {
    const root = new THREE.Group();
    /* plausible cm-domain footprints (≥ 2 m world) */
    const t199 = glbExtrusion("WEB_height_199", 3000, 199);
    const t95 = glbExtrusion("WEB_height_95", 2330, 95, 82.31, -166.27);
    root.add(t199, t95);

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(2);
    expect(result.factorExact).toBe(2);

    expect(worldBox(t199).max.y - worldBox(t199).min.y).toBeCloseTo(199, 0);
    expect(worldBox(t95).max.y - worldBox(t95).min.y).toBeCloseTo(95, 0);
    /* Phase 6 target: |rendered − encoded| / encoded ≤ 1 % */
    expect(Math.abs(worldBox(t95).max.y - worldBox(t95).min.y - 95) / 95).toBeLessThanOrEqual(0.01);
  });

  it("an already-correct building is NOT multiplied ×100 (factor ≈ 1 detected)", () => {
    const root = new THREE.Group();
    /* authored fully correct: 95 m tall in world already */
    const ok = new THREE.Mesh(new THREE.BoxGeometry(30, 95, 30), new THREE.MeshStandardMaterial());
    ok.name = "WEB_height_95";
    ok.position.y = 47.5;
    root.add(ok);

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(0);
    expect(result.factorAlreadyCorrect).toBe(1);
    expect(worldBox(ok).max.y - worldBox(ok).min.y).toBeCloseTo(95, 3);
  });

  it("a partially-scaled encoded building gets exactly the required factor (×10 example)", () => {
    const root = new THREE.Group();
    /* world height 9.5 m, encoded 95 → requiredFactor = 10 */
    const partial = new THREE.Mesh(new THREE.BoxGeometry(30, 9.5, 30), new THREE.MeshStandardMaterial());
    partial.name = "WEB_height_95";
    partial.position.y = 4.75;
    root.add(partial);

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(1);
    const box = worldBox(partial);
    expect(box.max.y - box.min.y).toBeCloseTo(95, 1);
    expect((partial.userData.odessaVerticalRecovery as { factor: number }).factor).toBeCloseTo(10, 1);
  });

  it("needle guard: encoded mesh with degenerate footprint (all-meters domain) is NOT recovered and is flagged", () => {
    const root = new THREE.Group();
    /* real case WEB_height_75: raw 8.77×8.51×75 all in meters → world footprint 0.09 m */
    const needle = glbExtrusion("WEB_height_75", 8.77, 75);
    root.add(needle);

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(0);
    expect(result.skippedNeedleGuard).toBe(1);
    expect(needle.userData.odessaSpikeSuspect).toBe(true);
    /* stays a tiny sliver instead of becoming a 75 m spike */
    expect(worldBox(needle).max.y - worldBox(needle).min.y).toBeCloseTo(0.75, 3);
  });

  it("non-building meshes are NOT recovered merely for being outside the ground band", () => {
    const root = new THREE.Group();
    const plane = glbExtrusion("WEB_plane_15", 32.3, 9.16); /* all-meters tree/plane */
    const pier = flatDecal("WEB_man_made_pier", 0.11, 40); /* elevated flat structure */
    const rivers = new THREE.Mesh(new THREE.BoxGeometry(600, 0.021, 600), new THREE.MeshStandardMaterial());
    rivers.name = "WEB_rivers"; /* just above the decal threshold */
    rivers.position.y = 0.0105;
    root.add(plane, pier, rivers);

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(0);
    expect(result.skippedNoEvidence).toBe(3);
    expect(worldBox(pier).min.y).toBeCloseTo(0.11, 3);
    expect(worldBox(rivers).max.y - worldBox(rivers).min.y).toBeCloseTo(0.021, 3);
  });

  it("building-family meshes get the proven pipeline ×100 when flattened and plausible", () => {
    const root = new THREE.Group();
    const chunk = glbExtrusion("HEAVY_BUILDING_CHUNK_01_02", 25000, 22); /* 250 m footprint, 0.22 m flattened */
    const needle = glbExtrusion("WEB_building38", 4.95, 30); /* all-meters anomaly, foot 0.05 m */
    root.add(chunk, needle);

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(1);
    expect(result.factorPipeline).toBe(1);
    expect(result.skippedNeedleGuard).toBe(1);
    expect(worldBox(chunk).max.y - worldBox(chunk).min.y).toBeCloseTo(22, 1);
    expect(worldBox(needle).max.y - worldBox(needle).min.y).toBeCloseTo(0.3, 3);
  });

  it("keeps X/Z world coordinates exact and the building base grounded", () => {
    const root = new THREE.Group();
    const tower = glbExtrusion("WEB_height_95", 2330, 95, 82.31, -166.27);
    root.add(tower);
    root.updateMatrixWorld(true);
    const before = worldBox(tower).clone();

    applyOdessaVerticalScaleRecovery(root, "selective");

    const after = worldBox(tower);
    expect(after.min.x).toBeCloseTo(before.min.x, 6);
    expect(after.max.x).toBeCloseTo(before.max.x, 6);
    expect(after.min.z).toBeCloseTo(before.min.z, 6);
    expect(after.max.z).toBeCloseTo(before.max.z, 6);
    expect(Math.abs(after.min.y)).toBeLessThan(0.01); /* no floating buildings */
  });

  it("never touches the ground-decal band and preserves the STEP 29.4 GPU depth-bias fix", () => {
    const root = new THREE.Group();
    const tower = glbExtrusion("WEB_height_95", 2330, 95);
    const base = flatDecal("WEB_base", -0.005);
    const water = flatDecal("WEB_water", 0);
    const landuse = flatDecal("WEB_landuse_f0", -0.002);
    root.add(tower, base, water, landuse);

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.skippedDecalBand).toBe(3);
    expect(worldBox(base).min.y).toBeCloseTo(-0.005, 4);
    expect(worldBox(water).min.y).toBeCloseTo(0, 4);

    const layering = applyGroundDecalLayering(root);
    expect(layering.decalMeshes).toBe(3);
    const baseMat = base.material as THREE.MeshStandardMaterial;
    const landuseMat = landuse.material as THREE.MeshStandardMaterial;
    expect(baseMat.userData.odessaDecalRank).toBe(decalRankForY(-0.005));
    expect(landuseMat.polygonOffsetFactor).toBeLessThan(baseMat.polygonOffsetFactor);
    expect((tower.material as THREE.MeshStandardMaterial).polygonOffset).toBe(false);
  });

  it("is idempotent and fully reversible", () => {
    const root = new THREE.Group();
    const tower = glbExtrusion("WEB_height_60", 3000, 60);
    root.add(tower);

    applyOdessaVerticalScaleRecovery(root, "selective");
    const once = worldBox(tower).max.y;
    const second = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(second.correctedMeshes).toBe(0);
    expect(worldBox(tower).max.y).toBeCloseTo(once, 6);
    expect(countVerticalRecoveredMeshes(root)).toBe(1);

    const reverted = revertOdessaVerticalScaleRecovery(root);
    expect(reverted).toBe(1);
    expect(worldBox(tower).max.y).toBeCloseTo(0.6, 4);
    expect(countVerticalRecoveredMeshes(root)).toBe(0);
  });

  it("legacy 29.5 mode remains available for dev comparison and off mode changes nothing", () => {
    const root = new THREE.Group();
    const plane = glbExtrusion("WEB_plane_15", 32.3, 9.16);
    root.add(plane);

    const off = applyOdessaVerticalScaleRecovery(root, "off");
    expect(off.correctedMeshes).toBe(0);
    expect(worldBox(plane).max.y - worldBox(plane).min.y).toBeCloseTo(0.0916, 4);

    /* legacy broad rule recovers it (this is the proven spike defect) */
    const legacy = applyOdessaVerticalScaleRecovery(root, "legacy");
    expect(legacy.correctedMeshes).toBe(1);
    expect(worldBox(plane).max.y - worldBox(plane).min.y).toBeCloseTo(9.16, 2);

    /* and reverting restores the source transform without touching GLBs */
    revertOdessaVerticalScaleRecovery(root);
    expect(worldBox(plane).max.y - worldBox(plane).min.y).toBeCloseTo(0.0916, 4);
  });

  it("applies the same world-plane rule across tiles — no vertical seams, horizontal transforms untouched", () => {
    const tileA = new THREE.Group();
    const tileB = new THREE.Group();
    const a = glbExtrusion("WEB_height_30", 2000, 30, 100, 50);
    const b = glbExtrusion("WEB_height_30", 2000, 30, 100, 50);
    tileA.add(a);
    tileB.add(b);

    applyOdessaVerticalScaleRecovery(tileA, "selective");
    applyOdessaVerticalScaleRecovery(tileB, "selective");

    expect(worldBox(a).min.y).toBeCloseTo(worldBox(b).min.y, 6);
    expect(worldBox(a).max.y).toBeCloseTo(worldBox(b).max.y, 6);
    expect(worldBox(a).max.y).toBeCloseTo(30, 1);
    expect(a.position.x).toBe(100);
    expect(a.position.z).toBe(50);
  });
});

/** Geometry with an exact raw vertex count spanning the given box (for
 * domain-table key matching: `${name}|${vertexCount}`). */
function meshWithVertexCount(name: string, count: number, footprint: number, height: number): THREE.Mesh {
  const arr = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    arr[i * 3] = (i % 2 === 0 ? -1 : 1) * (footprint / 2);
    arr[i * 3 + 1] = i % 3 === 0 ? 0 : height;
    arr[i * 3 + 2] = (i % 4 < 2 ? -1 : 1) * (footprint / 2);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(arr, 3));
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ name: `${name}_mat` }));
  mesh.name = name;
  return mesh;
}

describe("STEP 29.7 runtime spike forensics + transform-chain correction", () => {
  it("enforces the FINAL WORLD height (not local) under a scaled parent — nested parent scale accounted for", () => {
    const root = new THREE.Group();
    const tile = new THREE.Group();
    tile.scale.set(1, 0.5, 1); /* hostile parent Y scale */
    const tower = new THREE.Mesh(new THREE.BoxGeometry(30, 9.5, 30), new THREE.MeshStandardMaterial());
    tower.name = "WEB_height_95";
    tower.position.y = 4.75;
    tile.add(tower);
    root.add(tile);
    root.updateMatrixWorld(true);

    /* pre-recovery WORLD height is 9.5 × 0.5 = 4.75 m → required factor 20 */
    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(1);
    const box = worldBox(tower);
    expect(box.max.y - box.min.y).toBeCloseTo(95, 1); /* FINAL WORLD, not local */
    const tag = tower.userData.odessaVerticalRecovery as MeshRecoveryTag;
    expect(tag.factor).toBeCloseTo(20, 1);
    expect(tag.expectedHeight).toBe(95);
  });

  it("Phase 5 marker: version, applied, factor, originalMatrix, sourceHeight, expectedHeight", () => {
    const root = new THREE.Group();
    const tower = glbExtrusion("WEB_height_60", 3000, 60);
    root.add(tower);
    root.updateMatrixWorld(true);
    const original = tower.matrix.toArray();

    applyOdessaVerticalScaleRecovery(root, "selective");
    const tag = tower.userData.odessaVerticalRecovery as MeshRecoveryTag;
    expect(tag.version).toBe(VERTICAL_RECOVERY_VERSION);
    expect(tag.applied).toBe(true);
    expect(tag.factor).toBeCloseTo(100, 0);
    expect(tag.originalMatrix).toEqual(original);
    expect(tag.sourceHeight).toBeCloseTo(0.6, 3);
    expect(tag.expectedHeight).toBe(60);

    /* revert restores the EXACT pre-recovery local matrix */
    revertOdessaVerticalScaleRecovery(root);
    expect(tower.matrix.toArray().every((v, i) => Math.abs(v - original[i]) < 1e-12)).toBe(true);
  });

  it("recovery never runs twice: remount, tile reload, LOD activation, strict-mode reapply", () => {
    const scene = new THREE.Scene();
    const root = new THREE.Group();
    const tower = glbExtrusion("WEB_height_95", 2330, 95);
    root.add(tower);
    scene.add(root);

    applyOdessaVerticalScaleRecovery(root, "selective");
    const h1 = worldBox(tower).max.y - worldBox(tower).min.y;

    /* React remount / strict mode: prep called again on the same graph */
    expect(applyOdessaVerticalScaleRecovery(root, "selective").correctedMeshes).toBe(0);
    /* LOD activation: visibility flips then prep again */
    tower.visible = false;
    tower.visible = true;
    expect(applyOdessaVerticalScaleRecovery(root, "selective").correctedMeshes).toBe(0);
    /* tile deactivate/reactivate: detach + reattach + prep again */
    scene.remove(root);
    scene.add(root);
    expect(applyOdessaVerticalScaleRecovery(root, "selective").correctedMeshes).toBe(0);

    const h2 = worldBox(tower).max.y - worldBox(tower).min.y;
    expect(h2).toBeCloseTo(h1, 6);
    expect(h2).toBeCloseTo(95, 0); /* no repeated ×100 → no 9500 m spike */

    /* tile RELOAD (fresh parse = fresh meshes) converges to the same height */
    const freshRoot = new THREE.Group();
    const fresh = glbExtrusion("WEB_height_95", 2330, 95);
    freshRoot.add(fresh);
    applyOdessaVerticalScaleRecovery(freshRoot, "selective");
    expect(worldBox(fresh).max.y - worldBox(fresh).min.y).toBeCloseTo(h1, 4);
  });

  it("runtime spike classifier operates on final world boxes", () => {
    const box = (w: number, h: number, d: number) => new THREE.Box3(new THREE.Vector3(0, 0, 0), new THREE.Vector3(w, h, d));
    expect(classifyRuntimeSpike(box(0.5, 20, 0.5))).toBe("SPIKE"); /* h>15, foot<2 */
    expect(classifyRuntimeSpike(box(3, 30, 3))).toBe("SPIKE"); /* ratio 10 > 8 */
    expect(classifyRuntimeSpike(box(3, 60, 3))).toBe("TALL_THIN"); /* h>50, foot<5 */
    expect(classifyRuntimeSpike(box(0.01, 20, 0.01))).toBe("ZERO_FOOTPRINT");
    expect(classifyRuntimeSpike(box(30, 20, 30))).toBeNull(); /* healthy building */
    expect(classifyRuntimeSpike(box(2.9, 22.6, 2.4))).toBeNull(); /* chimney at ratio 7.8 */
  });

  it("mixed-domain meshes from the generated table are left exactly as authored and listed", () => {
    const root = new THREE.Group();
    /* WEB_building20|72 is a real repair-components entry (3 ground needles) */
    const mixed = meshWithVertexCount("WEB_building20", 72, 10, 0.22);
    root.add(mixed);
    root.updateMatrixWorld(true);
    const before = mixed.matrix.toArray();

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(0);
    expect(result.skippedMixedDomain).toBe(1);
    expect(mixed.userData.odessaMixedDomain).toBe(true);
    expect(mixed.userData.odessaVerticalRecovery).toBeUndefined();
    expect(mixed.matrix.toArray()).toEqual(before);
    expect(worldBox(mixed).max.y - worldBox(mixed).min.y).toBeCloseTo(0.22, 4);
  });

  it("post-apply verification reverts any correction that would produce a runtime spike", () => {
    const root = new THREE.Group();
    /* encoded mesh with footprint just past the 2 m guard but pencil-thin for
     * its height: 2.1 m × 45 m → ratio 21 → spike post-check must revert */
    const pencil = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.45, 2.1), new THREE.MeshStandardMaterial());
    pencil.name = "WEB_height_45";
    pencil.position.y = 0.225;
    root.add(pencil);
    root.updateMatrixWorld(true);
    const before = pencil.matrix.toArray();

    const result = applyOdessaVerticalScaleRecovery(root, "selective");
    expect(result.correctedMeshes).toBe(0);
    expect(result.revertedSpikePostCheck).toBe(1);
    expect(pencil.userData.odessaSpikeSuspect).toBe(true);
    expect(pencil.matrix.toArray().every((v, i) => Math.abs(v - before[i]) < 1e-9)).toBe(true);
    expect(worldBox(pencil).max.y - worldBox(pencil).min.y).toBeCloseTo(0.45, 3);
  });

  it("runtime spike report over the rendered graph finds zero spikes after selective recovery", () => {
    const root = new THREE.Group();
    root.add(
      glbExtrusion("WEB_height_95", 2330, 95, 82, -166),
      glbExtrusion("HEAVY_BUILDING_CHUNK_01_02", 25000, 22),
      glbExtrusion("WEB_plane_15", 32.3, 9.16),
      flatDecal("WEB_base", -0.005),
    );
    applyOdessaVerticalScaleRecovery(root, "selective");

    const rows = collectRuntimeSpikeReport(root, true);
    expect(rows.length).toBe(4);
    expect(rows.filter((r) => r.runtimeSpike != null && r.visible).length).toBe(0);
    const tower = rows.find((r) => r.name === "WEB_height_95")!;
    expect(tower.worldHeightY).toBeCloseTo(95, 0);
    expect(tower.recovery?.expectedHeight).toBe(95);
    expect(tower.encodedHeight).toBe(95);
  });

  it("X/Z stay exact and the 29.4 depth-bias fix survives the 29.7 path", () => {
    const root = new THREE.Group();
    const tower = glbExtrusion("WEB_height_30", 2000, 30, 55, -12);
    const base = flatDecal("WEB_base", -0.005);
    const landuse = flatDecal("WEB_landuse_f0", -0.002);
    root.add(tower, base, landuse);
    root.updateMatrixWorld(true);
    const beforeBox = worldBox(tower).clone();

    applyOdessaVerticalScaleRecovery(root, "selective");
    applyGroundDecalLayering(root);

    const after = worldBox(tower);
    expect(after.min.x).toBeCloseTo(beforeBox.min.x, 9);
    expect(after.max.z).toBeCloseTo(beforeBox.max.z, 9);
    expect((base.material as THREE.MeshStandardMaterial).polygonOffset).toBe(true);
    expect((landuse.material as THREE.MeshStandardMaterial).polygonOffsetFactor).toBeLessThan(
      (base.material as THREE.MeshStandardMaterial).polygonOffsetFactor,
    );
    expect((tower.material as THREE.MeshStandardMaterial).polygonOffset).toBe(false);
  });
});
