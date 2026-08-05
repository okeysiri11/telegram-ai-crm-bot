/**
 * Enterprise City Graphics Engine — Graphics Configuration.
 * Sprint CG-2. Quality tiers (Low/Medium/High/Ultra) plus FPS limit, animation/effect/shadow
 * quality, and icon density. Plain read/write functions over `localStorage`, matching the style
 * `cityEngine.ts` already uses for `sessionStorage` — not a new Zustand store. Key follows the
 * platform's real `ews_city_*_v1` naming convention.
 */

import type { GraphicsQuality, GraphicsSettings } from "./types";

export const CITY_GRAPHICS_CONFIG_KEY = "ews_city_graphics_v1";

const QUALITY_ORDER: GraphicsQuality[] = ["low", "medium", "high", "ultra"];

/** Per-tier defaults — every other quality field defaults to its tier's own value unless overridden. */
const TIER_DEFAULTS: Record<GraphicsQuality, Omit<GraphicsSettings, "quality" | "reducedMotion">> = {
  low: { fpsLimit: 30, animationQuality: "low", effectQuality: "low", shadowQuality: "low", iconDensity: "low" },
  medium: { fpsLimit: 45, animationQuality: "medium", effectQuality: "medium", shadowQuality: "low", iconDensity: "medium" },
  high: { fpsLimit: 60, animationQuality: "high", effectQuality: "high", shadowQuality: "medium", iconDensity: "high" },
  ultra: { fpsLimit: 120, animationQuality: "ultra", effectQuality: "ultra", shadowQuality: "ultra", iconDensity: "ultra" },
};

export function defaultGraphicsSettings(quality: GraphicsQuality = "high"): GraphicsSettings {
  return { quality, reducedMotion: false, ...TIER_DEFAULTS[quality] };
}

function isQuality(v: unknown): v is GraphicsQuality {
  return typeof v === "string" && (QUALITY_ORDER as string[]).includes(v);
}

/** Validate/repair a possibly-corrupt settings object field-by-field rather than rejecting it wholesale. */
export function normalizeGraphicsSettings(input: Partial<GraphicsSettings> | null | undefined): GraphicsSettings {
  const base = defaultGraphicsSettings(isQuality(input?.quality) ? input!.quality : "high");
  return {
    quality: base.quality,
    fpsLimit: typeof input?.fpsLimit === "number" && input.fpsLimit > 0 ? input.fpsLimit : base.fpsLimit,
    animationQuality: isQuality(input?.animationQuality) ? input!.animationQuality : base.animationQuality,
    effectQuality: isQuality(input?.effectQuality) ? input!.effectQuality : base.effectQuality,
    shadowQuality: isQuality(input?.shadowQuality) ? input!.shadowQuality : base.shadowQuality,
    iconDensity: isQuality(input?.iconDensity) ? input!.iconDensity : base.iconDensity,
    reducedMotion: Boolean(input?.reducedMotion),
  };
}

export function readGraphicsSettings(): GraphicsSettings {
  try {
    const raw = localStorage.getItem(CITY_GRAPHICS_CONFIG_KEY);
    if (!raw) return defaultGraphicsSettings();
    return normalizeGraphicsSettings(JSON.parse(raw) as Partial<GraphicsSettings>);
  } catch {
    return defaultGraphicsSettings();
  }
}

export function writeGraphicsSettings(settings: GraphicsSettings): void {
  try {
    localStorage.setItem(CITY_GRAPHICS_CONFIG_KEY, JSON.stringify(normalizeGraphicsSettings(settings)));
  } catch {
    /* ignore */
  }
}

/** Numeric rank for comparisons (e.g. "is effectQuality at least medium?"). */
export function qualityRank(q: GraphicsQuality): number {
  return QUALITY_ORDER.indexOf(q);
}
