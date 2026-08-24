/**
 * Distance-tier classification with hysteresis, and hide policy that
 * cannot punch city/sea holes or flicker at a hard ring.
 */

import type { DistanceTier, LodThresholds, LodVisibilityInput } from "./lodTypes";

const TIER_RANK: Record<DistanceTier, number> = { NEAR: 0, MID: 1, FAR: 2, CULL: 3 };

export function classifyDistanceTier(distanceM: number, t: LodThresholds): DistanceTier {
  if (distanceM <= t.nearM) return "NEAR";
  if (distanceM <= t.midM) return "MID";
  if (distanceM <= t.farM) return "FAR";
  return "CULL";
}

export function classifyDistanceTierHysteresis(
  distanceM: number,
  t: LodThresholds,
  prev?: DistanceTier,
): DistanceTier {
  const raw = classifyDistanceTier(distanceM, t);
  if (!prev || prev === raw) return raw;
  const h = t.hysteresis;
  const promote = TIER_RANK[raw] < TIER_RANK[prev];
  if (promote) {
    if (prev === "MID" && distanceM > t.nearM * (1 - h)) return "MID";
    if (prev === "FAR" && distanceM > t.midM * (1 - h)) return "FAR";
    if (prev === "CULL" && distanceM > t.farM * (1 - h)) return "CULL";
    return raw;
  }
  if (prev === "NEAR" && distanceM < t.nearM * (1 + h)) return "NEAR";
  if (prev === "MID" && distanceM < t.midM * (1 + h)) return "MID";
  if (prev === "FAR" && distanceM < t.farM * (1 + h)) return "FAR";
  return raw;
}

/**
 * City + sea + look-at stay visible. Only heavy FAR/CULL may hide, and only
 * with hysteresis (caller passes currentlyVisible).
 */
export function shouldAssetBeVisible(input: LodVisibilityInput, t: LodThresholds): boolean {
  if (input.seaProtected || input.nearTarget) return true;
  if (input.screenImportant) return true;
  const cityLike = input.layerId !== "heavy";
  if (cityLike) return true;

  const tier = classifyDistanceTierHysteresis(input.distanceM, t, input.prevTier);
  if (tier === "NEAR" || tier === "MID") return true;
  if (tier === "FAR") {
    if (input.inFrustum) return true;
    return input.currentlyVisible && input.distanceM < t.farM * (1 + t.hysteresis);
  }
  if (input.currentlyVisible) return input.distanceM < t.farM * (1 + t.hysteresis * 1.4);
  return false;
}
