import { beforeEach, describe, expect, it } from "vitest";
import { readFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";
import { AssetRegistry } from "./assetRegistry";
import { LayerManager } from "./layerManager";
import { manifestAssetEntries, manifestProgress } from "./odessaManifest";
import { resolvePublicAssetUrl } from "./publicAssetUrl";
import {
  readQualityProfile,
  readViewMode,
  resolveQuality,
  writeQualityProfile,
  writeViewMode,
} from "./qualityProfile";
import { adaptBlenderManifest, parseOdessaManifestJson } from "./manifestAdapter";
import {
  blenderBoundsToCity,
  normalizeAssetUrl,
  validateBlenderManifest,
  type BlenderWebManifest,
} from "./blenderManifest";
import type { OdessaManifest } from "./types";

const RUNTIME_MANIFEST_PATH = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../../../public/assets/odessa/odessa_manifest.json",
);
const PUBLIC_ODESSA = resolve(dirname(fileURLToPath(import.meta.url)), "../../../public/assets/odessa");

function glbMagicOk(path: string): boolean {
  const head = readFileSync(path).subarray(0, 4);
  return head.toString("utf8") === "glTF";
}

describe("Interactive City Odessa 3D core", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("deduplicates assets by id and url", () => {
    const reg = new AssetRegistry();
    const first = reg.register({ id: "x", url: "/assets/odessa/glb/x.glb" });
    expect(reg.register({ id: "x", url: "/assets/odessa/other.glb" })).toBe(first);
    expect(reg.register({ id: "y", url: "/assets/odessa/glb/x.glb" })).toBe(first);
    expect(reg.list()).toHaveLength(1);
  });

  it("resolves canonical public asset URLs", () => {
    expect(resolvePublicAssetUrl("/assets/odessa/TILE_02_00.glb")).toBe("/assets/odessa/TILE_02_00.glb");
    expect(resolvePublicAssetUrl("FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_03.glb")).toBe(
      "/assets/odessa/FINAL_TILE_04_REST/TILE_04_00_REST_BATCH_03.glb",
    );
    expect(() => resolvePublicAssetUrl("/Users/macbook/x.glb")).toThrow();
  });

  it("maps Blender bounds to Three.js city bounds", () => {
    const city = blenderBoundsToCity({
      min_x: -10,
      max_x: 10,
      min_y: -20,
      max_y: 20,
      min_z: 0,
      max_z: 2,
    });
    expect(city.maxZ).toBe(20);
    expect(city.maxY).toBe(2);
  });

  it("validates duplicate ids in Blender manifest", () => {
    const bad: BlenderWebManifest = {
      name: "x",
      version: 1,
      assets: [
        { id: "a", type: "top_level_tile", url: "/assets/odessa/a.glb" },
        { id: "a", type: "top_level_tile", url: "/assets/odessa/b.glb" },
      ],
    };
    expect(validateBlenderManifest(bad)).toContain("duplicate_id:a");
  });

  it("loads copied runtime manifest with 45 assets", () => {
    const raw = JSON.parse(readFileSync(RUNTIME_MANIFEST_PATH, "utf8")) as BlenderWebManifest;
    expect(raw.assets).toHaveLength(45);
    expect(validateBlenderManifest(raw)).toEqual([]);
    const manifest = parseOdessaManifestJson(raw);
    expect(manifest.tiles).toHaveLength(45);
    expect(manifest.geoTransform.calibrated).toBe(false);
  });

  it("maps every manifest URL to an existing GLB with glTF magic", () => {
    const raw = JSON.parse(readFileSync(RUNTIME_MANIFEST_PATH, "utf8")) as BlenderWebManifest;
    for (const a of raw.assets) {
      const url = a.url || normalizeAssetUrl(a.path || "");
      const rel = url.replace("/assets/odessa/", "");
      const fp = resolve(PUBLIC_ODESSA, rel);
      expect(fp).toBeTruthy();
      const stat = readFileSync(fp);
      expect(stat.byteLength).toBeGreaterThan(0);
      expect(glbMagicOk(fp)).toBe(true);
    }
  });

  it("persists view mode and quality profile", () => {
    writeViewMode("3d");
    writeQualityProfile("low");
    expect(readViewMode()).toBe("3d");
    expect(readQualityProfile()).toBe("low");
    expect(resolveQuality("low").maxConcurrentLoads).toBe(1);
    expect(resolveQuality("low").pixelRatioCap).toBe(1);
    expect(resolveQuality("medium").pixelRatioCap).toBe(1.25);
  });

  it("2D → 3D → 2D view-mode roundtrip stays stable", () => {
    writeViewMode("2d");
    expect(readViewMode()).toBe("2d");
    writeViewMode("3d");
    expect(readViewMode()).toBe("3d");
    writeViewMode("2d");
    expect(readViewMode()).toBe("2d");
  });

  it("manifest progress tracks loaded and failed separately", () => {
    const p = manifestProgress(45, 2, 1, 3, 0, { realGlbLoaded: 2, loadedMb: 16, totalMb: 382 });
    expect(p.percent).toBeGreaterThan(0);
    expect(p.realGlbLoaded).toBe(2);
  });
});
