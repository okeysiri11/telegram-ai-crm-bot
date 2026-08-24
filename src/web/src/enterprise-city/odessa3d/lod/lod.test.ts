import { afterEach, describe, expect, it } from "vitest";
import * as THREE from "three";
import { readFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";
import {
  classifyDistanceTier,
  classifyDistanceTierHysteresis,
  isInventedLodUrl,
  isSeaOrCoastProtected,
  lodThresholdsFor,
  LodVisibilityManager,
  resolveRuntimeAssetUrl,
  scoreLodPriority,
  screenSpaceImportance,
  shouldAssetBeVisible,
  starveBoost,
} from "./index";
import { cacheManifestCenter, clearBoundsCache, getCachedCenter } from "../assetBoundsCache";
import { ProgressiveSceneActivator } from "../progressiveActivator";
import { writeViewMode, readViewMode, resolveQuality } from "../qualityProfile";
import { parseOdessaManifestJson } from "../manifestAdapter";
import type { CityAsset } from "../types";

const RUNTIME_MANIFEST_PATH = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../../../../public/assets/odessa/odessa_manifest.json",
);

afterEach(() => {
  clearBoundsCache();
  writeViewMode("2d");
});

const mediumT = lodThresholdsFor("medium", 1400, 1);

describe("distance tier classification", () => {
  it("maps NEAR / MID / FAR / CULL from distance", () => {
    expect(classifyDistanceTier(80, mediumT)).toBe("NEAR");
    expect(classifyDistanceTier(mediumT.nearM + 40, mediumT)).toBe("MID");
    expect(classifyDistanceTier(mediumT.midM + 40, mediumT)).toBe("FAR");
    expect(classifyDistanceTier(mediumT.farM + 40, mediumT)).toBe("CULL");
  });
});

describe("LOD hysteresis", () => {
  it("does not demote NEAR until past the outer band", () => {
    const edge = mediumT.nearM * 1.1;
    expect(classifyDistanceTier(edge, mediumT)).toBe("MID");
    expect(classifyDistanceTierHysteresis(edge, mediumT, "NEAR")).toBe("NEAR");
    expect(classifyDistanceTierHysteresis(mediumT.nearM * 1.3, mediumT, "NEAR")).toBe("MID");
  });

  it("tiny camera movement does not flip FAR visibility", () => {
    expect(mediumT.hysteresis).toBeGreaterThanOrEqual(0.24);
    const d = mediumT.farM;
    const base = {
      id: "HEAVY_X",
      layerId: "heavy",
      inFrustum: false,
      nearTarget: false,
      seaProtected: false,
      screenImportant: false,
      currentlyVisible: true,
    };
    expect(shouldAssetBeVisible({ ...base, distanceM: d }, mediumT)).toBe(true);
    expect(shouldAssetBeVisible({ ...base, distanceM: d * (1 + mediumT.hysteresis * 0.4) }, mediumT)).toBe(true);
    expect(classifyDistanceTierHysteresis(mediumT.farM * 1.05, mediumT, "FAR")).toBe("FAR");
  });
});

describe("screen-space importance", () => {
  it("treats a large nearby radius as more important than the same radius far away", () => {
    const near = screenSpaceImportance(200, 120, 50, 720);
    const far = screenSpaceImportance(200, 2400, 50, 720);
    expect(near).toBeGreaterThan(far);
    expect(near).toBeGreaterThan(0.08);
    expect(far).toBeLessThan(near * 0.2);
  });
});

describe("frustum and target protection", () => {
  it("prioritizes frustum and look-at protection over equal distance", () => {
    const base = {
      distanceM: 600,
      inFrustum: false,
      nearTarget: false,
      manifestPriority: false,
      seaProtected: false,
      screenImportant: false,
    };
    expect(scoreLodPriority({ ...base, inFrustum: true })).toBeLessThan(scoreLodPriority(base));
    expect(scoreLodPriority({ ...base, nearTarget: true })).toBeLessThan(scoreLodPriority(base));
  });

  it("keeps look-at assets visible even when far/heavy", () => {
    expect(
      shouldAssetBeVisible(
        {
          id: "HEAVY_X",
          layerId: "heavy",
          distanceM: 4000,
          inFrustum: false,
          nearTarget: true,
          seaProtected: false,
          screenImportant: false,
          currentlyVisible: false,
        },
        mediumT,
      ),
    ).toBe(true);
  });
});

