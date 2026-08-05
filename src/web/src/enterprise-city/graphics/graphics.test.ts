import { beforeEach, describe, expect, it } from "vitest";
import { CITY_BUILDINGS, getBuilding } from "../cityCatalog";
import { CITY_DISTRICTS, getDistrict } from "../cityDistricts";
import { DEFAULT_VIEWPORT, clampViewport, panToBuilding } from "../cityEngine";
import {
  buildSceneGraph,
  walkSceneGraph,
  findSceneNode,
  sceneGraphStats,
} from "./sceneGraph";
import { DEFAULT_LAYERS, createLayerRegistry, QUALITY_DISABLED_LAYERS } from "./layerSystem";
import {
  animateViewport,
  focusBuilding,
  focusDistrict,
  resetCamera,
  cameraBounds,
} from "./cameraEngine";
import { animateValue } from "./animationController";
import { resolveEffect, allEffectKinds, isForbiddenAnimationClass } from "./visualEffects";
import { applyCityGraphicsTheme, availableCityThemes, baseThemeFor } from "./graphicsTheme";
import {
  CITY_GRAPHICS_CONFIG_KEY,
  defaultGraphicsSettings,
  normalizeGraphicsSettings,
  readGraphicsSettings,
  writeGraphicsSettings,
  qualityRank,
} from "./graphicsConfig";
import { createCityFrame, shouldRenderLayer } from "./renderPipeline";

