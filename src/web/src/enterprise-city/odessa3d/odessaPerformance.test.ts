import { describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import {
  AdaptivePixelRatioController,
  DemandRenderLoop,
  HARD_PIXEL_RATIO_CAP,
  HUD_THROTTLE_MS,
  QUALITY_IDLE_BOOST_MS,
  UNLOAD_DISTANCE_MULTIPLIER,
  applyTexturedMaterialFilters,
  loadUnloadDistances,
  scoreTilePriority,
  visibilityWithHysteresis,
} from "./odessaPerformance";
import { anisotropyForQuality, clampPixelRatio, isLowPowerDevice, rendererQualityConfig, resolveQuality } from "./qualityProfile";

describe("Odessa 3D performance", () => {
  it("quality presets clamp pixel ratio: LOW=1, MEDIUM=1.25, HIGH=1.5, never above 1.5", () => {
    expect(resolveQuality("low").pixelRatioCap).toBe(1);
    expect(resolveQuality("medium").pixelRatioCap).toBe(1.25);
    expect(resolveQuality("high").pixelRatioCap).toBe(1.5);
    expect(resolveQuality("high").enableShadows).toBe(false);
    expect(clampPixelRatio(3, 2)).toBeLessThanOrEqual(HARD_PIXEL_RATIO_CAP);
    expect(clampPixelRatio(2, 1.5)).toBe(1.5);
    expect(clampPixelRatio(0.9, 1)).toBe(0.9);
    expect(clampPixelRatio(3, 0.7)).toBeGreaterThanOrEqual(0.85);
  });

  it("unload distance is larger than load distance (hysteresis band)", () => {
    const { loadDistanceM, unloadDistanceM } = loadUnloadDistances(1000);
    expect(unloadDistanceM).toBeGreaterThan(loadDistanceM);
    expect(unloadDistanceM / loadDistanceM).toBeCloseTo(UNLOAD_DISTANCE_MULTIPLIER);
  });

  it("visibility hysteresis keeps assets visible until beyond unload distance", () => {
    expect(visibilityWithHysteresis(900, 800, 1100, true)).toBe(true);
    expect(visibilityWithHysteresis(1150, 800, 1100, true)).toBe(false);
    expect(visibilityWithHysteresis(790, 800, 1100, false)).toBe(true);
    expect(visibilityWithHysteresis(850, 800, 1100, false)).toBe(false);
  });

  it("prioritizes in-frustum near tiles over distant heavy tiles", () => {
    const near = scoreTilePriority({
      tileId: "a",
      distanceM: 200,
      inFrustum: true,
      manifestPriority: false,
      layerId: "city",
      sizeMb: 5,
      cameraForwardDot: 0.8,
    });
    const farHeavy = scoreTilePriority({
      tileId: "b",
      distanceM: 200,
      inFrustum: false,
      manifestPriority: false,
      layerId: "heavy",
      sizeMb: 24,
      cameraForwardDot: -0.5,
    });
    expect(near).toBeLessThan(farHeavy);
  });

  it("AUTO starts at 1.25 and never exceeds 1.5 even on high devicePixelRatio", () => {
    const ctrl = new AdaptivePixelRatioController("auto", 1.5);
    expect(ctrl.currentRatio(3)).toBe(1.25);
    expect(ctrl.currentRatio(3)).toBeLessThanOrEqual(HARD_PIXEL_RATIO_CAP);
  });

  it("adaptive DPR steps down only after sustained FPS below 26 for 3s", () => {
    const ctrl = new AdaptivePixelRatioController("auto", 1.25);
    const start = 1000;
    expect(ctrl.currentRatio(2)).toBe(1.25);
    ctrl.observe(42, start, 20, "INTERACTING");
    ctrl.observe(42, start + 2000, 20, "INTERACTING");
    expect(ctrl.currentRatio(2)).toBe(1.25);
    ctrl.observe(42, start + 3100, 20, "INTERACTING");
    expect(ctrl.currentRatio(2)).toBe(1);
  });

  it("does not raise DPR while interacting even if FPS is high", () => {
    const ctrl = new AdaptivePixelRatioController("auto", 1.25);
    const start = 1000;
    ctrl.observe(50, start, 20, "INTERACTING");
    ctrl.observe(50, start + 3100, 20, "INTERACTING");
    expect(ctrl.currentRatio(2)).toBe(1);
    ctrl.observe(16, start + 4000, 55, "INTERACTING");
    ctrl.observe(16, start + 13000, 55, "INTERACTING");
    expect(ctrl.currentRatio(2)).toBe(1);
  });

  it("restores preferred DPR after idle boost (~650 ms)", () => {
    const ctrl = new AdaptivePixelRatioController("auto", 1.25);
    const start = 1000;
    ctrl.observe(50, start, 20, "INTERACTING");
    ctrl.observe(50, start + 3100, 20, "INTERACTING");
    expect(ctrl.currentRatio(2)).toBe(1);
    ctrl.observe(16, start + 3200, 50, "IDLE");
    expect(ctrl.currentRatio(2)).toBe(1);
    ctrl.observe(16, start + 3200 + QUALITY_IDLE_BOOST_MS + 10, 50, "IDLE");
    expect(ctrl.currentRatio(2)).toBe(1.25);
  });

  it("FPS guard does not oscillate in the 26–40 dead band while interacting", () => {
    const ctrl = new AdaptivePixelRatioController("auto", 1.25);
    const start = 1000;
    ctrl.observe(42, start, 20, "INTERACTING");
    ctrl.observe(42, start + 3100, 20, "INTERACTING");
    const degraded = ctrl.currentRatio(2);
    expect(degraded).toBe(1);
    ctrl.observe(28, start + 4000, 33, "INTERACTING");
    ctrl.observe(28, start + 13000, 33, "INTERACTING");
    expect(ctrl.currentRatio(2)).toBe(degraded);
  });

  it("DemandRenderLoop uses a single RAF chain and stops when idle", () => {
    const raf = vi.spyOn(globalThis, "requestAnimationFrame").mockImplementation((cb) => {
      cb(0);
      return 1;
    });
    const cancel = vi.spyOn(globalThis, "cancelAnimationFrame").mockImplementation(() => {});
    let frames = 0;
    let keepGoing = true;
    const loop = new DemandRenderLoop({
      onFrame: () => {
        frames += 1;
        if (frames >= 2) keepGoing = false;
      },
      shouldContinue: () => keepGoing,
    });
    loop.requestFrame();
    expect(frames).toBeGreaterThanOrEqual(1);
    loop.dispose();
    expect(cancel).toHaveBeenCalled();
    raf.mockRestore();
    cancel.mockRestore();
  });

  it("DemandRenderLoop dispose cancels pending RAF", () => {
    let pendingCb: FrameRequestCallback | null = null;
    vi.spyOn(globalThis, "requestAnimationFrame").mockImplementation((cb) => {
      pendingCb = cb;
      return 42;
    });
    const cancel = vi.spyOn(globalThis, "cancelAnimationFrame").mockImplementation(() => {});
    const loop = new DemandRenderLoop({ onFrame: () => {}, shouldContinue: () => true });
    loop.requestFrame();
    loop.dispose();
    expect(cancel).toHaveBeenCalledWith(42);
    expect(pendingCb).toBeTruthy();
    cancel.mockRestore();
  });

  it("HUD throttle interval is between 250 and 500 ms", () => {
    expect(HUD_THROTTLE_MS).toBeGreaterThanOrEqual(250);
    expect(HUD_THROTTLE_MS).toBeLessThanOrEqual(500);
  });
});

describe("Odessa quality unload distances", () => {
  it("heavy load/unload distances use hysteresis multiplier", () => {
    const q = resolveQuality("medium");
    expect(q.heavyUnloadDistanceM).toBeGreaterThan(q.heavyLoadDistanceM);
    expect(q.unloadDistanceM).toBeGreaterThan(q.loadDistanceM);
  });

  it("AUTO quality restores MSAA on desktop and keeps cap ≤ 1.25", () => {
    const auto = resolveQuality("auto");
    expect(auto.profile).toBe("auto");
    expect(auto.antialias).toBe(true);
    expect(auto.pixelRatioCap).toBe(1.25);
    expect(auto.enableShadows).toBe(false);
    expect(auto.enableLocalShadows).toBe(false);
    expect(resolveQuality("high").enableLocalShadows).toBe(false);
    expect(resolveQuality("medium").antialias).toBe(true);
    expect(resolveQuality("low").antialias).toBe(false);
  });

  it("does not treat a 4-core Intel laptop as low-power", () => {
    vi.stubGlobal("navigator", { hardwareConcurrency: 4 });
    expect(isLowPowerDevice()).toBe(false);
    expect(resolveQuality("auto").antialias).toBe(true);
    vi.unstubAllGlobals();
  });

  it("anisotropy policy is LOW 1 / MEDIUM 4 / HIGH 8 clamped to GPU max", () => {
    expect(anisotropyForQuality("low", 16)).toBe(1);
    expect(anisotropyForQuality("medium", 16)).toBe(4);
    expect(anisotropyForQuality("high", 16)).toBe(8);
    expect(anisotropyForQuality("high", 2)).toBe(2);
    expect(anisotropyForQuality("auto", 16, false)).toBe(4);
    expect(anisotropyForQuality("auto", 16, true)).toBe(1);
  });

  it("renderer quality config matches STEP 26 MSAA / DPR ranges", () => {
    const low = rendererQualityConfig("low");
    const med = rendererQualityConfig("medium");
    const high = rendererQualityConfig("high");
    expect(low.antialias).toBe(false);
    expect(low.pixelRatioFloor).toBe(0.85);
    expect(low.pixelRatioCap).toBe(1);
    expect(med.antialias).toBe(true);
    expect(med.pixelRatioCap).toBe(1.25);
    expect(high.antialias).toBe(true);
    expect(high.pixelRatioCap).toBe(1.5);
  });
});

describe("texture filtering", () => {
  it("enables mipmaps, linear mag, and requested anisotropy on textured maps", () => {
    const tex = new THREE.Texture();
    applyTexturedMaterialFilters(tex, 4);
    expect(tex.generateMipmaps).toBe(true);
    expect(tex.minFilter).toBe(THREE.LinearMipmapLinearFilter);
    expect(tex.magFilter).toBe(THREE.LinearFilter);
    expect(tex.anisotropy).toBe(4);
    tex.dispose();
  });
});
