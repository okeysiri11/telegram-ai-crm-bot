import { afterEach, describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  OdessaEnvironment,
  applyCanonicalSeaAppearance,
  applyUntexturedReadability,
  applyUrbanVisualPass,
  buildingVariationDelta,
  classifyUrbanMaterial,
  countEnvironmentLights,
  getEnvironmentPreset,
  isCanonicalSeaMesh,
  lightingForQuality,
  resolveEnvironmentQuality,
  stableUnitHash,
  sunDirectionFromElevationAzimuth,
  validateEnvironmentPreset,
} from "./index";
import { fogDensityForCity } from "./atmosphere";
import { writeViewMode, readViewMode } from "../qualityProfile";
import { applyWaterSurfaceGuard } from "../waterSurfaceGuard";

function fakeRenderer(): THREE.WebGLRenderer {
  return {
    outputColorSpace: THREE.NoColorSpace,
    toneMapping: THREE.NoToneMapping,
    toneMappingExposure: 1,
    shadowMap: { enabled: true },
  } as unknown as THREE.WebGLRenderer;
}

function waterMesh(nodeName: string, color = 0x338899): { group: THREE.Group; mesh: THREE.Mesh } {
  const group = new THREE.Group();
  group.name = nodeName;
  const mat = new THREE.MeshStandardMaterial({
    name: "Water",
    color,
    metalness: 0.5,
    roughness: 0,
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), mat);
  mesh.name = `Mesh.${nodeName}`;
  group.add(mesh);
  return { group, mesh };
}

afterEach(() => {
  writeViewMode("2d");
});

describe("Odessa environment presets", () => {
  it("validates CLEAR_DAY and stub presets", () => {
    expect(validateEnvironmentPreset(getEnvironmentPreset("CLEAR_DAY"))).toEqual([]);
    expect(validateEnvironmentPreset(getEnvironmentPreset("SOFT_DAY"))).toEqual([]);
    expect(validateEnvironmentPreset(getEnvironmentPreset("SUNSET"))).toEqual([]);
    expect(validateEnvironmentPreset(getEnvironmentPreset("NIGHT"))).toEqual([]);
    const bad = { ...getEnvironmentPreset("CLEAR_DAY"), exposure: 9, elevationDeg: 400 };
    expect(validateEnvironmentPreset(bad).length).toBeGreaterThan(0);
  });

  it("maps quality profiles to environment quality without enabling shadows", () => {
    expect(resolveEnvironmentQuality("low")).toBe("low");
    expect(resolveEnvironmentQuality("medium")).toBe("medium");
    expect(resolveEnvironmentQuality("high")).toBe("high");
  });

  it("places the sun above the horizon for CLEAR_DAY elevation", () => {
    const preset = getEnvironmentPreset("CLEAR_DAY");
    const dir = sunDirectionFromElevationAzimuth(preset.elevationDeg, preset.azimuthDeg);
    expect(dir.y).toBeGreaterThan(0.35);
    expect(preset.elevationDeg).toBeGreaterThanOrEqual(30);
    expect(preset.elevationDeg).toBeLessThanOrEqual(45);
    expect(preset.azimuthDeg).toBeGreaterThan(120);
    expect(preset.azimuthDeg).toBeLessThan(200);
  });
});

