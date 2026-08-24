/**
 * STEP 28 — pick registry, deterministic IDs, highlight isolation, entity binding.
 */

import { describe, expect, it, beforeEach } from "vitest";
import * as THREE from "three";
import { PickRegistry } from "./pickRegistry";
import { makePickId } from "./pickIds";
import { bindPickableFromLookup, collectExactBuildingIds } from "./entityBinding";
import { HighlightController, HOVER_EMISSIVE, HOVER_HIGHLIGHT_HEX, SELECT_EMISSIVE } from "./highlightController";
import { isInteractivePickMesh } from "./pickFilter";
import { NO_DATA, objectPanelFacts } from "./objectPanelFacts";
import { isClickGesture, exceedsDragThreshold, CLICK_DRAG_THRESHOLD_PX } from "./pointerGesture";
import { auditSceneGraph } from "./sceneAudit";
import { seedPlatformBuildingEntities, clearCityEntities } from "../cityEntityRegistry";
import { easeOutCubic, createFocusTween, applyFocusTween, focusPoseForObject } from "./focusCamera";

function buildingMesh(name: string, material: THREE.Material): THREE.Mesh {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(4, 8, 4), material);
  mesh.name = name;
  return mesh;
}

function assetRoot(id: string, meshes: THREE.Mesh[]): THREE.Group {
  const root = new THREE.Group();
  root.name = id;
  for (const m of meshes) root.add(m);
  return root;
}

describe("pick IDs", () => {
  it("are deterministic for the same asset + mesh order + name", () => {
    expect(makePickId("TILE_02_00", 0, "Mesh.building")).toBe(makePickId("TILE_02_00", 0, "Mesh.building"));
    expect(makePickId("TILE_02_00", 0, "Mesh.building")).not.toBe(makePickId("TILE_02_00", 1, "Mesh.building"));
    expect(makePickId("a", 0, "")).toMatch(/^pick:a:0:unnamed$/);
  });
});

describe("PickRegistry", () => {
  it("registers meshes, skips water, and rejects duplicate asset registration", () => {
    const scene = new THREE.Scene();
    const shared = new THREE.MeshStandardMaterial({ name: "facade" });
    const a = buildingMesh("house_a", shared);
    const b = buildingMesh("house_b", shared);
    const water = new THREE.Mesh(
      new THREE.PlaneGeometry(10, 10),
      new THREE.MeshStandardMaterial({ name: "Water" }),
    );
    water.name = "WEB_water";
    const root = assetRoot("TILE_01", [a, b, water]);
    scene.add(root);

    const reg = new PickRegistry();
    expect(reg.registerAsset({ assetId: "TILE_01", root, layerId: "city" })).toBe(2);
    expect(reg.size()).toBe(2);
    const again = reg.registerAsset({ assetId: "TILE_01", root, layerId: "city" });
    expect(again).toBe(2);
    expect(reg.size()).toBe(2);

    const ids = reg.list().map((e) => e.pickId);
    expect(new Set(ids).size).toBe(ids.length);
    expect(reg.list().every((e) => e.assetId === "TILE_01")).toBe(true);
    expect(reg.list().some((e) => e.meshName === "WEB_water")).toBe(false);
  });

  it("unregisters on unload and does not retain disposed objects", () => {
    const scene = new THREE.Scene();
    const mesh = buildingMesh("b1", new THREE.MeshStandardMaterial());
    const root = assetRoot("TILE_X", [mesh]);
    scene.add(root);
    const reg = new PickRegistry();
    reg.registerAsset({ assetId: "TILE_X", root });
    const pickId = reg.list()[0].pickId;
    expect(reg.getObject(pickId)).toBe(mesh);

    scene.remove(root);
    mesh.geometry.dispose();
    reg.unregisterAsset("TILE_X");
    expect(reg.size()).toBe(0);
    expect(reg.get(pickId)).toBeUndefined();
    expect(reg.getObject(pickId)).toBeUndefined();
  });

  it("rebuilds cleanly after a 2D/3D remount-style clear", () => {
    const mesh = buildingMesh("b1", new THREE.MeshStandardMaterial());
    const root = assetRoot("TILE_R", [mesh]);
    const scene = new THREE.Scene();
    scene.add(root);
    const reg = new PickRegistry();
    reg.registerAsset({ assetId: "TILE_R", root });
    const firstId = reg.list()[0].pickId;
    reg.clear();
    expect(reg.size()).toBe(0);
    reg.registerAsset({ assetId: "TILE_R", root });
    expect(reg.size()).toBe(1);
    expect(reg.list()[0].pickId).toBe(firstId);
  });
});

