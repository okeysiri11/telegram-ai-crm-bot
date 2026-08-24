/**
 * Deterministic RANSAC around the production similarity solver.
 * Does not replace solveCalibrationWithAxisInference.
 */

import type { GeoControlPoint, CalibrationSolveResult } from "./types";
import { solveCalibrationWithAxisInference } from "./geoCalibration";
import { horizontalResidualMeters } from "./calibrationDiagnostics";

export const SOLVER_VERSION = "ados-odessa-similarity-xz-v1";

export type RansacOptions = {
  residualThresholdM?: number;
  minInliers?: number;
};

export type RansacSolveResult = {
  solve: CalibrationSolveResult;
  inliers: GeoControlPoint[];
  rejected: GeoControlPoint[];
};

function triples(n: number): Array<[number, number, number]> {
  const out: Array<[number, number, number]> = [];
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      for (let k = j + 1; k < n; k++) out.push([i, j, k]);
    }
  }
  return out;
}

export function ransacSolveCalibration(
  points: readonly GeoControlPoint[],
  options: RansacOptions = {},
): RansacSolveResult {
  const residualThresholdM = options.residualThresholdM ?? 15;
  const minInliers = options.minInliers ?? 3;
  if (points.length < 3) {
    return { solve: solveCalibrationWithAxisInference(points), inliers: [...points], rejected: [] };
  }
  let bestInliers: GeoControlPoint[] = [];
  let bestSolve: CalibrationSolveResult | null = null;
  const seeds = points.length <= 12 ? triples(points.length) : triples(Math.min(points.length, 8));
  for (const [i, j, k] of seeds) {
    const seed = [points[i], points[j], points[k]];
    const solved = solveCalibrationWithAxisInference(seed);
    if (!solved.calibration) continue;
    const inliers = points.filter(
      (p) => horizontalResidualMeters(p.world, p.geo, solved.calibration!).errorM <= residualThresholdM,
    );
    if (inliers.length < minInliers) continue;
    if (inliers.length > bestInliers.length) {
      bestInliers = inliers;
      bestSolve = solved;
    }
  }
  if (bestInliers.length >= minInliers) {
    const refined = solveCalibrationWithAxisInference(bestInliers);
    const rejected = points.filter((p) => !bestInliers.some((i) => i.id === p.id));
    return { solve: refined.calibration ? refined : bestSolve!, inliers: bestInliers, rejected };
  }
  return { solve: solveCalibrationWithAxisInference(points), inliers: [...points], rejected: [] };
}
