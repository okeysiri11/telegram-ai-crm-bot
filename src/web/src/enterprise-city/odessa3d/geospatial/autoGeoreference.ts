/**
 * STEP 30.4 automated georeference runner.
 * Uses the production solver only. Does not invent A/B/C or guess mesh identities.
 */

import type { GeoControlPoint } from "./types";
import { canPersistQuality } from "./geoCalibration";
import { loadPublicLandmarkCache, type PublicLandmark } from "./publicLandmarks";
import { extractModelLandmarks, matchableModelLandmarks, type InventoryNameRecord } from "./modelLandmarks";
import { mapLandmarksExact } from "./landmarkMapping";
import { ransacSolveCalibration, SOLVER_VERSION } from "./ransacCalibration";
import {
  IDENTITY_MODEL_ROOT,
  PACKAGE_EXPECTED_METERS_PER_WORLD_UNIT,
  PICK_COORDINATE_SPACE,
  classifyScaleStatus,
  pairScaleRows,
  rms,
  controlHorizontalResiduals,
} from "./calibrationDiagnostics";
import { describeAxisMapping, geoToWorld } from "./worldTransform";
import { evaluateHistoricalCheck } from "./historicalCheck";
import { saveAuthoredCalibration, type CalibrationStorage } from "./calibrationStore";
import { buildAuthoredRecord } from "./calibrationSession";
export type AutoGeoreferenceResult = {
  publicLandmarksFound: number;
  modelLandmarksMatched: number;
  semanticMappingFound: number;
  controlPoints: GeoControlPoint[];
  independentCheckPoints: GeoControlPoint[];
  axisMapping: string;
  solverScale: number | null;
  solverRotationDeg: number | null;
  controlRmsM: number | null;
  controlMaxM: number | null;
  independentCheckRmsM: number | null;
  independentCheckMaxM: number | null;
  historicalCheckErrorM: number | null;
  historicalCheckPredictedGps: string;
  historicalCheckActualGps: string;
  historicalCheckEastErrorM: number | null;
  historicalCheckNorthErrorM: number | null;
  pairScaleMedian: number | null;
  pairScaleStddev: number | null;
  pairRows: ReturnType<typeof pairScaleRows>;
  scaleStatus: ReturnType<typeof classifyScaleStatus>;
  quality: string;
  persisted: boolean;
  georeferenceStatus: "EXCELLENT" | "GOOD" | "ACCEPTABLE" | "FAILED" | "BLOCKED";
  rootCauseIfFailed: string;
  solverVersion: string;
  pickCoordinateSpace: typeof PICK_COORDINATE_SPACE;
  modelRoot: typeof IDENTITY_MODEL_ROOT;
};