describe("click vs drag", () => {
  it("uses a movement threshold so orbit/pan does not select", () => {
    const down = { x: 10, y: 10 };
    expect(isClickGesture(down, { x: 12, y: 11 })).toBe(true);
    expect(isClickGesture(down, { x: 10 + CLICK_DRAG_THRESHOLD_PX + 1, y: 10 })).toBe(false);
    expect(isClickGesture(down, { x: 11, y: 11 }, true)).toBe(false);
    expect(exceedsDragThreshold(down, { x: 30, y: 30 })).toBe(true);
  });
});

describe("shared-material highlight isolation", () => {
  it("clones only the target mesh material", () => {
    const shared = new THREE.MeshStandardMaterial({ color: 0x8899aa, name: "shared_facade" });
    const a = buildingMesh("a", shared);
    const b = buildingMesh("b", shared);
    const hl = new HighlightController();
    hl.setHover(a);
    expect(a.material).not.toBe(shared);
    expect(b.material).toBe(shared);
    expect(hl.materialCloneCount()).toBe(1);
    const hoverMat = a.material as THREE.MeshStandardMaterial;
    expect(hoverMat.emissiveIntensity).toBeLessThanOrEqual(0.12);
    expect(hoverMat.emissiveIntensity).toBe(HOVER_EMISSIVE);
    expect(hoverMat.emissive.getHex()).toBe(HOVER_HIGHLIGHT_HEX);
    expect(SELECT_EMISSIVE).toBeLessThan(0.25);
    hl.setSelected(b);
    expect(b.material).not.toBe(shared);
    expect((a.material as THREE.MeshStandardMaterial).uuid).not.toBe(shared.uuid);
    hl.clearAll();
    expect(a.material).toBe(shared);
    expect(b.material).toBe(shared);
    expect(hl.materialCloneCount()).toBe(0);
  });

  it("selected style replaces hover on the same mesh", () => {
    const mat = new THREE.MeshStandardMaterial({ color: 0x445566 });
    const mesh = buildingMesh("only", mat);
    const hl = new HighlightController();
    hl.setHover(mesh);
    hl.setSelected(mesh);
    expect(mesh.material).not.toBe(mat);
    hl.clearAll();
    expect(mesh.material).toBe(mat);
  });
});

describe("entity binding", () => {
  beforeEach(() => {
    clearCityEntities();
    seedPlatformBuildingEntities();
  });

  it("returns UNBOUND when no exact mapping exists", () => {
    const r = bindPickableFromLookup({
      pickId: "pick:TILE_02_00:0:Mesh_123",
      assetId: "TILE_02_00",
      meshName: "Mesh.123",
    });
    expect(r.status).toBe("UNBOUND");
    expect(r.label).toBeUndefined();
    expect(r.reasons).toContain("no_exact_entity_mapping");
  });

  it("returns BOUND only on exact catalog id", () => {
    const r = bindPickableFromLookup({
      pickId: "pick:crm:0:crm",
      assetId: "crm",
      meshName: "other",
    });
    expect(r.status).toBe("BOUND");
    expect(r.buildingId).toBe("crm");
    expect(r.label).toBe("CRM Center");
    expect(r.route).toBe("/crm");
  });

  it("returns AMBIGUOUS on conflicting exact ids", () => {
    const r = bindPickableFromLookup({
      pickId: "pick:x:0:y",
      assetId: "crm",
      meshName: "hub",
    });
    expect(r.status).toBe("AMBIGUOUS");
    expect(collectExactBuildingIds({ pickId: "p", assetId: "crm", meshName: "hub" }).sort()).toEqual(["crm", "hub"]);
  });

  it("never fuzzy-matches tile names to buildings", () => {
    const r = bindPickableFromLookup({
      pickId: "pick:crm_tile:0:x",
      assetId: "crm_tile",
      meshName: "crm_building_like",
    });
    expect(r.status).toBe("UNBOUND");
  });
});

describe("scene audit", () => {
  it("counts meshes, names, shared materials, and asset userData", () => {
    const shared = new THREE.MeshStandardMaterial({ name: "s" });
    const a = buildingMesh("named", shared);
    a.userData.odessaAssetId = "TILE_A";
    const b = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), shared);
    b.userData.odessaAssetId = "TILE_A";
    const root = new THREE.Group();
    root.add(a, b);
    const audit = auditSceneGraph(root);
    expect(audit.meshCount).toBe(2);
    expect(audit.namedMeshCount).toBe(1);
    expect(audit.unnamedMeshCount).toBe(1);
    expect(audit.meshesByAsset.TILE_A).toBe(2);
    expect(audit.materialsReused).toBe(1);
    expect(audit.meshesWithAssetId).toBe(2);
  });
});

