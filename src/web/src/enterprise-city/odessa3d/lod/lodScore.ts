/**
 * LOD priority scoring, screen-space importance, sea/target protection.
 * Lower score loads / activates first. Never invents LOD URLs.
 */

import type { LodScoreInput } from "./lodTypes";

const WATER_OR_COAST = /water|sea|ocean|bay|river|lake|canal|coast|harbour|harbor/i;

const PROTECTED_SEA_IDS = new Set([
  "TILE_04_00_REST_BATCH_07",
  "TILE_05_00",
  "TILE_03_00",
]);

export function isSeaOrCoastProtected(id: string, layerId?: string, url?: string): boolean {
  if (PROTECTED_SEA_IDS.has(id)) return true;
  if (WATER_OR_COAST.test(id) || WATER_OR_COAST.test(url || "")) return true;
  if (layerId === "dynamic") return false;
  return false;
}

/** Screen-space height fraction of a bounding radius. */
export function screenSpaceImportance(
  radiusM: number,
  distanceM: number,
  fovYDeg: number,
  viewportHeightPx: number,
): number {
  const dist = Math.max(8, distanceM);
  const fov = (Math.max(10, fovYDeg) * Math.PI) / 180;
  const worldH = 2 * dist * Math.tan(fov / 2);
  if (worldH <= 0 || viewportHeightPx <= 0) return 0;
  return (radiusM * 2 * viewportHeightPx) / worldH / viewportHeightPx;
}

export function isScreenImportant(importance: number, threshold: number): boolean {
  return importance >= threshold;
}

/** Bounded wait boost so far assets cannot starve behind a stream of slightly nearer ones. */
export function starveBoost(waitMs = 0): number {
  if (waitMs <= 0) return 0;
  return Math.min(420, waitMs / 48);
}

export function scoreLodPriority(input: LodScoreInput): number {
  let score = input.distanceM;
  if (input.seaProtected) score -= 8000;
  if (input.manifestPriority) score -= 5000;
  if (input.nearTarget) score -= 2800;
  if (input.inFrustum) score -= 2000;
  if (input.screenImportant) score -= 1500;
  score -= starveBoost(input.waitMs);
  score -= Math.max(0, input.cameraForwardDot ?? 0) * 500;
  if (input.layerId === "heavy" || input.heavyClass === "HEAVY") score += 700;
  if (input.heavyClass === "EXTREME") score += 1200;
  score += Math.max(0, (input.sizeMb ?? 0) - 8) * 35;
  return score;
}

/** Runtime URL is always the manifest URL. Never append _lodN or sibling paths. */
export function resolveRuntimeAssetUrl(url: string): string {
  return url;
}

export function isInventedLodUrl(url: string): boolean {
  return /(?:^|\/)[^/]*_lod\d+(?:\.[a-z0-9]+)?$/i.test(url) || /\/lod\d+\//i.test(url);
}
