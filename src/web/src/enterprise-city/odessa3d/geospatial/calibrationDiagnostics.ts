/**
 * Read-only georeference forensics. Does not invent GPS or change the live transform.
 * CHECK is never added to the solver.
 */

import type {
  AxisMapping,
  CalibrationSlotId,
  GeoCalibration,
  GeoControlPoint,
  GeoCoordinate,
  LocalWorldCoordinate,
} from "./types";
import { HORIZONTAL_AXIS_CANDIDATES, solveCalibrationFromControlPoints, solveCalibrationWithAxisInference } from "./geoCalibration";
import { horizontalDistanceMeters, wgs84ToLocalMeters } from "./localMeters";
import { describeAxisMapping, geoToWorld, worldToGeo } from "./worldTransform";
import type { CalibrationDraft, CheckDraft } from "./calibrationSession";
import { completeControlPoints } from "./calibrationSession";
import { activeOdessaPackage } from "../odessaPackage";

export const PICK_COORDINATE_SPACE = "threejs-world" as const;
export const PACKAGE_EXPECTED_METERS_PER_WORLD_UNIT = 1;
/** Pair / solver scale convention used in the V3 dump. */
export const SCALE_CONVENTION = "WORLD_UNITS_PER_METER" as const;

export type ModelRootTransform = {
  position: LocalWorldCoordinate;
  rotation: LocalWorldCoordinate;
  scale: LocalWorldCoordinate;
};

export const IDENTITY_MODEL_ROOT: ModelRootTransform = {
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0 },
  scale: { x: 1, y: 1, z: 1 },
};

export type ScaleConvention = "WORLD_UNITS_PER_METER" | "METERS_PER_WORLD_UNIT";

export type PairScaleRow = {
  pair: "AB" | "AC" | "BC";
  worldHorizontalDistance: number | null;
  gpsDistanceM: number | null;
  worldUnitsPerMeter: number | null;
  metersPerWorldUnit: number | null;
  convention: typeof SCALE_CONVENTION;
};

export type LeaveOneOutResult = {
  abToCErrorM: number | null;
  acToBErrorM: number | null;
  bcToAErrorM: number | null;
  likelyBadPoint: "A" | "B" | "C" | "NONE" | "INCONCLUSIVE";
};

export type CheckForensics = {
  world: LocalWorldCoordinate | null;
  actual: GeoCoordinate | null;
  predicted: GeoCoordinate | null;
  errorM: number | null;
  eastErrorM: number | null;
  northErrorM: number | null;
  includedInSolver: false;
  abSolverToCheckErrorM: number | null;
  acSolverToCheckErrorM: number | null;
  bcSolverToCheckErrorM: number | null;
};

export type AxisMappingRms = {
  mapping: AxisMapping;
  label: string;
  horizontalRmsM: number | null;
};

export type ScaleStatus =
  | "CONSISTENT_WITH_1M"
  | "CONSISTENT_WITH_SOLVER"
  | "CONTROL_POINTS_INCONSISTENT"
  | "UNKNOWN";

export type HorizontalPointResidual = {
  id: string;
  horizontalM: number;
  residual3dM: number;
};

export function worldHorizontalDistance(a: LocalWorldCoordinate, b: LocalWorldCoordinate): number {
  return Math.hypot(a.x - b.x, a.z - b.z);
}

export function gpsHorizontalDistanceM(a: GeoCoordinate, b: GeoCoordinate): number {
  return horizontalDistanceMeters(wgs84ToLocalMeters(a), wgs84ToLocalMeters(b));
}

/** Horizontal ENU residual: predicted GPS from world vs authored GPS. */
export function horizontalResidualMeters(
  world: LocalWorldCoordinate,
  geo: GeoCoordinate,
  calibration: GeoCalibration,
): { errorM: number; eastM: number; northM: number; predicted: GeoCoordinate } {
  const predicted = worldToGeo(world, calibration);
  const predEnu = wgs84ToLocalMeters(predicted);
  const actEnu = wgs84ToLocalMeters(geo);
  const eastM = predEnu.east - actEnu.east;
  const northM = predEnu.north - actEnu.north;
  return { errorM: Math.hypot(eastM, northM), eastM, northM, predicted };
}