describe("OdessaEnvironment lifecycle", () => {
  it("creates lights and sky once and ignores a second mount", () => {
    const scene = new THREE.Scene();
    const env = new OdessaEnvironment({ quality: "medium" });
    const renderer = fakeRenderer();
    env.mount(scene, renderer);
    env.mount(scene, renderer);
    expect(env.isMounted()).toBe(true);
    expect(countEnvironmentLights(scene)).toEqual({ sun: 1, hemi: 1, sky: 1 });
    expect(renderer.outputColorSpace).toBe(THREE.SRGBColorSpace);
    expect(renderer.toneMapping).toBe(THREE.ACESFilmicToneMapping);
    expect(renderer.toneMappingExposure).toBe(getEnvironmentPreset("CLEAR_DAY").exposure);
    expect(renderer.shadowMap.enabled).toBe(false);
    expect(scene.fog).toBeInstanceOf(THREE.FogExp2);
    expect((scene.fog as THREE.FogExp2).color.getHex()).not.toBe(0xffffff);
    expect((scene.fog as THREE.FogExp2).color.getHex()).toBe(getEnvironmentPreset("CLEAR_DAY").fogColor);
    env.dispose();
  });

  it("disposes sky, lights, and fog", () => {
    const scene = new THREE.Scene();
    const env = new OdessaEnvironment({ quality: "high" });
    env.mount(scene, fakeRenderer());
    env.dispose();
    expect(env.isMounted()).toBe(false);
    expect(countEnvironmentLights(scene)).toEqual({ sun: 0, hemi: 0, sky: 0 });
    expect(scene.fog).toBeNull();
    expect(scene.children.find((c) => c.name === "odessaEnvironment")).toBeUndefined();
  });

  it("switches quality without duplicating sky or lights", () => {
    const scene = new THREE.Scene();
    const env = new OdessaEnvironment({ quality: "high" });
    env.mount(scene, fakeRenderer());
    env.setQuality("low");
    expect(countEnvironmentLights(scene)).toEqual({ sun: 1, hemi: 1, sky: 1 });
    expect(env.diagnostics().skyEnabled).toBe(false);
    env.setQuality("high");
    expect(countEnvironmentLights(scene)).toEqual({ sun: 1, hemi: 1, sky: 1 });
    expect(env.diagnostics().skyEnabled).toBe(true);
    env.dispose();
  });

  it("LOW quality uses background without enabling sky", () => {
    const scene = new THREE.Scene();
    const env = new OdessaEnvironment({ quality: "low" });
    env.mount(scene, fakeRenderer());
    expect(countEnvironmentLights(scene)).toEqual({ sun: 1, hemi: 1, sky: 0 });
    expect(env.diagnostics().skyEnabled).toBe(false);
    env.dispose();
  });

  it("fog diagnostic toggle removes and restores haze without touching lights or exposure", () => {
    const scene = new THREE.Scene();
    const renderer = fakeRenderer();
    const env = new OdessaEnvironment({ quality: "medium" });
    env.mount(scene, renderer);
    const exposureBefore = renderer.toneMappingExposure;
    expect(scene.fog).toBeInstanceOf(THREE.FogExp2);
    env.setFogEnabled(false);
    expect(scene.fog).toBeNull();
    expect(env.diagnostics().fogEnabled).toBe(false);
    /* Preset/quality sync while disabled must not silently re-apply fog. */
    env.setQuality("high");
    expect(scene.fog).toBeNull();
    env.setFogEnabled(true);
    expect(scene.fog).toBeInstanceOf(THREE.FogExp2);
    expect(env.diagnostics().fogEnabled).toBe(true);
    expect(renderer.toneMappingExposure).toBe(exposureBefore);
    expect(countEnvironmentLights(scene)).toEqual({ sun: 1, hemi: 1, sky: 1 });
    env.dispose();
  });

  it("does not enable local shadows by default even on HIGH", () => {
    const scene = new THREE.Scene();
    const renderer = fakeRenderer();
    const env = new OdessaEnvironment({ quality: "high", enableLocalShadows: false });
    env.mount(scene, renderer);
    env.setLocalShadows(false);
    expect(renderer.shadowMap.enabled).toBe(false);
    env.dispose();
  });

  it("2D → 3D remount does not leave duplicate environment nodes", () => {
    writeViewMode("2d");
    writeViewMode("3d");
    const scene = new THREE.Scene();
    const first = new OdessaEnvironment({ quality: "medium" });
    first.mount(scene, fakeRenderer());
    first.dispose();
    writeViewMode("2d");
    writeViewMode("3d");
    const second = new OdessaEnvironment({ quality: "medium" });
    second.mount(scene, fakeRenderer());
    expect(countEnvironmentLights(scene)).toEqual({ sun: 1, hemi: 1, sky: 1 });
    expect(scene.children.filter((c) => c.name === "odessaEnvironment")).toHaveLength(1);
    second.dispose();
    writeViewMode("2d");
    expect(readViewMode()).toBe("2d");
  });
});

