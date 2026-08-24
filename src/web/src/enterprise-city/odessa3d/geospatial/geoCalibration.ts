/**
 * Control-point calibration solver. Uniform scale + yaw + translation only.
 * Never deforms city GLB geometry.
 */

import type {
  AuthoredCalibrationRecord,
  AxisMapping,
  CalibrationNeed,
  CalibrationQuality,
  CalibrationSolveResult,
  GeoCalibration,
  GeoControlPoint,
  GeoCoordinate,
  GeoreferenceStatus,
  LocalWorldCoordinate,
  PointErrorMeters,
} from "./types";
import { IDENTITY_AXIS_MAPPING, mappedHorizontalAxes, UNCALIBRATED_GEOTRANSFORM_AXES } from "./worldTransform";
import { geoToWorld, worldToGeo } from "./worldTransform";
import { horizontalDistanceMeters, isFiniteGeo, wgs84ToLocalMeters } from "./localMeters";
import { ODESSA_ENU_ORIGIN } from "./localMeters";

/** Empty until survey/GPS control points are authored. Do not guess. */
export const AUTHORED_GEO_CONTROL_POINTS: readonly GeoControlPoint[] = [];

export const DEFAULT_CALIBRATION_NEEDS: CalibrationNeed[] = [
  {
    code: "control_point_a",
    detail: "Known model world (X,Y,Z) plus a measured WGS84 (lat, lon) at the same physical location",
  },
  {
    code: "control_point_b",
    detail: "Second control point, hundreds of meters from the first, for scale and yaw",
  },
  {
    code: "control_point_c",
    detail: "Third control point for residual validation (recommended)",
  },
  {
    code: "axis_confirm",
    detail: "Confirm ground axes: Blender export is Y-up / XZ map; uncalibrated GeoTransform assumed east=+X north=−Z",
  },
  {
    code: "unit_confirm",
    detail: "Confirm whether one world unit is one meter (REBUILT_METRIC cityBounds span ~73.5 × 104.8 km)",
  },
];

export const MIN_SEPARATION_M = 20;
export const RECOMMENDED_SEPARATION_M = 500;
export const MIN_WORLD_SEPARATION = 2;
export const AUTHORED_CALIBRATION_SOURCE = "AUTHORED_CONTROL_POINTS";

/** Candidate ground mappings (Y-up). Rotation cannot absorb a reflection. */
export const HORIZONTAL_AXIS_CANDIDATES: readonly AxisMapping[] = [
  IDENTITY_AXIS_MAPPING,
  UNCALIBRATED_GEOTRANSFORM_AXES,
  { east: "-x", north: "z", up: "y" },
  { east: "-x", north: "-z", up: "y" },
  { east: "z", north: "x", up: "y" },
  { east: "z", north: "-x", up: "y" },
  { east: "-z", north: "x", up: "y" },
  { east: "-z", north: "-x", up: "y" },
];

export function qualityFromError(maxErrorMeters: number, meanErrorMeters: number): CalibrationQuality {
  if (!Number.isFinite(maxErrorMeters) || !Number.isFinite(meanErrorMeters)) return "INVALID";
  if (maxErrorMeters < 2 && meanErrorMeters < 2) return "EXCELLENT";
  if (maxErrorMeters <= 5) return "GOOD";
  if (maxErrorMeters <= 15) return "ACCEPTABLE";
  return "POOR";
}

function statusFromQuality(quality: CalibrationQuality, pointCount: number): GeoreferenceStatus {
  if (pointCount < 3 && (quality === "EXCELLENT" || quality === "GOOD" || quality === "ACCEPTABLE" || quality === "POOR")) {
    return "PROVISIONAL";
  }
  switch (quality) {
    case "EXCELLENT":
    case "GOOD":
      return "READY_CALIBRATED";
    case "ACCEPTABLE":
      return "READY_APPROXIMATE";
    case "POOR":
      return "CALIBRATION_POOR";
    case "UNAVAILABLE":
      return "CALIBRATION_REQUIRED";
    default:
      return "INVALID";
  }
}

function meanWorld(points: GeoControlPoint[]): LocalWorldCoordinate {
  const n = points.length;
  let x = 0;
  let y = 0;
  let z = 0;
  for (const p of points) {
    x += p.world.x;
    y += p.world.y;
    z += p.world.z;
  }
  return { x: x / n, y: y / n, z: z / n };
}