export function residual3dMeters(
  world: LocalWorldCoordinate,
  geo: GeoCoordinate,
  calibration: GeoCalibration,
  geoToWorldFn: (g: GeoCoordinate, c: GeoCalibration) => LocalWorldCoordinate,
): number {
  const pred = geoToWorldFn(geo, calibration);
  return Math.hypot(pred.x - world.x, pred.y - world.y, pred.z - world.z) * Math.abs(calibration.metersPerWorldUnit);
}

export function pairScaleRows(points: readonly GeoControlPoint[]): PairScaleRow[] {
  const a = points.find((p) => p.id === "A" || p.label === "A");
  const b = points.find((p) => p.id === "B" || p.label === "B");
  const c = points.find((p) => p.id === "C" || p.label === "C");
  const row = (pair: PairScaleRow["pair"], p: GeoControlPoint | undefined, q: GeoControlPoint | undefined): PairScaleRow => {
    if (!p || !q) {
      return {
        pair,
        worldHorizontalDistance: null,
        gpsDistanceM: null,
        worldUnitsPerMeter: null,
        metersPerWorldUnit: null,
        convention: SCALE_CONVENTION,
      };
    }
    const worldDist = worldHorizontalDistance(p.world, q.world);
    const gpsDistanceM = gpsHorizontalDistanceM(p.geo, q.geo);
    const worldUnitsPerMeter = gpsDistanceM > 1e-6 ? worldDist / gpsDistanceM : null;
    const metersPerWorldUnit = worldDist > 1e-6 ? gpsDistanceM / worldDist : null;
    return {
      pair,
      worldHorizontalDistance: worldDist,
      gpsDistanceM,
      worldUnitsPerMeter,
      metersPerWorldUnit,
      convention: SCALE_CONVENTION,
    };
  };
  return [row("AB", a, b), row("AC", a, c), row("BC", b, c)];
}

export function classifyScaleStatus(
  pairs: readonly PairScaleRow[],
  solverWorldUnitsPerMeter: number | null,
  packageMetersPerWorldUnit = PACKAGE_EXPECTED_METERS_PER_WORLD_UNIT,
): ScaleStatus {
  const scales = pairs.map((p) => p.worldUnitsPerMeter).filter((n): n is number => n != null && Number.isFinite(n));
  if (scales.length < 2) return "UNKNOWN";
  const mean = scales.reduce((s, n) => s + n, 0) / scales.length;
  const spread = Math.max(...scales) - Math.min(...scales);
  const inconsistent = spread > 0.15 * Math.max(Math.abs(mean), 0.2);
  if (inconsistent) return "CONTROL_POINTS_INCONSISTENT";
  const packageWu = 1 / packageMetersPerWorldUnit;
  if (scales.every((s) => Math.abs(s - packageWu) / packageWu < 0.08)) return "CONSISTENT_WITH_1M";
  if (
    solverWorldUnitsPerMeter != null &&
    scales.every((s) => Math.abs(s - solverWorldUnitsPerMeter) / Math.max(Math.abs(solverWorldUnitsPerMeter), 0.2) < 0.08)
  ) {
    return "CONSISTENT_WITH_SOLVER";
  }
  return "UNKNOWN";
}

function holdoutHorizontalError(fit: GeoControlPoint[], held: GeoControlPoint): number | null {
  const solved = solveCalibrationWithAxisInference(fit);
  if (!solved.calibration) return null;
  return horizontalResidualMeters(held.world, held.geo, solved.calibration).errorM;
}

