/**
 * Model-side landmark candidates from authored mesh names.
 * Does not guess which generic WEB_build is a real building.
 */

import { normalizeLandmarkName } from "./publicLandmarks";
import type { LocalWorldCoordinate } from "./types";

export type ModelLandmarkCandidate = {
  id: string;
  name: string;
  normalized: string;
  world: LocalWorldCoordinate | null;
  source: string;
  matchable: boolean;
};

export type InventoryNameRecord = {
  name?: string;
  file?: string;
  center?: { x?: number; y?: number; z?: number };
};

const GENERIC =
  /^(name|build|highway|landuse|amenity|natural|route|height|building|barrier|shop|power|aeroway|track|residential|footway|service|path|road|tram|trolleybus|primary|secondary|tertiary|trunk|unclassified|pedestrian|steps|restriction|leisure|man|made)$/;

export function extractModelLandmarks(records: readonly InventoryNameRecord[]): ModelLandmarkCandidate[] {
  const out: ModelLandmarkCandidate[] = [];
  for (const rec of records) {
    const name = rec.name ?? "";
    if (!name) continue;
    const normalized = normalizeLandmarkName(name);
    const tokens = normalized.split(" ").filter((t) => t.length >= 4 && !GENERIC.test(t) && !/^\d+$/.test(t));
    const matchable = tokens.length > 0 && !/^[\d\s]+$/.test(normalized);
    const world =
      rec.center && Number.isFinite(rec.center.x) && Number.isFinite(rec.center.y) && Number.isFinite(rec.center.z)
        ? { x: rec.center.x as number, y: rec.center.y as number, z: rec.center.z as number }
        : null;
    out.push({
      id: name,
      name,
      normalized,
      world,
      source: rec.file ?? "inventory",
      matchable,
    });
  }
  return out;
}

export function matchableModelLandmarks(records: readonly InventoryNameRecord[]): ModelLandmarkCandidate[] {
  return extractModelLandmarks(records).filter((m) => m.matchable);
}
