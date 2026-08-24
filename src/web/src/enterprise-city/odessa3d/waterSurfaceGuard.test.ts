import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  applyWaterSurfaceGuard,
  findDuplicateWaterMeshes,
  isWaterLikeMesh,
  nameLooksLikeWater,
  stabilizeWaterMaterial,
  waterCategoryFromName,
} from "./waterSurfaceGuard";

function makeWaterNode(
  nodeName: string,
  width: number,
  depth: number,
  x: number,
  z: number,
  y = 0,
): { group: THREE.Group; mesh: THREE.Mesh } {
  const group = new THREE.Group();
  group.name = nodeName;
  const geo = new THREE.PlaneGeometry(width, depth);
  geo.rotateX(-Math.PI / 2);
  const mat = new THREE.MeshStandardMaterial({
    name: "Water",
    color: 0x338899,
    metalness: 0.5,
    roughness: 0,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = `Mesh.${nodeName}`;
  group.add(mesh);
  group.position.set(x, y, z);
  group.updateMatrixWorld(true);
  return { group, mesh };
}

describe("Odessa water classification", () => {
  it("classifies sea / river / bay names and rejects towers/wells", () => {
    expect(nameLooksLikeWater("WEB_water")).toBe(true);
    expect(nameLooksLikeWater("Water")).toBe(true);
    expect(nameLooksLikeWater("WEB_bay")).toBe(true);
    expect(nameLooksLikeWater("WEB_rivers")).toBe(true);
    expect(nameLooksLikeWater("WEB_lake")).toBe(true);
    expect(nameLooksLikeWater("WEB_man_made_water_tower_1")).toBe(false);
    expect(nameLooksLikeWater("WEB_man_made_water_well_1")).toBe(false);
    expect(nameLooksLikeWater("WEB_man_made_wastewater_plant_1")).toBe(false);
    expect(nameLooksLikeWater("WEB_man_made_breakwater_1")).toBe(false);
    expect(nameLooksLikeWater("building")).toBe(false);
    expect(waterCategoryFromName("WEB_water")).toBe("sea");
    expect(waterCategoryFromName("WEB_bay")).toBe("sea");
    expect(waterCategoryFromName("WEB_rivers")).toBe("river");
    expect(waterCategoryFromName("WEB_lake")).toBe("lake");
  });

  it("detects water-like meshes via parent node or Water material", () => {
    const sea = makeWaterNode("WEB_water", 100, 100, 0, 0);
    expect(isWaterLikeMesh(sea.mesh)).toBe(true);
    const building = new THREE.Mesh(
      new THREE.BoxGeometry(4, 8, 4),
      new THREE.MeshStandardMaterial({ name: "building" }),
    );
    building.name = "Mesh.building";
    expect(isWaterLikeMesh(building)).toBe(false);
  });
});

describe("Odessa duplicate water guard", () => {
  it("hides overlapping sea/bay duplicates and keeps the canonical WEB_water", () => {
    const water = makeWaterNode("WEB_water", 600, 900, 0, -100);
    const bay = makeWaterNode("WEB_bay", 400, 480, 80, 40);
    const scene = new THREE.Group();
    scene.add(water.group, bay.group);
    scene.updateMatrixWorld(true);

    const dup = findDuplicateWaterMeshes([water.mesh, bay.mesh]);
    expect(dup.get(water.mesh)?.hide).toBe(false);
    expect(dup.get(bay.mesh)?.hide).toBe(true);

    const result = applyWaterSurfaceGuard([scene]);
    expect(result.meshCount).toBe(2);
    expect(result.duplicatesHidden).toBe(1);
    expect(water.mesh.visible).toBe(true);
    expect(bay.mesh.visible).toBe(false);
  });

  it("preserves spatially distinct rivers, lakes, and non-water meshes", () => {
    const water = makeWaterNode("WEB_water", 600, 900, 0, -100);
    const rivers = makeWaterNode("WEB_rivers", 500, 500, -40, 20);
    const lake = makeWaterNode("WEB_lake", 30, 24, 2000, 2000);
    const building = new THREE.Mesh(
      new THREE.BoxGeometry(6, 12, 6),
      new THREE.MeshStandardMaterial({ name: "building", color: 0x888888 }),
    );
    building.name = "Mesh.building";
    building.position.set(10, 6, 10);
    const scene = new THREE.Group();
    scene.add(water.group, rivers.group, lake.group, building);
    scene.updateMatrixWorld(true);

    const result = applyWaterSurfaceGuard([scene]);
    expect(result.meshCount).toBe(3);
    expect(water.mesh.visible).toBe(true);
    expect(rivers.mesh.visible).toBe(true);
    expect(lake.mesh.visible).toBe(true);
    expect(building.visible).toBe(true);
    expect(result.records.find((r) => r.category === "river")?.hiddenAsDuplicate).toBe(false);
    expect(result.records.find((r) => r.category === "lake")?.hiddenAsDuplicate).toBe(false);
  });

  it("stabilizes Water material: no mirror specular, opaque, FrontSide, depthWrite", () => {
    const mat = new THREE.MeshStandardMaterial({
      name: "Water",
      metalness: 0.5,
      roughness: 0,
      transparent: false,
      side: THREE.DoubleSide,
    });
    stabilizeWaterMaterial(mat);
    expect(mat.metalness).toBe(0);
    expect(mat.roughness).toBeGreaterThanOrEqual(0.6);
    expect(mat.transparent).toBe(false);
    expect(mat.depthWrite).toBe(true);
    expect(mat.depthTest).toBe(true);
    expect(mat.side).toBe(THREE.FrontSide);
    expect(mat.envMap).toBeNull();
  });

  it("does not scan or hide buildings that share a tile with water", () => {
    const water = makeWaterNode("WEB_water", 200, 200, 0, 0);
    const house = new THREE.Mesh(
      new THREE.BoxGeometry(8, 10, 8),
      new THREE.MeshStandardMaterial({ name: "building" }),
    );
    const tile = new THREE.Group();
    tile.add(water.group, house);
    applyWaterSurfaceGuard([tile]);
    expect(house.visible).toBe(true);
    expect((house.material as THREE.MeshStandardMaterial).name).toBe("building");
  });
});