export function leaveOneOut(points: readonly GeoControlPoint[]): LeaveOneOutResult {
  const a = points.find((p) => p.id === "A" || p.label === "A");
  const b = points.find((p) => p.id === "B" || p.label === "B");
  const c = points.find((p) => p.id === "C" || p.label === "C");
  const empty: LeaveOneOutResult = {
    abToCErrorM: null,
    acToBErrorM: null,
    bcToAErrorM: null,
    likelyBadPoint: "INCONCLUSIVE",
  };
  if (!a || !b || !c) return empty;
  const abToCErrorM = holdoutHorizontalError([a, b], c);
  const acToBErrorM = holdoutHorizontalError([a, c], b);
  const bcToAErrorM = holdoutHorizontalError([b, c], a);
  const three = solveCalibrationWithAxisInference([a, b, c]);
  const fromResidual =
    three.calibration != null
      ? identifyLikelyBadFromResiduals(controlHorizontalResiduals([a, b, c], three.calibration, geoToWorld))
      : "INCONCLUSIVE";
  const fromScale = identifyLikelyBadFromPairScales(pairScaleRows([a, b, c]));
  const fromHoldout = identifyLikelyBadPoint({ A: bcToAErrorM, B: acToBErrorM, C: abToCErrorM });
  let likelyBadPoint: LeaveOneOutResult["likelyBadPoint"] = "INCONCLUSIVE";
  if (fromScale !== "INCONCLUSIVE" && fromScale !== "NONE") likelyBadPoint = fromScale;
  else if (fromResidual !== "INCONCLUSIVE" && fromResidual !== "NONE") likelyBadPoint = fromResidual;
  else likelyBadPoint = fromHoldout;
  return {
    abToCErrorM,
    acToBErrorM,
    bcToAErrorM,
    likelyBadPoint,
  };
}

export function identifyLikelyBadFromResiduals(
  rows: readonly HorizontalPointResidual[],
): LeaveOneOutResult["likelyBadPoint"] {
  const entries = rows
    .filter((r) => r.id === "A" || r.id === "B" || r.id === "C")
    .map((r) => ({ id: r.id as CalibrationSlotId, e: r.horizontalM }));
  if (entries.length < 3) return "INCONCLUSIVE";
  const sorted = [...entries].sort((x, y) => x.e - y.e);
  const max = sorted[2];
  const mid = sorted[1];
  if (max.e < 5 && max.e < mid.e * 1.8 + 1) return "NONE";
  if (max.e > mid.e * 1.5 && max.e > 8) return max.id;
  if (max.e > mid.e * 2.0) return max.id;
  return "INCONCLUSIVE";
}

export function identifyLikelyBadFromPairScales(
  pairs: readonly PairScaleRow[],
): LeaveOneOutResult["likelyBadPoint"] {
  const ab = pairs.find((p) => p.pair === "AB")?.worldUnitsPerMeter;
  const ac = pairs.find((p) => p.pair === "AC")?.worldUnitsPerMeter;
  const bc = pairs.find((p) => p.pair === "BC")?.worldUnitsPerMeter;
  if (ab == null || ac == null || bc == null) return "INCONCLUSIVE";
  const near = (x: number, y: number) => Math.abs(x - y) / Math.max(Math.abs(x), Math.abs(y), 0.2) < 0.08;
  const nearPackage = (s: number) => Math.abs(s - 1) < 0.08;
  const mean = (Math.abs(ab) + Math.abs(ac) + Math.abs(bc)) / 3;
  const spread = Math.max(ab, ac, bc) - Math.min(ab, ac, bc);
  if (spread < 0.08 * Math.max(mean, 0.2)) return "NONE";
  const packageHits = [
    nearPackage(ab) ? "AB" : null,
    nearPackage(ac) ? "AC" : null,
    nearPackage(bc) ? "BC" : null,
  ].filter((v): v is "AB" | "AC" | "BC" => v != null);
  /** The only pair consistent with 1 wu/m excludes the suspicious point. */
  if (packageHits.length === 1) {
    return packageHits[0] === "AB" ? "C" : packageHits[0] === "AC" ? "B" : "A";
  }
  if (packageHits.length === 3) return "NONE";
  if (near(ac, bc) && !near(ab, ac)) return "C";
  if (near(ab, ac) && !near(ab, bc)) return "A";
  if (near(ab, bc) && !near(ab, ac)) return "B";
  return "INCONCLUSIVE";
}