describe("sea protection", () => {
  it("protects WEB_water tile and river/bay ids", () => {
    expect(isSeaOrCoastProtected("TILE_04_00_REST_BATCH_07")).toBe(true);
    expect(isSeaOrCoastProtected("TILE_03_00")).toBe(true);
    expect(isSeaOrCoastProtected("TILE_05_00")).toBe(true);
    expect(isSeaOrCoastProtected("HEAVY_BUILDING_CHUNK_00_02", "heavy")).toBe(false);
    expect(
      shouldAssetBeVisible(
        {
          id: "TILE_04_00_REST_BATCH_07",
          layerId: "city",
          distanceM: 8000,
          inFrustum: false,
          nearTarget: false,
          seaProtected: true,
          screenImportant: false,
          currentlyVisible: true,
        },
        mediumT,
      ),
    ).toBe(true);
  });
});

describe("starvation prevention", () => {
  it("gives a bounded boost so similar-distance waiters are not stuck forever", () => {
    expect(starveBoost(0)).toBe(0);
    expect(starveBoost(25_000)).toBeGreaterThan(starveBoost(1000));
    expect(starveBoost(99_000)).toBe(420);
    const fresh = scoreLodPriority({
      distanceM: 700,
      inFrustum: false,
      nearTarget: false,
      manifestPriority: false,
      seaProtected: false,
      screenImportant: false,
      waitMs: 0,
    });
    const waiting = scoreLodPriority({
      distanceM: 740,
      inFrustum: false,
      nearTarget: false,
      manifestPriority: false,
      seaProtected: false,
      screenImportant: false,
      waitMs: 25_000,
    });
    expect(waiting).toBeLessThan(fresh);
    const near = scoreLodPriority({
      distanceM: 120,
      inFrustum: true,
      nearTarget: true,
      manifestPriority: false,
      seaProtected: false,
      screenImportant: false,
      waitMs: 0,
    });
    expect(near).toBeLessThan(waiting);
  });
});

describe("quality profiles", () => {
  it("LOW uses a smaller NEAR radius than HIGH and lodBias stays on presets", () => {
    const low = lodThresholdsFor("low", 1400);
    const high = lodThresholdsFor("high", 1400);
    expect(low.nearM).toBeLessThan(high.nearM);
    expect(low.farM).toBeLessThan(high.farM);
    expect(resolveQuality("low").lodBias).toBeGreaterThan(resolveQuality("high").lodBias);
  });
});

describe("bounding cache", () => {
  it("evaluates from cached manifest centers without measuring Box3", () => {
    cacheManifestCenter("TILE_X", { minX: -20, maxX: 20, minZ: -10, maxZ: 10, minY: 0, maxY: 4 });
    expect(getCachedCenter("TILE_X")).toEqual({ x: 0, y: 2, z: 0 });
    const mgr = new LodVisibilityManager();
    const decisions = mgr.evaluate(
      [{ id: "TILE_X", layerId: "city", currentlyVisible: true, bounds: { minX: -20, maxX: 20, minZ: -10, maxZ: 10 } }],
      {
        camX: 0,
        camZ: 0,
        targetX: 0,
        targetZ: 0,
        inFrustum: () => true,
        fovYDeg: 50,
        viewportHeight: 600,
        profile: "medium",
        cityDiagonalM: 1400,
        lodBias: 1,
      },
    );
    expect(decisions[0].visible).toBe(true);
    expect(mgr.diagnostics().boundsMs).toBeGreaterThanOrEqual(0);
    mgr.dispose();
  });
});

describe("priority ordering", () => {
  it("orders sea + near-frustum ahead of distant heavy", () => {
    const sea = scoreLodPriority({
      distanceM: 900,
      inFrustum: true,
      nearTarget: false,
      manifestPriority: true,
      seaProtected: true,
      screenImportant: false,
      layerId: "city",
    });
    const heavy = scoreLodPriority({
      distanceM: 400,
      inFrustum: false,
      nearTarget: false,
      manifestPriority: false,
      seaProtected: false,
      screenImportant: false,
      layerId: "heavy",
      heavyClass: "EXTREME",
      sizeMb: 24,
    });
    expect(sea).toBeLessThan(heavy);
  });
});

