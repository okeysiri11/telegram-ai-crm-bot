/**
 * Distance-tier thresholds. Scaled by city size and quality lodBias.
 * Coarser bias (LOW) shrinks NEAR/MID; HIGH keeps more of the city detailed.
 */

import type { QualityProfile } from "../types";
import { resolveQuality } from "../qualityProfile";
import type { LodThresholds } from "./lodTypes";

export const LOD_HYSTERESIS = 0.28;
export const LOD_REF_DIAGONAL_M = 1400;
export const LOD_SCREEN_IMPORTANT = 0.08;
export const LOD_TARGET_PROTECT_M = 380;

export function lodThresholdsFor(
  profile: QualityProfile,
  cityDiagonalM = LOD_REF_DIAGONAL_M,
  lodBias?: number,
): LodThresholds {
  const q = resolveQuality(profile);
  const bias = lodBias ?? q.lodBias;
  const scale = Math.max(0.55, cityDiagonalM / LOD_REF_DIAGONAL_M);
  const shrinkNear = 1 + bias * 0.28;
  const shrinkMid = 1 + bias * 0.16;
  const shrinkFar = 1 + bias * 0.08;
  return {
    nearM: (420 * scale) / shrinkNear,
    midM: (1050 * scale) / shrinkMid,
    farM: (2400 * scale) / shrinkFar,
    targetProtectM: LOD_TARGET_PROTECT_M * scale,
    screenImportant: LOD_SCREEN_IMPORTANT,
    hysteresis: LOD_HYSTERESIS,
  };
}

export function radiusFromBounds(b?: { minX: number; maxX: number; minZ: number; maxZ: number }): number {
  if (!b) return 400;
  return Math.hypot(b.maxX - b.minX, b.maxZ - b.minZ) * 0.5;
}