export function identifyLikelyBadPoint(errors: Record<CalibrationSlotId, number | null>): LeaveOneOutResult["likelyBadPoint"] {
  const entries = (["A", "B", "C"] as const)
    .map((id) => ({ id, e: errors[id] }))
    .filter((row): row is { id: CalibrationSlotId; e: number } => row.e != null && Number.isFinite(row.e));
  if (entries.length < 3) return "INCONCLUSIVE";
  const sorted = [...entries].sort((x, y) => x.e - y.e);
  const max = sorted[2];
  const mid = sorted[1];
  if (max.e < 5 && max.e < mid.e * 1.8 + 1) return "NONE";
  if (max.e > mid.e * 1.8 && max.e > 8) return max.id;
  if (max.e > mid.e * 2.2) return max.id;
  return "INCONCLUSIVE";
}

export function evaluateCheckForensics(
  check: CheckDraft,
  points: readonly GeoControlPoint[],
  threePointCal: GeoCalibration | null,
): CheckForensics {
  const base: CheckForensics = {
    world: check.world,
    actual: check.geo,
    predicted: null,
    errorM: null,
    eastErrorM: null,
    northErrorM: null,
    includedInSolver: false,
    abSolverToCheckErrorM: null,
    acSolverToCheckErrorM: null,
    bcSolverToCheckErrorM: null,
  };
  if (threePointCal && check.world && check.geo) {
    const r = horizontalResidualMeters(check.world, check.geo, threePointCal);
    base.predicted = r.predicted;
    base.errorM = r.errorM;
    base.eastErrorM = r.eastM;
    base.northErrorM = r.northM;
  } else if (threePointCal && check.world) {
    base.predicted = worldToGeo(check.world, threePointCal);
  }
  const a = points.find((p) => p.id === "A" || p.label === "A");
  const b = points.find((p) => p.id === "B" || p.label === "B");
  const c = points.find((p) => p.id === "C" || p.label === "C");
  const pairErr = (fit: GeoControlPoint[]) => {
    if (!check.world || !check.geo) return null;
    const solved = solveCalibrationWithAxisInference(fit);
    if (!solved.calibration) return null;
    return horizontalResidualMeters(check.world, check.geo, solved.calibration).errorM;
  };
  if (a && b) base.abSolverToCheckErrorM = pairErr([a, b]);
  if (a && c) base.acSolverToCheckErrorM = pairErr([a, c]);
  if (b && c) base.bcSolverToCheckErrorM = pairErr([b, c]);
  return base;
}

export function axisMappingRms(points: readonly GeoControlPoint[]): AxisMappingRms[] {
  return HORIZONTAL_AXIS_CANDIDATES.map((mapping) => {
    const solved = solveCalibrationFromControlPoints(points, "axis_test", mapping);
    const cal = solved.calibration;
    if (!cal || points.length < 2) {
      return { mapping, label: describeAxisMapping(mapping), horizontalRmsM: null };
    }
    const errs = points.map((p) => horizontalResidualMeters(p.world, p.geo, cal).errorM);
    const rms = Math.sqrt(errs.reduce((s, e) => s + e * e, 0) / errs.length);
    return { mapping, label: describeAxisMapping(mapping), horizontalRmsM: rms };
  });
}

export function bestAxisMapping(rows: readonly AxisMappingRms[]): AxisMappingRms | null {
  let best: AxisMappingRms | null = null;
  for (const row of rows) {
    if (row.horizontalRmsM == null) continue;
    if (!best || (best.horizontalRmsM != null && row.horizontalRmsM < best.horizontalRmsM - 1e-6)) {
      best = row;
    }
  }
  return best;
}

export function controlHorizontalResiduals(
  points: readonly GeoControlPoint[],
  calibration: GeoCalibration,
  geoToWorldFn: (g: GeoCoordinate, c: GeoCalibration) => LocalWorldCoordinate,
): HorizontalPointResidual[] {
  return points.map((p) => ({
    id: p.id,
    horizontalM: horizontalResidualMeters(p.world, p.geo, calibration).errorM,
    residual3dM: residual3dMeters(p.world, p.geo, calibration, geoToWorldFn),
  }));
}