function meanGeo(points: GeoControlPoint[]): GeoCoordinate {
  const n = points.length;
  let lat = 0;
  let lon = 0;
  let alt = 0;
  let altN = 0;
  for (const p of points) {
    lat += p.geo.lat;
    lon += p.geo.lon;
    if (p.geo.altitude != null) {
      alt += p.geo.altitude;
      altN += 1;
    }
  }
  const origin: GeoCoordinate = { lat: lat / n, lon: lon / n };
  if (altN) origin.altitude = alt / altN;
  return origin;
}

export function canPersistQuality(quality: CalibrationQuality, allowPoor = false): boolean {
  if (quality === "EXCELLENT" || quality === "GOOD" || quality === "ACCEPTABLE") return true;
  return allowPoor && quality === "POOR";
}

function emptySolve(
  extras: Partial<CalibrationSolveResult> & Pick<CalibrationSolveResult, "status" | "quality" | "reasons">,
): CalibrationSolveResult {
  return {
    calibration: null,
    controlPointCount: 0,
    meanErrorMeters: null,
    meanErrorMeters3d: null,
    maxErrorMeters3d: null,
    maxErrorMeters: null,
    independentResidualMeters: null,
    scale: null,
    rotation: null,
    origin: null,
    worldOrigin: null,
    needs: [...DEFAULT_CALIBRATION_NEEDS],
    ...extras,
  };
}

