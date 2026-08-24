/**
 * Odessa visual environment presets. CLEAR_DAY is the STEP 23 baseline.
 * SOFT_DAY / SUNSET / NIGHT are config stubs — not full lighting productions.
 */

import type { QualityProfile } from "../types";
import { isLowPowerDevice } from "../qualityProfile";

export type EnvironmentPresetId = "CLEAR_DAY" | "SOFT_DAY" | "SUNSET" | "NIGHT";
export type EnvironmentQuality = "low" | "medium" | "high";
export type WaterVisualMode = "stable" | "sea-override" | "off";

export type EnvironmentPreset = {
  id: EnvironmentPresetId;
  implemented: boolean;
  turbidity: number;
  rayleigh: number;
  mieCoefficient: number;
  mieDirectionalG: number;
  elevationDeg: number;
  azimuthDeg: number;
  exposure: number;
  sunColor: number;
  sunIntensity: number;
  hemiSky: number;
  hemiGround: number;
  hemiIntensity: number;
  fogColor: number;
  haze: number;
  backgroundColor: number;
  waterColor: number;
  waterRoughnessNear: number;
  waterRoughnessFar: number;
};

export const ODESSA_CLEAR_DAY: EnvironmentPreset = {
  id: "CLEAR_DAY",
  implemented: true,
  turbidity: 3.1,
  rayleigh: 1.55,
  mieCoefficient: 0.0042,
  mieDirectionalG: 0.74,
  elevationDeg: 34,
  azimuthDeg: 148,
  exposure: 0.8,
  sunColor: 0xffe8c8,
  sunIntensity: 1.26,
  hemiSky: 0xb8cce0,
  hemiGround: 0x6e6358,
  hemiIntensity: 0.28,
  fogColor: 0xa9c0d0,
  haze: 1.0,
  backgroundColor: 0xaec4d6,
  waterColor: 0x154e5a,
  waterRoughnessNear: 0.62,
  waterRoughnessFar: 0.82,
};

export const ODESSA_SOFT_DAY: EnvironmentPreset = {
  ...ODESSA_CLEAR_DAY,
  id: "SOFT_DAY",
  implemented: false,
  turbidity: 4.2,
  rayleigh: 1.35,
  sunIntensity: 0.92,
  hemiIntensity: 0.4,
  exposure: 0.84,
  haze: 1.15,
};

export const ODESSA_SUNSET: EnvironmentPreset = {
  ...ODESSA_CLEAR_DAY,
  id: "SUNSET",
  implemented: false,
  elevationDeg: 8,
  azimuthDeg: 248,
  turbidity: 6,
  rayleigh: 2.2,
  sunColor: 0xffc58a,
  sunIntensity: 0.78,
  hemiSky: 0xd8b8a0,
  hemiGround: 0x6a5348,
  fogColor: 0xd2b8a4,
  backgroundColor: 0xc9a890,
  exposure: 0.78,
};

export const ODESSA_NIGHT: EnvironmentPreset = {
  ...ODESSA_CLEAR_DAY,
  id: "NIGHT",
  implemented: false,
  elevationDeg: -12,
  azimuthDeg: 200,
  turbidity: 1,
  rayleigh: 0.4,
  sunIntensity: 0.04,
  hemiSky: 0x1a2433,
  hemiGround: 0x0c1016,
  hemiIntensity: 0.22,
  fogColor: 0x121820,
  backgroundColor: 0x0d1218,
  exposure: 0.7,
  waterColor: 0x0c2a34,
  waterRoughnessNear: 0.72,
  waterRoughnessFar: 0.88,
};

export const ENVIRONMENT_PRESETS: Record<EnvironmentPresetId, EnvironmentPreset> = {
  CLEAR_DAY: ODESSA_CLEAR_DAY,
  SOFT_DAY: ODESSA_SOFT_DAY,
  SUNSET: ODESSA_SUNSET,
  NIGHT: ODESSA_NIGHT,
};

export const DEFAULT_ENVIRONMENT_PRESET: EnvironmentPresetId = "CLEAR_DAY";

export function getEnvironmentPreset(id: EnvironmentPresetId = DEFAULT_ENVIRONMENT_PRESET): EnvironmentPreset {
  return ENVIRONMENT_PRESETS[id] ?? ODESSA_CLEAR_DAY;
}

export function resolveEnvironmentQuality(profile: QualityProfile): EnvironmentQuality {
  if (profile === "low") return "low";
  if (profile === "high") return "high";
  if (profile === "medium") return "medium";
  return isLowPowerDevice() ? "low" : "medium";
}

export function lightingForQuality(
  preset: EnvironmentPreset,
  quality: EnvironmentQuality,
): { sunIntensity: number; hemiIntensity: number; exposure: number } {
  if (quality === "low") {
    return {
      sunIntensity: preset.sunIntensity * 0.92,
      hemiIntensity: Math.min(0.36, preset.hemiIntensity * 1.1),
      exposure: preset.exposure,
    };
  }
  if (quality === "high") {
    return {
      sunIntensity: preset.sunIntensity * 1.08,
      hemiIntensity: preset.hemiIntensity * 0.82,
      exposure: preset.exposure,
    };
  }
  return {
    sunIntensity: preset.sunIntensity,
    hemiIntensity: preset.hemiIntensity,
    exposure: preset.exposure,
  };
}

export function validateEnvironmentPreset(preset: EnvironmentPreset): string[] {
  const errors: string[] = [];
  if (!preset?.id) errors.push("missing_id");
  const num = (key: keyof EnvironmentPreset, min: number, max: number) => {
    const v = preset[key];
    if (typeof v !== "number" || Number.isNaN(v) || v < min || v > max) errors.push(`range:${String(key)}`);
  };
  num("turbidity", 0, 20);
  num("rayleigh", 0, 8);
  num("mieCoefficient", 0, 0.1);
  num("mieDirectionalG", 0, 1);
  num("elevationDeg", -90, 90);
  num("azimuthDeg", 0, 360);
  num("exposure", 0.2, 2);
  num("sunIntensity", 0, 4);
  num("hemiIntensity", 0, 2);
  num("haze", 0.2, 3);
  num("waterRoughnessNear", 0.35, 1);
  num("waterRoughnessFar", 0.35, 1);
  if (preset.waterRoughnessNear > preset.waterRoughnessFar) errors.push("water_roughness_order");
  return errors;
}
