/**
 * Enterprise City Graphics Engine — shared types.
 * Sprint CG-2. Rendering/visualization only — no business logic, no runtime, no backend.
 * This module never redefines platform-level concepts (CityBuilding, CityDistrictMeta, CityViewport
 * all stay owned by cityCatalog.ts / cityDistricts.ts / cityEngine.ts respectively) — it only adds the
 * types those files have no reason to own themselves.
 */

import type { CityBuildingId, CityDistrictId } from "../cityCatalog";

export type SceneNodeKind = "city" | "district" | "building" | "floor" | "room" | "interactive_object";

/** One node in the City → District → Building → Floor → Room → Interactive Object hierarchy. */
export type SceneNode = {
  id: string;
  kind: SceneNodeKind;
  refId?: CityBuildingId | CityDistrictId | string;
  label: string;
  children: SceneNode[];
};

export type RenderLayerId =
  | "background"
  | "roads"
  | "buildings"
  | "effects"
  | "agents"
  | "selection"
  | "ui_overlay"
  | "debug";

export type LayerState = {
  id: RenderLayerId;
  label: string;
  /** Rendering order — lower paints first (background), higher paints last (debug overlays). */
  order: number;
  enabled: boolean;
};

export type EffectKind =
  | "hover"
  | "selection"
  | "pulse"
  | "highlight"
  | "glow"
  | "fade"
  | "building_activation"
  | "district_activation";

/** A resolved, ready-to-apply effect — a CSS class + duration, never raw style computation. */
export type ResolvedEffect = {
  kind: EffectKind;
  className: string;
  durationMs: number;
  /** True only for the platform's small set of sanctioned continuous loops (design-system rule). */
  continuous: boolean;
};

export type GraphicsQuality = "low" | "medium" | "high" | "ultra";

export type GraphicsSettings = {
  quality: GraphicsQuality;
  fpsLimit: number;
  animationQuality: GraphicsQuality;
  effectQuality: GraphicsQuality;
  shadowQuality: GraphicsQuality;
  iconDensity: GraphicsQuality;
  /** Mirrors the platform's own `prefers-reduced-motion` / reduced-motion contract. */
  reducedMotion: boolean;
};

export type CityGraphicsTheme = "light" | "dark" | "enterprise" | "cyber";

/** A single JS-driven animation in flight (camera focus transitions, building scale/opacity, etc). */
export type AnimationHandle = {
  id: string;
  cancel: () => void;
};