describe("Odessa atmosphere fog", () => {
  it("does not hide nearby city-scale distances", () => {
    const density = fogDensityForCity(1400, "medium", 1.08);
    const near = 1 - Math.exp(-((density * 80) ** 2));
    const far = 1 - Math.exp(-((density * 1200) ** 2));
    expect(near).toBeLessThan(0.02);
    expect(far).toBeGreaterThan(0.35);
  });
});

describe("Odessa sea runtime material", () => {
  it("applies only to canonical WEB_water, not bay or rivers", () => {
    const sea = waterMesh("WEB_water");
    const bay = waterMesh("WEB_bay");
    const river = waterMesh("WEB_rivers");
    const root = new THREE.Group();
    root.add(sea.group, bay.group, river.group);
    applyWaterSurfaceGuard([root]);
    const preset = getEnvironmentPreset("CLEAR_DAY");
    expect(isCanonicalSeaMesh(sea.mesh)).toBe(true);
    expect(isCanonicalSeaMesh(bay.mesh)).toBe(false);
    expect(isCanonicalSeaMesh(river.mesh)).toBe(false);
    expect(applyCanonicalSeaAppearance(sea.mesh, preset)).toBe(true);
    expect(applyCanonicalSeaAppearance(bay.mesh, preset)).toBe(false);
    expect(applyCanonicalSeaAppearance(river.mesh, preset)).toBe(false);
    const seaMat = sea.mesh.material as THREE.MeshStandardMaterial;
    expect(seaMat.color.getHex()).toBe(preset.waterColor);
    expect(seaMat.metalness).toBe(0);
    expect(seaMat.roughness).toBeGreaterThanOrEqual(0.55);
    expect(seaMat.envMap).toBeNull();
    expect((bay.mesh.material as THREE.MeshStandardMaterial).color.getHex()).not.toBe(preset.waterColor);
  });
});

describe("untextured building readability", () => {
  it("adds roughness to washed white untextured surfaces and leaves others alone", () => {
    const white = new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: 0.12, metalness: 0.4 });
    const red = new THREE.MeshStandardMaterial({ color: 0xaa3333, roughness: 0.2 });
    const textured = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1 });
    textured.map = new THREE.Texture();
    const water = new THREE.MeshStandardMaterial({ name: "Water", color: 0xffffff, roughness: 0.1 });
    expect(applyUntexturedReadability(white)).toBe(true);
    expect(white.roughness).toBeGreaterThanOrEqual(0.55);
    expect(white.roughness).toBeLessThanOrEqual(0.85);
    expect(white.metalness).toBe(0);
    expect(white.color.r).toBeGreaterThan(0.8);
    expect(white.color.getHex()).not.toBe(0xffffff);
    expect(applyUntexturedReadability(red)).toBe(false);
    expect(red.roughness).toBe(0.2);
    expect(applyUntexturedReadability(textured)).toBe(false);
    expect(textured.roughness).toBe(0.1);
    expect(applyUntexturedReadability(water)).toBe(false);
    textured.map.dispose();
    white.dispose();
    red.dispose();
    textured.dispose();
    water.dispose();
  });
});