export function solveCalibrationFromControlPoints(
  points: readonly GeoControlPoint[],
  source = "control_points",
  axisMapping: AxisMapping = IDENTITY_AXIS_MAPPING,
): CalibrationSolveResult {
  const needs = [...DEFAULT_CALIBRATION_NEEDS];
  const valid = points.filter((p) => isFiniteGeo(p.geo) && Number.isFinite(p.world.x) && Number.isFinite(p.world.z));
  if (valid.length < 2) {
    return emptySolve({
      status: "CALIBRATION_REQUIRED",
      quality: "UNAVAILABLE",
      controlPointCount: valid.length,
      reasons: ["need_at_least_2_control_points"],
      needs,
    });
  }

  const origin = meanGeo(valid);
  const worldOrigin = meanWorld(valid);
  const src: Array<{ e: number; n: number }> = [];
  const dst: Array<{ x: number; z: number }> = [];
  for (const p of valid) {
    const enu = wgs84ToLocalMeters(p.geo, origin);
    src.push({ e: enu.east, n: enu.north });
    const mapped = mappedHorizontalAxes(
      { x: p.world.x - worldOrigin.x, y: p.world.y - worldOrigin.y, z: p.world.z - worldOrigin.z },
      axisMapping,
    );
    dst.push({ x: mapped.east, z: mapped.north });
  }

  let maxPair = 0;
  let maxWorld = 0;
  for (let i = 0; i < valid.length; i++) {
    for (let j = i + 1; j < valid.length; j++) {
      const d = horizontalDistanceMeters(
        wgs84ToLocalMeters(valid[i].geo, origin),
        wgs84ToLocalMeters(valid[j].geo, origin),
      );
      if (d > maxPair) maxPair = d;
      const w = Math.hypot(valid[i].world.x - valid[j].world.x, valid[i].world.z - valid[j].world.z);
      if (w > maxWorld) maxWorld = w;
    }
  }
  if (maxPair < MIN_SEPARATION_M) {
    return emptySolve({
      status: "INVALID",
      quality: "INVALID",
      controlPointCount: valid.length,
      origin,
      worldOrigin,
      reasons: [`control_points_too_close:${maxPair.toFixed(1)}m`, "degenerate_pair"],
      needs,
    });
  }
  if (maxWorld < MIN_WORLD_SEPARATION) {
    return emptySolve({
      status: "INVALID",
      quality: "INVALID",
      controlPointCount: valid.length,
      origin,
      worldOrigin,
      reasons: [`world_points_too_close:${maxWorld.toFixed(2)}`, "degenerate_pair"],
      needs,
    });
  }

  let dot = 0;
  let cross = 0;
  let srcVar = 0;
  let dstVar = 0;
  for (let i = 0; i < src.length; i++) {
    dot += src[i].e * dst[i].x + src[i].n * dst[i].z;
    cross += src[i].e * dst[i].z - src[i].n * dst[i].x;
    srcVar += src[i].e * src[i].e + src[i].n * src[i].n;
    dstVar += dst[i].x * dst[i].x + dst[i].z * dst[i].z;
  }
  if (srcVar < 1e-6) {
    return emptySolve({
      status: "INVALID",
      quality: "INVALID",
      controlPointCount: valid.length,
      origin,
      worldOrigin,
      reasons: ["degenerate_geo_spread", "degenerate_pair"],
      needs,
    });
  }
  if (dstVar < 1e-6) {
    return emptySolve({
      status: "INVALID",
      quality: "INVALID",
      controlPointCount: valid.length,
      origin,
      worldOrigin,
      reasons: ["degenerate_world_spread", "degenerate_pair"],
      needs,
    });
  }

  const rotation = Math.atan2(cross, dot);
  const c = Math.cos(rotation);
  const s = Math.sin(rotation);
  let rotatedDot = 0;
  for (let i = 0; i < src.length; i++) {
    const re = src[i].e * c - src[i].n * s;
    const rn = src[i].e * s + src[i].n * c;
    rotatedDot += re * dst[i].x + rn * dst[i].z;
  }
  const worldPerMeter = rotatedDot / srcVar;
  if (!Number.isFinite(worldPerMeter) || worldPerMeter <= 1e-9) {
    return emptySolve({
      status: "INVALID",
      quality: "INVALID",
      controlPointCount: valid.length,
      origin,
      worldOrigin,
      rotation,
      reasons: [worldPerMeter < 0 ? "reflected_scale" : "degenerate_scale", "degenerate_pair"],
      needs,
    });
  }
  const metersPerWorldUnit = 1 / worldPerMeter;

  const calibration: GeoCalibration = {
    origin,
    worldOrigin,
    metersPerWorldUnit,
    rotationRadians: rotation,
    axisMapping,
    source,
    confidence: "CALIBRATED",
  };

  let errSum = 0;
  let errMax = 0;
  let errSum3d = 0;
  let errMax3d = 0;
  const pointErrors: PointErrorMeters[] = [];
  for (const p of valid) {
    const pred = geoToWorld(p.geo, calibration);
    const dx = pred.x - p.world.x;
    const dy = pred.y - p.world.y;
    const dz = pred.z - p.world.z;
    const err3d = Math.hypot(dx, dy, dz) * Math.abs(metersPerWorldUnit);
    const predGeo = worldToGeo(p.world, calibration);
    const horiz = horizontalDistanceMeters(wgs84ToLocalMeters(predGeo), wgs84ToLocalMeters(p.geo));
    pointErrors.push({ id: p.id, errorMeters: horiz, horizontalErrorMeters: horiz, error3dMeters: err3d });
    errSum += horiz;
    if (horiz > errMax) errMax = horiz;
    errSum3d += err3d;
    if (err3d > errMax3d) errMax3d = err3d;
  }
  const meanErrorMeters = errSum / valid.length;
  const meanErrorMeters3d = errSum3d / valid.length;
  const quality = qualityFromError(errMax, meanErrorMeters);
  if (quality === "EXCELLENT" || quality === "GOOD") calibration.confidence = "CALIBRATED";
  if (quality === "ACCEPTABLE") calibration.confidence = "APPROXIMATE";
  if (quality === "POOR" || quality === "INVALID") calibration.confidence = "APPROXIMATE";

  const status = statusFromQuality(quality, valid.length);
  const hideCalibration = status === "INVALID" || status === "CALIBRATION_REQUIRED";
  return {
    status,
    quality,
    calibration: hideCalibration ? null : calibration,
    controlPointCount: valid.length,
    meanErrorMeters,
    maxErrorMeters: errMax,
    meanErrorMeters3d,
    maxErrorMeters3d: errMax3d,
    independentResidualMeters: null,
    scale: worldPerMeter,
    rotation,
    origin,
    worldOrigin,
    pointErrors,
    reasons:
      status === "CALIBRATION_POOR"
        ? ["residual_too_high", "CALIBRATION_POOR"]
        : status === "PROVISIONAL"
          ? ["provisional_two_point_solve"]
          : ["solved_from_control_points"],
    needs: status === "READY_CALIBRATED" || status === "READY_APPROXIMATE" ? [] : needs,
  };
}

export function solveCalibrationWithAxisInference(
  points: readonly GeoControlPoint[],
  source = "control_points",
): CalibrationSolveResult {
  let best: CalibrationSolveResult | null = null;
  for (const mapping of HORIZONTAL_AXIS_CANDIDATES) {
    const solved = solveCalibrationFromControlPoints(points, source, mapping);
    if (!solved.calibration || (solved.scale ?? 0) <= 0) continue;
    if (
      !best ||
      (solved.meanErrorMeters ?? Infinity) < (best.meanErrorMeters ?? Infinity) - 1e-6 ||
      (Math.abs((solved.meanErrorMeters ?? 0) - (best.meanErrorMeters ?? 0)) < 1e-6 &&
        Math.abs(solved.rotation ?? 0) < Math.abs(best.rotation ?? 0))
    ) {
      best = solved;
    }
  }
  if (best) {
    return { ...best, reasons: [...best.reasons, "axis_inferred"] };
  }
  return solveCalibrationFromControlPoints(points, source);
}

