/**
 * Exact-name semantic mapping only. No nearest-building guesses.
 */

import { normalizeLandmarkName, type PublicLandmark } from "./publicLandmarks";
import type { ModelLandmarkCandidate } from "./modelLandmarks";
import type { GeoCoordinate, LocalWorldCoordinate } from "./types";

export type SemanticMapping = {
  publicId: string;
  modelId: string;
  name: string;
  gps: GeoCoordinate;
  world: LocalWorldCoordinate | null;
  source: string;
};

export function mapLandmarksExact(
  publicLandmarks: readonly PublicLandmark[],
  modelLandmarks: readonly ModelLandmarkCandidate[],
): SemanticMapping[] {
  const byNorm = new Map<string, ModelLandmarkCandidate[]>();
  for (const m of modelLandmarks) {
    if (!m.matchable) continue;
    const list = byNorm.get(m.normalized) ?? [];
    list.push(m);
    byNorm.set(m.normalized, list);
  }
  const out: SemanticMapping[] = [];
  for (const pub of publicLandmarks) {
    const names = [pub.name, ...pub.aliases].map(normalizeLandmarkName).filter(Boolean);
    for (const n of names) {
      const hits = byNorm.get(n);
      if (!hits || hits.length !== 1) continue;
      const model = hits[0];
      out.push({
        publicId: pub.id,
        modelId: model.id,
        name: pub.name,
        gps: pub.gps,
        world: model.world,
        source: `${pub.source} ↔ ${model.source}`,
      });
      break;
    }
  }
  return out;
}