export function rms(values: readonly number[]): number | null {
  if (!values.length) return null;
  return Math.sqrt(values.reduce((s, v) => s + v * v, 0) / values.length);
}

export function modelRootWarning(root: ModelRootTransform): string | null {
  const ident =
    Math.abs(root.position.x) < 1e-6 &&
    Math.abs(root.position.y) < 1e-6 &&
    Math.abs(root.position.z) < 1e-6 &&
    Math.abs(root.rotation.x) < 1e-6 &&
    Math.abs(root.rotation.y) < 1e-6 &&
    Math.abs(root.rotation.z) < 1e-6 &&
    Math.abs(root.scale.x - 1) < 1e-6 &&
    Math.abs(root.scale.y - 1) < 1e-6 &&
    Math.abs(root.scale.z - 1) < 1e-6;
  return ident ? null : "MODEL_ROOT_NOT_IDENTITY";
}

function fmtN(n: number | null | undefined, digits = 4): string {
  return n == null || !Number.isFinite(n) ? "—" : n.toFixed(digits);
}

function fmtWorld(w: LocalWorldCoordinate | null | undefined): string {
  return w ? `${w.x.toFixed(3)}, ${w.y.toFixed(3)}, ${w.z.toFixed(3)}` : "—";
}

function fmtGps(g: GeoCoordinate | null | undefined): string {
  return g ? `${g.lat.toFixed(6)}, ${g.lon.toFixed(6)}` : "—";
}