describe("progressive activation ordering", () => {
  it("activates a near city tile before a far heavy one in one IDLE tick", () => {
    const act = new ProgressiveSceneActivator();
    const near = stub("NEAR_CITY", { layerId: "city", bounds: { minX: -8, maxX: 8, minZ: -8, maxZ: 8 } });
    const far = stub("FAR_HEAVY", {
      layerId: "heavy",
      triangleCount: 600_000,
      heavyClass: "HEAVY",
      bounds: { minX: 3800, maxX: 3900, minZ: 3800, maxZ: 3900 },
    });
    act.ingest(near);
    act.ingest(far);
    const attached: string[] = [];
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 8000);
    camera.position.set(0, 40, 80);
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld();
    const frustum = new THREE.Frustum();
    frustum.setFromProjectionMatrix(
      new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse),
    );
    act.tick(
      {
        now: 0,
        mode: "IDLE",
        fps: 60,
        camera,
        target: new THREE.Vector3(0, 0, 0),
        frustum,
        priorityIds: new Set(),
        enableShadows: false,
        maxAnisotropy: 1,
      },
      (info) => attached.push(info.asset.id),
    );
    expect(attached[0]).toBe("NEAR_CITY");
    act.disposeAll();
  });
});

describe("2D/3D remount and disposal", () => {
  it("disposes LOD state and remounts without leftover tiers", () => {
    writeViewMode("3d");
    const mgr = new LodVisibilityManager();
    cacheManifestCenter("A", { minX: 0, maxX: 10, minZ: 0, maxZ: 10 });
    mgr.evaluate([{ id: "A", layerId: "heavy", currentlyVisible: true }], {
      camX: 0,
      camZ: 0,
      targetX: 0,
      targetZ: 0,
      inFrustum: () => false,
      fovYDeg: 50,
      viewportHeight: 600,
      profile: "low",
      cityDiagonalM: 1400,
      lodBias: 2,
    });
    mgr.dispose();
    expect(mgr.diagnostics().visible).toBe(0);
    writeViewMode("2d");
    writeViewMode("3d");
    const again = new LodVisibilityManager();
    expect(again.diagnostics().near).toBe(0);
    again.dispose();
    writeViewMode("2d");
    expect(readViewMode()).toBe("2d");
  });
});

describe("no invented LOD URLs", () => {
  it("never rewrites manifest URLs and rejects _lod sibling paths", () => {
    const json = JSON.parse(readFileSync(RUNTIME_MANIFEST_PATH, "utf8"));
    const manifest = parseOdessaManifestJson(json);
    for (const tile of manifest.tiles) {
      for (const asset of tile.assets) {
        expect(resolveRuntimeAssetUrl(asset.url)).toBe(asset.url);
        expect(isInventedLodUrl(asset.url)).toBe(false);
      }
    }
    expect(isInventedLodUrl("/assets/odessa/TILE_02_00_lod2.glb")).toBe(true);
    expect(isInventedLodUrl("/assets/odessa/lod1/TILE_02_00.glb")).toBe(true);
  });
});

describe("city holes", () => {
  it("never hides city-layer assets for distance alone", () => {
    expect(
      shouldAssetBeVisible(
        {
          id: "TILE_02_00",
          layerId: "city",
          distanceM: 9000,
          inFrustum: false,
          nearTarget: false,
          seaProtected: false,
          screenImportant: false,
          currentlyVisible: true,
        },
        mediumT,
      ),
    ).toBe(true);
  });
});

function stub(id: string, patch: Partial<CityAsset> = {}): CityAsset {
  const root = new THREE.Group();
  root.add(new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2), new THREE.MeshStandardMaterial()));
  return {
    id,
    url: `/assets/odessa/${id}.glb`,
    status: "loaded",
    source: "REAL_GLB",
    lifecycle: "parsed",
    object3D: root,
    tileId: id,
    layerId: "city",
    triangleCount: 80,
    ...patch,
    object3D: patch.object3D ?? root,
  };
}