describe("Sprint CG-2 Enterprise City Graphics Engine", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  describe("scene graph", () => {
    it("builds City -> District -> Building from the real live catalogs", () => {
      const scene = buildSceneGraph();
      expect(scene.kind).toBe("city");
      expect(scene.children).toHaveLength(CITY_DISTRICTS.length);
      const district = scene.children.find((d) => d.refId === "crm")!;
      expect(district.kind).toBe("district");
      expect(district.children.some((b) => b.refId === "crm")).toBe(true);
    });

    it("excludes the plaza from district building lists", () => {
      const scene = buildSceneGraph();
      const allBuildingIds = new Set<string>();
      walkSceneGraph(scene, (node) => {
        if (node.kind === "building") allBuildingIds.add(String(node.refId));
      });
      expect(allBuildingIds.has("plaza")).toBe(false);
      const realBuildingCount = CITY_BUILDINGS.filter((b) => b.kind !== "plaza").length;
      expect(allBuildingIds.size).toBe(realBuildingCount);
    });

    it("activates Floor/Room/InteractiveObject only when extension data is passed", () => {
      const bare = buildSceneGraph();
      expect(sceneGraphStats(bare).floor).toBe(0);

      const withFloors = buildSceneGraph([
        {
          buildingId: "crm",
          floors: [
            { id: "f1", label: "Floor 1", rooms: [{ id: "r1", label: "Room 1", interactiveObjects: [{ id: "o1", label: "Desk" }] }] },
          ],
        },
      ]);
      const stats = sceneGraphStats(withFloors);
      expect(stats.floor).toBe(1);
      expect(stats.room).toBe(1);
      expect(stats.interactive_object).toBe(1);
    });

    it("finds a node by stable id", () => {
      const scene = buildSceneGraph();
      const found = findSceneNode(scene, "building:crm");
      expect(found?.label).toBe(getBuilding("crm")!.label);
      expect(findSceneNode(scene, "building:does-not-exist")).toBeNull();
    });
  });

  describe("layer system", () => {
    it("defaults debug off and all other layers on, in the requested order", () => {
      expect(DEFAULT_LAYERS.map((l) => l.id)).toEqual([
        "background",
        "roads",
        "buildings",
        "effects",
        "agents",
        "selection",
        "ui_overlay",
        "debug",
      ]);
      const registry = createLayerRegistry();
      expect(registry.isEnabled("debug")).toBe(false);
      expect(registry.isEnabled("buildings")).toBe(true);
    });

    it("toggles a layer without mutating the previous registry", () => {
      const registry = createLayerRegistry();
      const toggled = registry.toggle("debug");
      expect(registry.isEnabled("debug")).toBe(false);
      expect(toggled.isEnabled("debug")).toBe(true);
    });

    it("orders layers by paint order", () => {
      const registry = createLayerRegistry();
      expect(registry.ordered().map((l) => l.id)[0]).toBe("background");
      expect(registry.ordered().at(-1)!.id).toBe("debug");
    });

    it("lists layers a low/medium quality tier should disable", () => {
      expect(QUALITY_DISABLED_LAYERS.low).toEqual(expect.arrayContaining(["effects", "debug"]));
      expect(QUALITY_DISABLED_LAYERS.medium).toEqual(["debug"]);
    });
  });

  describe("camera engine", () => {
    it("derives bounds by probing the real clamp function, matching cityEngine's real limits", () => {
      const bounds = cameraBounds();
      expect(bounds.zoomMax).toBe(1.75);
      expect(bounds.zoomMin).toBe(0.65);
      expect(bounds.panLimit).toBe(35);
    });

    it("collapses to a single instant frame under reducedMotion", () => {
      const frames: unknown[] = [];
      const handle = animateViewport(DEFAULT_VIEWPORT, { x: 10, y: 10, zoom: 1.2 }, {
        reducedMotion: true,
        onFrame: (v) => frames.push(v),
      });
      expect(frames).toHaveLength(1);
      expect(handle.cancel).toBeTypeOf("function");
    });

    it("animates focusBuilding toward the real panToBuilding target", () => {
      const crm = getBuilding("crm")!;
      let last: { x: number; y: number; zoom: number } | null = null;
      focusBuilding(DEFAULT_VIEWPORT, crm, {
        reducedMotion: true,
        onFrame: (v) => (last = v),
      });
      expect(last).not.toBeNull();
      expect(last).toEqual(panToBuilding(crm, DEFAULT_VIEWPORT));
    });

    it("animates focusDistrict toward the district centroid", () => {
      const crmDistrict = getDistrict("crm")!;
      let last: { x: number; y: number; zoom: number } | null = null;
      focusDistrict(DEFAULT_VIEWPORT, crmDistrict, {
        reducedMotion: true,
        onFrame: (v) => (last = v),
      });
      expect(last).not.toBeNull();
      expect(clampViewport(last!)).toEqual(last);
    });

    it("resets the camera to the real DEFAULT_VIEWPORT", () => {
      let last: { x: number; y: number; zoom: number } | null = null;
      resetCamera({ x: 20, y: -20, zoom: 1.5 }, {
        reducedMotion: true,
        onFrame: (v) => (last = v),
      });
      expect(last).toEqual(DEFAULT_VIEWPORT);
    });
  });

  describe("animation controller", () => {
    it("drives frames from 0 toward 1 and completes, via jsdom's real requestAnimationFrame", async () => {
      const frames: number[] = [];
      await new Promise<void>((resolve) => {
        animateValue({
          durationMs: 20,
          onFrame: (t) => frames.push(t),
          onComplete: resolve,
        });
      });
      expect(frames.length).toBeGreaterThan(0);
      expect(frames.at(-1)).toBe(1);
      expect(frames.every((t) => t >= 0 && t <= 1)).toBe(true);
    });

    it("returns a cancellable handle that stops further frames", async () => {
      const frames: number[] = [];
      const handle = animateValue({ durationMs: 1000, onFrame: (t) => frames.push(t) });
      handle.cancel();
      await new Promise((r) => setTimeout(r, 50));
      const countAtCancel = frames.length;
      await new Promise((r) => setTimeout(r, 50));
      expect(frames.length).toBe(countAtCancel);
    });
  });

  describe("visual effects", () => {
    it("resolves every declared effect kind to a class + duration", () => {
      for (const kind of allEffectKinds()) {
        const resolved = resolveEffect(kind);
        expect(resolved.className.length).toBeGreaterThan(0);
        expect(resolved.durationMs).toBeGreaterThanOrEqual(0);
      }
    });

    it("collapses duration to 0 under reducedMotion", () => {
      const resolved = resolveEffect("glow", true);
      expect(resolved.durationMs).toBe(0);
    });

    it("keeps pulse continuous only because its class is on the platform's sanctioned loop allowlist", () => {
      const resolved = resolveEffect("pulse");
      expect(resolved.continuous).toBe(true);
      expect(resolved.className).toBe("edm-ai-live");
    });

    it("flags forbidden animation classes", () => {
      expect(isForbiddenAnimationClass("some-bounce-class")).toBe(true);
      expect(isForbiddenAnimationClass("eds-anim-fade")).toBe(false);
    });
  });

  describe("graphics theme", () => {
    it("maps every City theme onto a real platform ThemeId", () => {
      for (const theme of availableCityThemes()) {
        expect(["light", "dark", "corporate", "custom"]).toContain(baseThemeFor(theme));
      }
    });

    it("applies without throwing outside a DOM context guard", () => {
      expect(() => applyCityGraphicsTheme("enterprise")).not.toThrow();
      expect(() => applyCityGraphicsTheme("cyber")).not.toThrow();
    });
  });

  describe("graphics config", () => {
    it("derives sensible per-tier defaults", () => {
      const low = defaultGraphicsSettings("low");
      const ultra = defaultGraphicsSettings("ultra");
      expect(low.fpsLimit).toBeLessThan(ultra.fpsLimit);
      expect(qualityRank(low.quality)).toBeLessThan(qualityRank(ultra.quality));
    });

    it("repairs corrupt/partial settings field by field", () => {
      const repaired = normalizeGraphicsSettings({ quality: "ultra", fpsLimit: -5, effectQuality: "bogus" as never });
      expect(repaired.quality).toBe("ultra");
      expect(repaired.fpsLimit).toBeGreaterThan(0);
      expect(["low", "medium", "high", "ultra"]).toContain(repaired.effectQuality);
    });

    it("persists and reads back settings under the real ews_city_*_v1 key convention", () => {
      expect(CITY_GRAPHICS_CONFIG_KEY).toBe("ews_city_graphics_v1");
      writeGraphicsSettings(defaultGraphicsSettings("medium"));
      const read = readGraphicsSettings();
      expect(read.quality).toBe("medium");
    });

    it("falls back to defaults when nothing is persisted", () => {
      expect(readGraphicsSettings().quality).toBe("high");
    });
  });

  describe("render pipeline", () => {
    it("composes scene, layers, settings, viewport and bounds into one frame", () => {
      const frame = createCityFrame();
      expect(frame.scene.kind).toBe("city");
      expect(frame.viewport).toEqual(DEFAULT_VIEWPORT);
      expect(frame.bounds.zoomMax).toBe(1.75);
      expect(shouldRenderLayer(frame, "buildings")).toBe(true);
    });

    it("disables the effects layer by default at low quality", () => {
      const frame = createCityFrame({ settings: defaultGraphicsSettings("low") });
      expect(shouldRenderLayer(frame, "effects")).toBe(false);
      expect(shouldRenderLayer(frame, "buildings")).toBe(true);
    });

    it("lets explicit layer overrides win over quality defaults", () => {
      const frame = createCityFrame({
        settings: defaultGraphicsSettings("low"),
        layerOverrides: { effects: true },
      });
      expect(shouldRenderLayer(frame, "effects")).toBe(true);
    });
  });
});
