/**
 * Quality profiles for 3D Odessa — safe degradation on mobile/weak devices.
 */

import type { QualityProfile } from "./types";
import { UNLOAD_DISTANCE_MULTIPLIER, VISIBILITY_UNLOAD_MULTIPLIER } from "./odessaPerformance";

export type QualitySettings = {
  profile: QualityProfile;
  maxConcurrentLoads: number;
  maxActiveTiles: number;
  loadDistanceM: number;
  unloadDistanceM: number;
  unloadDistanceMultiplier: number;
  visibilityDistanceM: number;
  visibilityUnloadDistanceM: number;
  heavyLoadDistanceM: number;
  heavyUnloadDistanceM: number;
  enableShadows: boolean;
  antialias: boolean;
  pixelRatioCap: number;
  lodBias: number;
  cameraFarCap: number;
  maxAnisotropy: number;
  /** HIGH-only optional local shadows. Always false in STEP 23 baseline. */
  enableLocalShadows: boolean;
};

const PRESETS: Record<Exclude<QualityProfile, "auto">, QualitySettings> = {
  low: {
    profile: "low",
    maxConcurrentLoads: 1,
    maxActiveTiles: 6,
    loadDistanceM: 1100,
    unloadDistanceM: 1100 * UNLOAD_DISTANCE_MULTIPLIER,
    unloadDistanceMultiplier: UNLOAD_DISTANCE_MULTIPLIER,
    visibilityDistanceM: 1400,
    visibilityUnloadDistanceM: 1400 * VISIBILITY_UNLOAD_MULTIPLIER,
    heavyLoadDistanceM: 650,
    heavyUnloadDistanceM: 650 * UNLOAD_DISTANCE_MULTIPLIER,
    enableShadows: false,
    antialias: false,
    pixelRatioCap: 1,
    lodBias: 2,
    cameraFarCap: 12000,
    maxAnisotropy: 1,
    enableLocalShadows: false,
  },
  medium: {
    profile: "medium",
    maxConcurrentLoads: 2,
    maxActiveTiles: 10,
    loadDistanceM: 1600,
    unloadDistanceM: 1600 * UNLOAD_DISTANCE_MULTIPLIER,
    unloadDistanceMultiplier: UNLOAD_DISTANCE_MULTIPLIER,
    visibilityDistanceM: 2000,
    visibilityUnloadDistanceM: 2000 * VISIBILITY_UNLOAD_MULTIPLIER,
    heavyLoadDistanceM: 900,
    heavyUnloadDistanceM: 900 * UNLOAD_DISTANCE_MULTIPLIER,
    enableShadows: false,
    antialias: true,
    pixelRatioCap: 1.25,
    lodBias: 1,
    cameraFarCap: 16000,
    maxAnisotropy: 4,
    enableLocalShadows: false,
  },
  high: {
    profile: "high",
    maxConcurrentLoads: 3,
    maxActiveTiles: 14,
    loadDistanceM: 2200,
    unloadDistanceM: 2200 * UNLOAD_DISTANCE_MULTIPLIER,
    unloadDistanceMultiplier: UNLOAD_DISTANCE_MULTIPLIER,
    visibilityDistanceM: 2800,
    visibilityUnloadDistanceM: 2800 * VISIBILITY_UNLOAD_MULTIPLIER,
    heavyLoadDistanceM: 1200,
    heavyUnloadDistanceM: 1200 * UNLOAD_DISTANCE_MULTIPLIER,
    enableShadows: false,
    antialias: true,
    pixelRatioCap: 1.5,
    lodBias: 0,
    cameraFarCap: 20000,
    maxAnisotropy: 8,
    enableLocalShadows: false,
  },
};

export function isLowPowerDevice(): boolean {
  if (typeof window === "undefined") return false;
  try {
    if (window.matchMedia?.("(max-width: 768px)")?.matches) return true;
  } catch {
    /* jsdom without matchMedia */
  }
  const cores = typeof navigator !== "undefined" ? navigator.hardwareConcurrency || 8 : 8;
  /* 4-core Intel laptops are desktop, not phones — only treat dual-core as weak. */
  return cores <= 2;
}

/** Never blindly use full devicePixelRatio above 1.5. Floor 0.85 (LOW). */
export function clampPixelRatio(devicePixelRatio: number, cap: number): number {
  const boundedCap = Math.min(Math.max(cap, 0.85), 1.5);
  return Math.min(Math.max(devicePixelRatio, 0), boundedCap);
}

export type RendererQualityConfig = {
  mode: QualityProfile;
  antialias: boolean;
  pixelRatioCap: number;
  pixelRatioFloor: number;
  maxAnisotropy: number;
};

/** Policy anisotropy: LOW 1 / MEDIUM 4 / HIGH 8, clamped to GPU max. */
export function anisotropyForQuality(
  profile: QualityProfile,
  gpuMaxAnisotropy: number,
  lowPower = false,
): number {
  const gpu = Math.max(1, gpuMaxAnisotropy || 1);
  if (profile === "low" || (profile === "auto" && lowPower)) return 1;
  if (profile === "high") return Math.min(8, gpu);
  return Math.min(4, gpu);
}

export function rendererQualityConfig(profile: QualityProfile): RendererQualityConfig {
  const q = resolveQuality(profile);
  const lowPower = profile === "auto" && isLowPowerDevice();
  return {
    mode: q.profile,
    antialias: q.antialias,
    pixelRatioCap: q.pixelRatioCap,
    pixelRatioFloor: lowPower || q.profile === "low" ? 0.85 : 1,
    maxAnisotropy: q.maxAnisotropy,
  };
}

export function resolveQuality(profile: QualityProfile): QualitySettings {
  if (profile === "auto") {
    const lowPower = isLowPowerDevice();
    const base = lowPower ? PRESETS.low : PRESETS.medium;
    return {
      ...base,
      profile: "auto",
      antialias: !lowPower,
      pixelRatioCap: lowPower ? 1 : 1.25,
      maxAnisotropy: lowPower ? 1 : 4,
      maxConcurrentLoads: lowPower ? 1 : 2,
    };
  }
  return PRESETS[profile];
}

export const CITY_VIEW_MODE_KEY = "ews_city_view_mode";
export const CITY_3D_QUALITY_KEY = "ews_city_3d_quality";

export function readViewMode(): "2d" | "3d" {
  try {
    const v = sessionStorage.getItem(CITY_VIEW_MODE_KEY);
    return v === "3d" ? "3d" : "2d";
  } catch {
    return "2d";
  }
}

export function writeViewMode(mode: "2d" | "3d") {
  try {
    sessionStorage.setItem(CITY_VIEW_MODE_KEY, mode);
  } catch {
    /* ignore */
  }
}

export function readQualityProfile(): QualityProfile {
  try {
    const v = sessionStorage.getItem(CITY_3D_QUALITY_KEY) as QualityProfile | null;
    if (v === "low" || v === "medium" || v === "high" || v === "auto") return v;
  } catch {
    /* ignore */
  }
  return "auto";
}

export function writeQualityProfile(profile: QualityProfile) {
  try {
    sessionStorage.setItem(CITY_3D_QUALITY_KEY, profile);
  } catch {
    /* ignore */
  }
}