export function independentHoldoutResidual(
  fitPoints: readonly GeoControlPoint[],
  heldOut: GeoControlPoint,
): number | null {
  const solved = solveCalibrationWithAxisInference(fitPoints);
  if (!solved.calibration) return null;
  const predGeo = worldToGeo(heldOut.world, solved.calibration);
  return horizontalDistanceMeters(wgs84ToLocalMeters(predGeo), wgs84ToLocalMeters(heldOut.geo));
}

export type ManifestGeoHint = {
  originLat?: number;
  originLng?: number;
  calibrated?: boolean;
};

/**
 * Authoritative resolver. A manifest `calibrated: false` flag and an approximate
 * city-center lat/lng do NOT constitute a model-to-WGS84 transform.
 */
export function resolveOdessaCalibration(input: {
  controlPoints?: readonly GeoControlPoint[];
  manifest?: ManifestGeoHint;
  saved?: AuthoredCalibrationRecord | null;
  currentFingerprint?: string | null;
}): CalibrationSolveResult {
  const saved = input.saved;
  if (saved) {
    if (
      input.currentFingerprint &&
      saved.modelFingerprint &&
      saved.modelFingerprint !== input.currentFingerprint
    ) {
      return emptySolve({
        status: "CALIBRATION_MODEL_MISMATCH",
        quality: saved.quality ?? "UNAVAILABLE",
        controlPointCount: saved.controlPoints?.length ?? 0,
        origin: saved.origin ?? null,
        worldOrigin: saved.worldOrigin ?? null,
        scale: saved.scale ?? null,
        rotation: saved.rotationRadians ?? null,
        meanErrorMeters: saved.meanErrorMeters ?? null,
        maxErrorMeters: saved.maxErrorMeters ?? null,
        reasons: ["CALIBRATION_MODEL_MISMATCH", "model_fingerprint_changed"],
      });
    }
    const solved = solveCalibrationWithAxisInference(saved.controlPoints, AUTHORED_CALIBRATION_SOURCE);
    if (!solved.calibration || !canPersistQuality(solved.quality, saved.quality === "POOR")) {
      return {
        ...solved,
        status: solved.quality === "POOR" ? "CALIBRATION_POOR" : "CALIBRATION_REQUIRED",
        calibration: null,
        reasons: [...solved.reasons, "saved_calibration_failed_revalidation"],
      };
    }
    return {
      ...solved,
      status: solved.quality === "POOR" ? "CALIBRATION_POOR" : "READY_CALIBRATED",
      calibration: {
        ...solved.calibration,
        source: AUTHORED_CALIBRATION_SOURCE,
        confidence: solved.quality === "POOR" ? "APPROXIMATE" : "CALIBRATED",
      },
      reasons: [...solved.reasons, "restored_authored_calibration"],
    };
  }

  const points = input.controlPoints ?? AUTHORED_GEO_CONTROL_POINTS;
  if (points.length >= 2) return solveCalibrationWithAxisInference(points);

  const reasons = ["no_control_points"];
  if (input.manifest?.calibrated === false) reasons.push("manifest_calibrated_false");
  if (input.manifest?.calibrated === true) {
    reasons.push("manifest_calibrated_true_but_missing_world_origin_scale_rotation");
  }
  reasons.push("approximate_city_center_is_not_model_georeference");

  return emptySolve({
    status: "CALIBRATION_REQUIRED",
    quality: "UNAVAILABLE",
    controlPointCount: points.length,
    origin:
      input.manifest?.originLat != null && input.manifest.originLng != null
        ? { lat: input.manifest.originLat, lon: input.manifest.originLng }
        : { ...ODESSA_ENU_ORIGIN },
    reasons,
  });
}

export function overlaysEnabled(status: GeoreferenceStatus): boolean {
  return status === "READY_EXACT" || status === "READY_CALIBRATED" || status === "READY_APPROXIMATE";
}

export function clickGeoEnabled(status: GeoreferenceStatus): boolean {
  return overlaysEnabled(status);
}