describe("selection / hover IDs", () => {
  it("tracks hover then selection without storing Three objects in the snapshot shape", () => {
    let hovered: string | null = null;
    let selected: string | null = null;
    const setHover = (id: string | null) => {
      if (hovered === id) return false;
      hovered = id;
      return true;
    };
    const setSelect = (id: string | null) => {
      selected = id;
    };
    expect(setHover("pick:a:0:x")).toBe(true);
    expect(setHover("pick:a:0:x")).toBe(false);
    expect(setHover("pick:a:1:y")).toBe(true);
    setSelect("pick:a:1:y");
    setSelect(null);
    expect(hovered).toBe("pick:a:1:y");
    expect(selected).toBeNull();
  });
});

describe("interactive pick whitelist", () => {
  it("rejects sea, ground, roads, vegetation, and city-scale merges", () => {
    const mk = (name: string, w: number, h: number, d: number, cls?: string) => {
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial());
      mesh.name = name;
      if (cls) mesh.userData.odessaMaterialClass = cls;
      mesh.updateMatrixWorld(true);
      return mesh;
    };
    expect(isInteractivePickMesh(mk("WEB_water", 200, 0.2, 200)).ok).toBe(false);
    expect(isInteractivePickMesh(mk("WEB_base", 600, 0.1, 600)).ok).toBe(false);
    expect(isInteractivePickMesh(mk("OSM_roads_1", 80, 0.3, 80)).ok).toBe(false);
    expect(isInteractivePickMesh(mk("park_trees", 20, 8, 20, "VEGETATION")).ok).toBe(false);
    expect(isInteractivePickMesh(mk("merged_district", 1200, 20, 900)).reason).toBe("city-scale-merge");
    expect(isInteractivePickMesh(mk("WEB_height_12", 18, 14, 16)).ok).toBe(true);
    expect(isInteractivePickMesh(mk("house_a", 8, 10, 8, "BUILDING")).ok).toBe(true);
  });
});

describe("object panel facts", () => {
  it("falls back to Нет данных without throwing", () => {
    const facts = objectPanelFacts(
      {
        pickId: "pick:x:0:unnamed",
        assetId: "TILE",
        objectUuid: "u",
        bindingStatus: "UNBOUND",
      },
      { status: "UNBOUND", pickId: "pick:x:0:unnamed", assetId: "TILE", reasons: [] },
    );
    expect(facts.name).toBe(NO_DATA);
    expect(facts.type).toBe(NO_DATA);
    expect(facts.position.x).toBe(NO_DATA);
    expect(facts.size.y).toBe(NO_DATA);
  });

  it("prefers metadata name and reports XYZ / size", () => {
    const facts = objectPanelFacts(
      {
        pickId: "pick:t:0:b",
        assetId: "TILE",
        objectUuid: "u",
        meshName: "Mesh.1",
        displayName: "Дом на Дерибасовской",
        classification: "BUILDING",
        bindingStatus: "UNBOUND",
        position: { x: 10, y: 5, z: -3 },
        size: { x: 12, y: 14, z: 8 },
      },
      { status: "UNBOUND", pickId: "pick:t:0:b", assetId: "TILE", reasons: [] },
    );
    expect(facts.name).toBe("Дом на Дерибасовской");
    expect(facts.type).toBe("BUILDING");
    expect(facts.position.y).toBe("5.00");
    expect(facts.size.x).toBe("12.00");
  });
});

describe("focus pose", () => {
  it("keeps the camera outside the object AABB", () => {
    const mesh = buildingMesh("focus", new THREE.MeshStandardMaterial());
    mesh.position.set(0, 4, 0);
    mesh.updateMatrixWorld(true);
    const camera = new THREE.PerspectiveCamera(50, 1, 0.5, 4000);
    camera.position.set(40, 30, 40);
    camera.lookAt(0, 0, 0);
    const pose = focusPoseForObject(mesh, camera);
    const box = new THREE.Box3().setFromObject(mesh);
    expect(box.containsPoint(pose.position)).toBe(false);
    expect(pose.position.y).toBeGreaterThan(box.max.y);
    expect(easeOutCubic(0)).toBe(0);
    expect(easeOutCubic(1)).toBe(1);
    const tween = createFocusTween(0, camera.position, pose.position, new THREE.Vector3(), pose.target, 100);
    const done = applyFocusTween(tween, 100, camera, new THREE.Vector3());
    expect(done).toBe(true);
  });
});