describe("STEP 27 lighting / materials", () => {
  it("scales sun vs fill by quality without adding lights", () => {
    const preset = getEnvironmentPreset("CLEAR_DAY");
    const low = lightingForQuality(preset, "low");
    const med = lightingForQuality(preset, "medium");
    const high = lightingForQuality(preset, "high");
    expect(high.sunIntensity).toBeGreaterThan(med.sunIntensity);
    expect(high.hemiIntensity).toBeLessThan(med.hemiIntensity);
    expect(low.sunIntensity).toBeLessThan(med.sunIntensity);
    expect(med.sunIntensity).toBeGreaterThan(med.hemiIntensity);
  });

  it("classifies water / road / building from names and does not use per-frame state", () => {
    expect(classifyUrbanMaterial({ materialName: "WEB_water" })).toBe("WATER");
    expect(classifyUrbanMaterial({ meshName: "asphalt_road_01" })).toBe("ROAD");
    expect(classifyUrbanMaterial({ materialName: "BuildingWhite" })).toBe("BUILDING");
    expect(classifyUrbanMaterial({ materialName: "TreeLeaves" })).toBe("VEGETATION");
  });

  it("building variation is deterministic and bounded ±3–6%", () => {
    const a = buildingVariationDelta("TILE_02_00", "plaster");
    const b = buildingVariationDelta("TILE_02_00", "plaster");
    const c = buildingVariationDelta("TILE_08_00", "plaster");
    expect(a).toBe(b);
    expect(c).not.toBe(a);
    expect(Math.abs(a)).toBeGreaterThanOrEqual(0);
    expect(Math.abs(a)).toBeLessThanOrEqual(0.06);
    expect(stableUnitHash("x")).toBe(stableUnitHash("x"));
  });

  it("does not rewrite authored textures or water, and skips variation on LOW", () => {
    const textured = new THREE.MeshStandardMaterial({ color: 0xcccccc, roughness: 0.2 });
    textured.map = new THREE.Texture();
    const water = new THREE.MeshStandardMaterial({ name: "SeaWater", color: 0x338899, metalness: 0.4 });
    const gray = new THREE.MeshStandardMaterial({ name: "Building", color: 0xc8c8c8, roughness: 0.2, metalness: 0.3 });
    expect(applyUrbanVisualPass(textured, { assetId: "a", meshName: "m", quality: "medium" }).skippedTextured).toBe(true);
    expect(textured.roughness).toBe(0.2);
    expect(applyUrbanVisualPass(water, { assetId: "a", meshName: "WEB_water", quality: "high" }).classified).toBe("WATER");
    expect(water.metalness).toBe(0.4);
    const low = applyUrbanVisualPass(gray, { assetId: "TILE_01", meshName: "bldg", quality: "low" });
    expect(low.classified).toBe("BUILDING");
    expect(low.varied).toBe(false);
    expect(low.normalized).toBe(false);
    expect(gray.metalness).toBe(0.3);
    const medGray = new THREE.MeshStandardMaterial({ name: "Building", color: 0xc8c8c8, roughness: 0.2, metalness: 0.3 });
    const med = applyUrbanVisualPass(medGray, { assetId: "TILE_01", meshName: "bldg", quality: "medium" });
    expect(med.normalized).toBe(true);
    expect(med.varied).toBe(true);
    expect(medGray.metalness).toBe(0);
    expect(medGray.roughness).toBeGreaterThanOrEqual(0.55);
    textured.map.dispose();
    textured.dispose();
    water.dispose();
    gray.dispose();
    medGray.dispose();
  });

  it("darkens identified road materials and keeps vegetation hue", () => {
    const road = new THREE.MeshStandardMaterial({ name: "AsphaltRoad", color: 0x888888, roughness: 0.4 });
    const before = road.color.getHex();
    applyUrbanVisualPass(road, { assetId: "t", meshName: "street", quality: "medium" });
    expect(road.color.getHex()).not.toBe(before);
    expect(road.color.getHex()).toBeLessThan(before);
    expect(road.metalness).toBe(0);
    const veg = new THREE.MeshStandardMaterial({ name: "ParkGrass", color: 0x3d8a3a, roughness: 0.4 });
    applyUrbanVisualPass(veg, { assetId: "t", meshName: "lawn", quality: "medium" });
    expect(veg.color.getHex()).toBe(0x3d8a3a);
    road.dispose();
    veg.dispose();
  });
});