export function formatGeoreferenceDiagnosticV3(input: {
  draft: CalibrationDraft;
  check: CheckDraft;
  modelRoot?: ModelRootTransform;
  pickCoordinateSpace?: string;
}): string {
  const draft = input.draft;
  const points = completeControlPoints(draft);
  const solved = points.length >= 2 ? solveCalibrationWithAxisInference(points) : null;
  const cal = solved?.calibration ?? null;
  const horiz = cal ? controlHorizontalResiduals(points, cal, geoToWorld) : [];
  const byId = Object.fromEntries(horiz.map((r) => [r.id, r]));
  const pairs = pairScaleRows(points);
  const loo = leaveOneOut(points);
  const chk = evaluateCheckForensics(input.check, points, cal);
  const axes = points.length >= 2 ? axisMappingRms(points) : [];
  const best = bestAxisMapping(axes);
  const solverScale = solved?.scale ?? null;
  const scaleStatus = classifyScaleStatus(pairs, solverScale);
  const root = input.modelRoot ?? IDENTITY_MODEL_ROOT;
  const pickSpace = input.pickCoordinateSpace ?? PICK_COORDINATE_SPACE;
  const horizVals = horiz.map((r) => r.horizontalM);
  const d3 = horiz.map((r) => r.residual3dM);
  const currentAxis = cal ? describeAxisMapping(cal.axisMapping) : "—";
  const pair = (id: PairScaleRow["pair"]) => pairs.find((p) => p.pair === id);

  return [
    "=== GEOREFERENCE DIAGNOSTIC V3 ===",
    "",
    `A_WORLD=${fmtWorld(draft.A.world)}`,
    `A_GPS=${fmtGps(draft.A.geo)}`,
    `A_HORIZONTAL_RESIDUAL_M=${fmtN(byId.A?.horizontalM)}`,
    "",
    `B_WORLD=${fmtWorld(draft.B.world)}`,
    `B_GPS=${fmtGps(draft.B.geo)}`,
    `B_HORIZONTAL_RESIDUAL_M=${fmtN(byId.B?.horizontalM)}`,
    "",
    `C_WORLD=${fmtWorld(draft.C.world)}`,
    `C_GPS=${fmtGps(draft.C.geo)}`,
    `C_HORIZONTAL_RESIDUAL_M=${fmtN(byId.C?.horizontalM)}`,
    "",
    `CONTROL_HORIZONTAL_RMS_M=${fmtN(rms(horizVals))}`,
    `CONTROL_HORIZONTAL_MAX_M=${fmtN(horizVals.length ? Math.max(...horizVals) : null)}`,
    "",
    `CONTROL_3D_RMS_M=${fmtN(rms(d3))}`,
    `CONTROL_3D_MAX_M=${fmtN(d3.length ? Math.max(...d3) : null)}`,
    "",
    `AB_WORLD_HORIZONTAL_DISTANCE=${fmtN(pair("AB")?.worldHorizontalDistance)}`,
    `AB_GPS_DISTANCE_M=${fmtN(pair("AB")?.gpsDistanceM)}`,
    `AB_SCALE=${fmtN(pair("AB")?.worldUnitsPerMeter)} (${SCALE_CONVENTION})`,
    "",
    `AC_WORLD_HORIZONTAL_DISTANCE=${fmtN(pair("AC")?.worldHorizontalDistance)}`,
    `AC_GPS_DISTANCE_M=${fmtN(pair("AC")?.gpsDistanceM)}`,
    `AC_SCALE=${fmtN(pair("AC")?.worldUnitsPerMeter)} (${SCALE_CONVENTION})`,
    "",
    `BC_WORLD_HORIZONTAL_DISTANCE=${fmtN(pair("BC")?.worldHorizontalDistance)}`,
    `BC_GPS_DISTANCE_M=${fmtN(pair("BC")?.gpsDistanceM)}`,
    `BC_SCALE=${fmtN(pair("BC")?.worldUnitsPerMeter)} (${SCALE_CONVENTION})`,
    "",
    `AB_TO_C_ERROR_M=${fmtN(loo.abToCErrorM)}`,
    `AC_TO_B_ERROR_M=${fmtN(loo.acToBErrorM)}`,
    `BC_TO_A_ERROR_M=${fmtN(loo.bcToAErrorM)}`,
    "",
    `LIKELY_BAD_POINT=${loo.likelyBadPoint}`,
    "",
    `PACKAGE_SCALE_EXPECTED=${PACKAGE_EXPECTED_METERS_PER_WORLD_UNIT} (METERS_PER_WORLD_UNIT; package ${activeOdessaPackage().id})`,
    `SOLVER_SCALE=${fmtN(solverScale)} (${SCALE_CONVENTION})`,
    `SCALE_STATUS=${scaleStatus}`,
    "",
    `CURRENT_AXIS_MAPPING=${currentAxis}`,
    `BEST_AXIS_MAPPING=${best?.label ?? "—"}`,
    `BEST_AXIS_HORIZONTAL_RMS=${fmtN(best?.horizontalRmsM)}`,
    "",
    `PICK_COORDINATE_SPACE=${pickSpace}`,
    `MODEL_ROOT_POSITION=${fmtWorld(root.position)}`,
    `MODEL_ROOT_ROTATION=${fmtWorld(root.rotation)}`,
    `MODEL_ROOT_SCALE=${fmtWorld(root.scale)}`,
    modelRootWarning(root) ? `MODEL_ROOT_WARNING=${modelRootWarning(root)}` : "MODEL_ROOT_WARNING=NONE",
    "",
    `CHECK_WORLD=${fmtWorld(chk.world)}`,
    `CHECK_ACTUAL_GPS=${fmtGps(chk.actual)}`,
    `CHECK_PREDICTED_GPS=${fmtGps(chk.predicted)}`,
    `CHECK_ERROR_M=${fmtN(chk.errorM)}`,
    `CHECK_EAST_ERROR_M=${fmtN(chk.eastErrorM)}`,
    `CHECK_NORTH_ERROR_M=${fmtN(chk.northErrorM)}`,
    "",
    `AB_SOLVER_TO_CHECK_ERROR_M=${fmtN(chk.abSolverToCheckErrorM)}`,
    `AC_SOLVER_TO_CHECK_ERROR_M=${fmtN(chk.acSolverToCheckErrorM)}`,
    `BC_SOLVER_TO_CHECK_ERROR_M=${fmtN(chk.bcSolverToCheckErrorM)}`,
    "",
    "=== END GEOREFERENCE DIAGNOSTIC V3 ===",
  ].join("\n");
}
