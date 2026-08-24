/**
 * Manifest bounds cache — schedule from authored extents, measure geometry once.
 */

import type { CityBounds } from "./types";

export type CachedCenter = { x: number; y: number; z: number };

const centers = new Map<string, CachedCenter>();
const measured = new Map<string, CityBounds>();

export function centerFromCityBounds(b: CityBounds): CachedCenter {
  return {
    x: (b.minX + b.maxX) * 0.5,
    y: ((b.minY ?? 0) + (b.maxY ?? 0)) * 0.5,
    z: (b.minZ + b.maxZ) * 0.5,
  };
}

export function cacheManifestCenter(assetId: string, bounds?: CityBounds): CachedCenter | null {
  if (!bounds) return centers.get(assetId) ?? null;
  const c = centerFromCityBounds(bounds);
  centers.set(assetId, c);
  return c;
}

export function getCachedCenter(assetId: string): CachedCenter | null {
  return centers.get(assetId) ?? null;
}

export function cacheMeasuredBounds(assetId: string, bounds: CityBounds): CityBounds {
  measured.set(assetId, bounds);
  centers.set(assetId, centerFromCityBounds(bounds));
  return bounds;
}

export function getMeasuredBounds(assetId: string): CityBounds | undefined {
  return measured.get(assetId);
}

export function distanceXZ(ax: number, az: number, bx: number, bz: number): number {
  return Math.hypot(ax - bx, az - bz);
}

export function clearBoundsCache() {
  centers.clear();
  measured.clear();
}
