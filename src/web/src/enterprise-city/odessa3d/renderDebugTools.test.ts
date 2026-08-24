/**
 * STEP 29.4 — regression tests for the proven artifact root cause:
 * the source GLB stacks flat city-wide OSM decal layers 1–5 mm apart,
 * which z-fight at oblique camera angles. The fix ranks the decal stack
 * with polygonOffset in the authored Y order.
 */

import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  DEFAULT_DEBUG_VIEW,
  MaterialDebugOverride,
  MeshBisector,
  applyGroundDecalLayering,
  cameraAltitudeReport,
  decalRankForY,
  describeIntersection,
  isGroundDecalBox,
  setBasePlaneHidden,
} from "./renderDebugTools";
import { materialInternKey } from "./materialIntern";

function flatMesh(name: string, y: number, size = 600, mat?: THREE.Material): THREE.Mesh {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(size, 0.0001, size),
    mat ?? new THREE.MeshStandardMaterial({ name: `${name}_mat` }),
  );
  mesh.name = name;
  mesh.position.y = y;
  return mesh;
}

describe("STEP 29.4 ground-decal depth layering (root-cause fix)", () => {
  it("classifies the authored mm decal band and ranks it in Y order", () => {
    const landuse = new THREE.Box3(new THREE.Vector3(-300, -0.002, -300), new THREE.Vector3(300, -0.002, 300));
    const building = new THREE.Box3(new THREE.Vector3(0, 0, 0), new THREE.Vector3(20, 0.85, 20));
    expect(isGroundDecalBox(landuse)).toBe(true);
    expect(isGroundDecalBox(building)).toBe(false);

    /* Authored stack order must be strictly preserved: base < labels < landuse < water < natural < leisure < roads */
    const ranks = [-0.005, -0.003, -0.002, 0, 0.001, 0.003, 0.005].map((y) => decalRankForY(y));
    for (let i = 1; i < ranks.length; i++) expect(ranks[i]).toBeGreaterThan(ranks[i - 1]);
  });

  it("STEP 29.9 metric decal stack (×100 authored Y) ranks identically to the legacy mm stack", () => {
    const yScale = 100;
    const landuse = new THREE.Box3(
      new THREE.Vector3(-30000, -0.2, -30000),
      new THREE.Vector3(30000, -0.2, 30000),
    );
    expect(isGroundDecalBox(landuse, yScale)).toBe(true);
    const legacy = [-0.005, -0.003, -0.002, 0, 0.001, 0.003, 0.005].map((y) => decalRankForY(y, 1));
    const metric = [-0.5, -0.3, -0.2, 0, 0.1, 0.3, 0.5].map((y) => decalRankForY(y, yScale));
    expect(metric).toEqual(legacy);
  });

  it("applies polygonOffset to decals, clones shared materials, and never biases buildings", () => {
    const root = new THREE.Group();
    const sharedDefault = new THREE.MeshStandardMaterial({ name: "default_shared" });

    const base = flatMesh("WEB_base", -0.005);
    const landuse = flatMesh("WEB_landuse_f0", -0.002);
    const road = flatMesh("WEB_highway_primary_1", 0.0025, 600, sharedDefault);
    const building = new THREE.Mesh(new THREE.BoxGeometry(20, 0.85, 20), sharedDefault);
    building.name = "WEB_building99";
    building.position.y = 0.425;
    root.add(base, landuse, road, building);

    const result = applyGroundDecalLayering(root);
    expect(result.decalMeshes).toBe(3);

    const baseMat = base.material as THREE.MeshStandardMaterial;
    const landuseMat = landuse.material as THREE.MeshStandardMaterial;
    const roadMat = road.material as THREE.MeshStandardMaterial;

    expect(baseMat.polygonOffset).toBe(true);
    expect(landuseMat.polygonOffset).toBe(true);
    expect(roadMat.polygonOffset).toBe(true);

    /* Higher authored layers get a stronger negative bias (pulled toward camera). */
    expect(roadMat.polygonOffsetFactor).toBeLessThan(landuseMat.polygonOffsetFactor);
    expect(landuseMat.polygonOffsetFactor).toBeLessThan(baseMat.polygonOffsetFactor);
    expect(baseMat.polygonOffsetFactor).toBeLessThanOrEqual(-1);

    /* The building shared the road's material — it must NOT be biased. */
    expect(roadMat).not.toBe(sharedDefault);
    expect(sharedDefault.polygonOffset).toBe(false);
    expect((building.material as THREE.Material)).toBe(sharedDefault);

    /* Idempotent: a second pass creates no additional clones. */
    const again = applyGroundDecalLayering(root);
    expect(again.clonedMaterials).toBe(0);
    expect(again.rankedMaterials).toBe(0);
  });

  it("material intern key never merges different decal ranks", () => {
    const a = new THREE.MeshStandardMaterial({ name: "landuse" });
    const b = a.clone();
    a.polygonOffset = true;
    a.polygonOffsetFactor = -4;
    a.polygonOffsetUnits = -8;
    b.polygonOffset = true;
    b.polygonOffsetFactor = -9;
    b.polygonOffsetUnits = -18;
    expect(materialInternKey(a)).not.toBeNull();
    expect(materialInternKey(a)).not.toBe(materialInternKey(b));
  });
});

