/**
 * Enterprise City Graphics Engine — Render Pipeline.
 * Sprint CG-2. The single orchestration point that composes scene graph + layer system + camera
 * engine + visual effects + graphics config into one object a City screen consumes. This file
 * contains no rendering itself (no DOM, no canvas) — it only assembles the read-only frame data a
 * consumer (`EnterpriseCityPage.tsx` or any future City screen) uses to decide what to paint.
 * Reusable by every City screen; owns no store, no business logic, no Runtime/backend calls.
 */

import type { CityViewport } from "../cityEngine";
import { DEFAULT_VIEWPORT } from "../cityEngine";
import type { SceneBuildingExtension } from "./sceneGraph";
import { buildSceneGraph, sceneGraphStats } from "./sceneGraph";
import { createLayerRegistry, QUALITY_DISABLED_LAYERS, type LayerRegistry } from "./layerSystem";
import { cameraBounds } from "./cameraEngine";
import { readGraphicsSettings } from "./graphicsConfig";
import type { GraphicsSettings, SceneNode } from "./types";

export type CityFrame = {
  scene: SceneNode;
  stats: ReturnType<typeof sceneGraphStats>;
  layers: LayerRegistry;
  settings: GraphicsSettings;
  viewport: CityViewport;
  bounds: ReturnType<typeof cameraBounds>;
};

export type CreateCityFramePipelineOptions = {
  viewport?: CityViewport;
  settings?: GraphicsSettings;
  floorExtensions?: SceneBuildingExtension[];
  layerOverrides?: Partial<Record<import("./types").RenderLayerId, boolean>>;
};

/**
 * Build one immutable frame's worth of render data. Cheap to call per-render: the scene graph is
 * the only non-trivial piece of work, and it is proportional to the real (small, ~34-building)
 * catalog — no pagination or memoization is needed at this scale.
 */
export function createCityFrame(options: CreateCityFramePipelineOptions = {}): CityFrame {
  const settings = options.settings ?? readGraphicsSettings();
  const scene = buildSceneGraph(options.floorExtensions ?? []);
  const qualityDisabled = QUALITY_DISABLED_LAYERS[settings.quality as "low" | "medium"] ?? [];
  const disabledOverrides = Object.fromEntries(qualityDisabled.map((id) => [id, false]));
  const layers = createLayerRegistry({ ...disabledOverrides, ...options.layerOverrides });

  return {
    scene,
    stats: sceneGraphStats(scene),
    layers,
    settings,
    viewport: options.viewport ?? DEFAULT_VIEWPORT,
    bounds: cameraBounds(),
  };
}

/** Whether a given render layer should currently paint, honoring both the registry and reduced-motion. */
export function shouldRenderLayer(frame: CityFrame, id: import("./types").RenderLayerId): boolean {
  return frame.layers.isEnabled(id);
}