function median(values: number[]): number | null {
  if (!values.length) return null;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

function stddev(values: number[]): number | null {
  if (values.length < 2) return null;
  const m = values.reduce((a, b) => a + b, 0) / values.length;
  return Math.sqrt(values.reduce((a, b) => a + (b - m) ** 2, 0) / values.length);
}

export function runAutomatedGeoreference(input: {
  inventory: readonly InventoryNameRecord[];
  publicLandmarks?: readonly PublicLandmark[];
  storage?: CalibrationStorage | null;
  modelFingerprint?: string;
}): AutoGeoreferenceResult {
  const publicLandmarks = input.publicLandmarks ?? loadPublicLandmarkCache();
  const modelAll = extractModelLandmarks(input.inventory);
  const modelMatchable = matchableModelLandmarks(input.inventory);
  const mapped = mapLandmarksExact(publicLandmarks, modelMatchable);
  const complete = mapped.filter((m) => m.world);
  const controls: GeoControlPoint[] = complete.map((m, i) => ({
    id: i < 3 ? (["A", "B", "C"] as const)[i] : `P${i}`,
    label: m.name,
    geo: m.gps,
    world: m.world!,
    coordinateSpace: "world",
  }));

  const empty: AutoGeoreferenceResult = {
    publicLandmarksFound: publicLandmarks.length,
    modelLandmarksMatched: modelMatchable.length,
    semanticMappingFound: mapped.length,
    controlPoints: [],
    independentCheckPoints: [],
    axisMapping: "—",
    solverScale: null,
    solverRotationDeg: null,
    controlRmsM: null,
    controlMaxM: null,
    independentCheckRmsM: null,
    independentCheckMaxM: null,
    historicalCheckErrorM: evaluateHistoricalCheck(null).errorM,
    historicalCheckPredictedGps: "46.386292, 30.705357",
    historicalCheckActualGps: "46.386267, 30.705832",
    historicalCheckEastErrorM: evaluateHistoricalCheck(null).eastErrorM,
    historicalCheckNorthErrorM: evaluateHistoricalCheck(null).northErrorM,
    pairScaleMedian: null,
    pairScaleStddev: null,
    pairRows: [],
    scaleStatus: "UNKNOWN",
    quality: "UNAVAILABLE",
    persisted: false,
    georeferenceStatus: "BLOCKED",
    rootCauseIfFailed: "NO_SEMANTIC_MODEL_TO_WGS84_MAPPING",
    solverVersion: SOLVER_VERSION,
    pickCoordinateSpace: PICK_COORDINATE_SPACE,
    modelRoot: IDENTITY_MODEL_ROOT,
  };

  if (controls.length < 3) {
    empty.modelLandmarksMatched = modelMatchable.length;
    empty.rootCauseIfFailed =
      modelAll.length === 0
        ? "NO_MODEL_LANDMARK_INVENTORY"
        : "NO_EXACT_NAME_CORRESPONDENCE_BETWEEN_PUBLIC_GPS_AND_MODEL_MESHES";
    return empty;
  }

  const holdouts = controls.slice(3);
  const fit = controls.slice(0, Math.max(3, controls.length - holdouts.length));
  const ransac = ransacSolveCalibration(fit);
  const solve = ransac.solve;
  const pairs = pairScaleRows(ransac.inliers.length >= 3 ? ransac.inliers : fit);
  const scales = pairs.map((p) => p.worldUnitsPerMeter).filter((n): n is number => n != null);
  const cal = solve.calibration;
  const horiz = cal ? controlHorizontalResiduals(fit, cal, geoToWorld) : [];
  const horizVals = horiz.map((h) => h.horizontalM);
  const chk = evaluateHistoricalCheck(cal, fit);
  const holdoutErrs = cal
    ? holdouts.map((p) => controlHorizontalResiduals([p], cal, geoToWorld)[0]?.horizontalM).filter((n): n is number => n != null)
    : [];

  const quality = solve.quality;
  const status =
    quality === "EXCELLENT" || quality === "GOOD" || quality === "ACCEPTABLE"
      ? quality
      : quality === "POOR"
        ? "FAILED"
        : "BLOCKED";

  let persisted = false;
  if (cal && canPersistQuality(quality) && input.storage && input.modelFingerprint) {
    const record = buildAuthoredRecord({
      solve,
      controlPoints: ransac.inliers,
      modelFingerprint: input.modelFingerprint,
      independentResidualMeters: holdoutErrs.length ? rms(holdoutErrs) : chk.errorM,
    });
    if (record) {
      persisted = saveAuthoredCalibration(
        {
          ...record,
          version: 4,
          schemaVersion: 4,
          independentChecks: holdouts.map((p) => ({
            id: p.id,
            world: p.world,
            gps: p.geo,
            pickedAt: null,
            coordinateSpace: "world" as const,
          })),
        },
        input.storage,
      );
    }
  }

  return {
    publicLandmarksFound: publicLandmarks.length,
    modelLandmarksMatched: modelMatchable.length,
    semanticMappingFound: mapped.length,
    controlPoints: fit,
    independentCheckPoints: holdouts,
    axisMapping: cal ? describeAxisMapping(cal.axisMapping) : "—",
    solverScale: solve.scale,
    solverRotationDeg: solve.rotation != null ? (solve.rotation * 180) / Math.PI : null,
    controlRmsM: rms(horizVals),
    controlMaxM: horizVals.length ? Math.max(...horizVals) : null,
    independentCheckRmsM: holdoutErrs.length ? rms(holdoutErrs) : null,
    independentCheckMaxM: holdoutErrs.length ? Math.max(...holdoutErrs) : null,
    historicalCheckErrorM: chk.errorM,
    historicalCheckPredictedGps: chk.predicted
      ? `${chk.predicted.lat.toFixed(6)}, ${chk.predicted.lon.toFixed(6)}`
      : "—",
    historicalCheckActualGps: "46.386267, 30.705832",
    historicalCheckEastErrorM: chk.eastErrorM,
    historicalCheckNorthErrorM: chk.northErrorM,
    pairScaleMedian: median(scales),
    pairScaleStddev: stddev(scales),
    pairRows: pairs,
    scaleStatus: classifyScaleStatus(pairs, solve.scale, PACKAGE_EXPECTED_METERS_PER_WORLD_UNIT),
    quality,
    persisted,
    georeferenceStatus: status,
    rootCauseIfFailed: status === "BLOCKED" || status === "FAILED" ? "SOLVE_QUALITY_INSUFFICIENT" : "",
    solverVersion: SOLVER_VERSION,
    pickCoordinateSpace: PICK_COORDINATE_SPACE,
    modelRoot: IDENTITY_MODEL_ROOT,
  };
}