describe("STEP 29.4 isolation tooling", () => {
  it("material debug override applies wireframe/side/transparency and restores originals", () => {
    const root = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({ transparent: true, opacity: 0.5, side: THREE.DoubleSide });
    root.add(new THREE.Mesh(new THREE.BoxGeometry(), mat));
    const override = new MaterialDebugOverride();

    override.apply(root, { wireframe: true, sideMode: "front", transparentOff: true });
    expect(mat.wireframe).toBe(true);
    expect(mat.side).toBe(THREE.FrontSide);
    expect(mat.transparent).toBe(false);
    expect(mat.opacity).toBe(1);

    override.apply(root, { ...DEFAULT_DEBUG_VIEW });
    expect(mat.wireframe).toBe(false);
    expect(mat.side).toBe(THREE.DoubleSide);
    expect(mat.transparent).toBe(true);
    expect(mat.opacity).toBe(0.5);
  });

  it("binary bisector halves deterministically, descends, and restores visibility", () => {
    const root = new THREE.Group();
    for (let i = 0; i < 8; i++) root.add(flatMesh(`mesh_${i}`, 0));
    const bisector = new MeshBisector();
    bisector.activate(root);
    expect(bisector.status().totalMeshes).toBe(8);

    bisector.step("HALF_A");
    expect(bisector.status().currentCount).toBe(4);
    const visibleA = root.children.filter((c) => c.visible).length;
    expect(visibleA).toBe(4);

    bisector.step("NEXT_SPLIT");
    bisector.step("HALF_B");
    const st = bisector.status();
    expect(st.currentCount).toBe(2);
    expect(st.depth).toBe(1);
    expect(st.currentNames.length).toBe(2);

    bisector.deactivate();
    expect(root.children.every((c) => c.visible)).toBe(true);
  });

  it("camera altitude report detects below-base and inside-box states", () => {
    const box = new THREE.Box3(new THREE.Vector3(-400, -0.165, -400), new THREE.Vector3(400, 2, 400));
    const cam = new THREE.PerspectiveCamera();
    cam.position.set(0, -1, 0);
    const below = cameraAltitudeReport(cam, box);
    expect(below.belowCityBase).toBe(true);
    expect(below.belowSeaLevel).toBe(true);
    cam.position.set(0, 1, 0);
    const inside = cameraAltitudeReport(cam, box);
    expect(inside.belowCityBase).toBe(false);
    expect(inside.insideCityBox).toBe(true);
  });

  it("hides and restores only the proven WEB_base gray slab", () => {
    const root = new THREE.Group();
    const basePlane = flatMesh("WEB_base", -0.005);
    const other = flatMesh("WEB_landuse_f0", -0.002);
    root.add(basePlane, other);
    expect(setBasePlaneHidden(root, true)).toBe(1);
    expect(basePlane.visible).toBe(false);
    expect(other.visible).toBe(true);
    setBasePlaneHidden(root, false);
    expect(basePlane.visible).toBe(true);
  });

  it("inspector reports object, material, world position, box and decal rank", () => {
    const root = new THREE.Group();
    const slab = flatMesh("WEB_base", -0.005);
    root.add(slab);
    applyGroundDecalLayering(root);
    root.updateMatrixWorld(true);

    const ray = new THREE.Raycaster(new THREE.Vector3(0, 10, 0), new THREE.Vector3(0, -1, 0));
    const hits = ray.intersectObject(root, true);
    expect(hits.length).toBeGreaterThan(0);
    const info = describeIntersection(hits[0]);
    expect(info.object).toBe("WEB_base");
    expect(info.decalRank).toBe(decalRankForY(-0.005));
    expect(info.meshBoxHeight).not.toBeNull();
    expect(info.meshBoxHeight!).toBeLessThan(0.01);
    expect(info.boundingBox).not.toBeNull();
    expect(info.worldPosition[1]).toBeCloseTo(-0.005, 2);
  });
});
