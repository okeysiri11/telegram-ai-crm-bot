/**
 * Pair-scale distribution from many matched correspondences.
 * Convention: WORLD_UNITS_PER_METER (same as STEP 30.1 solver).
 */

import type { GeoControlPoint } from "./types";
import { gpsHorizontalDistanceM, worldHorizontalDistance } from "./calibrationDiagnostics";

export const HISTORICAL_SOLVER_SCALE_1_4475 = 1.4475;
export const PACKAGE_SCALE_1_0 = 1;
export const SCALE_SUPPORT_RELATIVE_TOLERANCE = 0.08;
export const MIN_PAIRS_FOR_SCALE_DECISION = 3;

export type PairScaleDistribution = {
  count: number;
  median: number | null;
  mean: number | null;
  stddev: number | null;
  p05: number | null;
  p95: number | null;
  values: number[];
};

function percentile(sorted: readonly number[], p: number): number | null {
  if (!sorted.length) return null;
  const idx = (sorted.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  return sorted[lo] * (hi - idx) + sorted[hi] * (idx - lo);
}

export function allPairWorldUnitsPerMeter(points: readonly GeoControlPoint[]): number[] {
  const values: number[] = [];
  for (let i = 0; i < points.length; i++) {
    for (let j = i + 1; j < points.length; j++) {
      const world = worldHorizontalDistance(points[i].world, points[j].world);
      const gps = gpsHorizontalDistanceM(points[i].geo, points[j].geo);
      if (gps > 1e-6 && Number.isFinite(world / gps)) values.push(world / gps);
    }
  }
  return values;
}

export function summarizePairScales(values: readonly number[]): PairScaleDistribution {
  const finite = values.filter((n) => Number.isFinite(n)).sort((a, b) => a - b);
  if (!finite.length) {
    return { count: 0, median: null, mean: null, stddev: null, p05: null, p95: null, values: [] };
  }
  const mean = finite.reduce((s, n) => s + n, 0) / finite.length;
  const stddev =
    finite.length >= 2 ? Math.sqrt(finite.reduce((s, n) => s + (n - mean) ** 2, 0) / finite.length) : 0;
  return {
    count: finite.length,
    median: percentile(finite, 0.5),
    mean,
    stddev,
    p05: percentile(finite, 0.05),
    p95: percentile(finite, 0.95),
    values: finite,
  };
}

export function pairScaleDistribution(points: readonly GeoControlPoint[]): PairScaleDistribution {
  return summarizePairScales(allPairWorldUnitsPerMeter(points));
}

export function scaleHypothesisSupported(
  dist: PairScaleDistribution,
  target: number,
  relativeTol = SCALE_SUPPORT_RELATIVE_TOLERANCE,
): boolean {
  if (dist.count < MIN_PAIRS_FOR_SCALE_DECISION || dist.median == null || !Number.isFinite(target) || target <= 0) {
    return false;
  }
  const rel = Math.abs(dist.median - target) / target;
  const tight = dist.stddev == null || dist.stddev <= 0.15 * target;
  return rel <= relativeTol && tight;
}
