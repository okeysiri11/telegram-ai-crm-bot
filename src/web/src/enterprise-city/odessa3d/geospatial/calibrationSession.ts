/**
 * Interactive 3-point calibration session. Pure functions — no Three.js.
 */

import type {
  AuthoredCalibrationRecord,
  CalibrationSlotId,
  CalibrationSolveResult,
  GeoControlPoint,
  GeoCoordinate,
  LocalWorldCoordinate,
} from "./types";
import {
  AUTHORED_CALIBRATION_SOURCE,
  MIN_SEPARATION_M,
  RECOMMENDED_SEPARATION_M,
  MIN_WORLD_SEPARATION,
  canPersistQuality,
  independentHoldoutResidual,
  solveCalibrationWithAxisInference,
} from "./geoCalibration";
import { horizontalDistanceMeters, ODESSA_GEO_ORIGIN, wgs84ToLocalMeters } from "./localMeters";
import { applyPasteToGpsFields, validateGpsInput } from "./gpsValidation";
import { worldToGeo } from "./worldTransform";

export type DraftControlPoint = {
  id: CalibrationSlotId;
  label: string;
  world: LocalWorldCoordinate | null;
  geo: GeoCoordinate | null;
  latText: string;
  lonText: string;
  pickedAt: string | null;
};

export type CalibrationDraft = Record<CalibrationSlotId, DraftControlPoint>;

export type CaptureWorldResult = { ok: true; world: LocalWorldCoordinate } | { ok: false; error: string };

export type ApplyGpsResult =
  | { ok: true; geo: GeoCoordinate; warning?: string }
  | { ok: false; error: string };

export type CalibrationEvaluation = {
  complete: GeoControlPoint[];
  duplicateError: string | null;
  provisional: CalibrationSolveResult | null;
  independentResidualMeters: number | null;
  final: CalibrationSolveResult | null;
  canSave: boolean;
  canSavePoor: boolean;
  provisionalStatus: "NONE" | "PROVISIONAL" | "INVALID";
  distances: ControlPointDistances;
  worldDistances: ControlPointDistances;
  triangleArea: number | null;
  collinear: boolean;
};

export type ControlPointDistances = {
  ab: number | null;
  ac: number | null;
  bc: number | null;
  recommendedM: number;
  shortPairs: string[];
};

export const CALIBRATION_SLOTS: CalibrationSlotId[] = ["A", "B", "C"];

export function emptyCalibrationDraft(): CalibrationDraft {
  return {
    A: { id: "A", label: "A", world: null, geo: null, latText: "", lonText: "", pickedAt: null },
    B: { id: "B", label: "B", world: null, geo: null, latText: "", lonText: "", pickedAt: null },
    C: { id: "C", label: "C", world: null, geo: null, latText: "", lonText: "", pickedAt: null },
  };
}

export function draftFromControlPoints(points: readonly GeoControlPoint[]): CalibrationDraft {
  const draft = emptyCalibrationDraft();
  for (const p of points) {
    const id = (p.label || p.id).toUpperCase();
    const slot: CalibrationSlotId | null = id === "A" || id === "B" || id === "C" ? id : null;
    if (!slot) continue;
    draft[slot] = {
      id: slot,
      label: slot,
      world: { ...p.world },
      geo: { ...p.geo },
      latText: String(p.geo.lat),
      lonText: String(p.geo.lon),
      pickedAt: p.pickedAt ?? null,
    };
  }
  return draft;
}

export function draftFromObservations(
  observations: readonly { id: string; world: LocalWorldCoordinate | null; gps?: GeoCoordinate | null; geo?: GeoCoordinate | null; pickedAt?: string | null }[],
): CalibrationDraft {
  const draft = emptyCalibrationDraft();
  for (const o of observations) {
    const id = o.id.toUpperCase();
    if (id !== "A" && id !== "B" && id !== "C") continue;
    const geo = o.gps ?? o.geo ?? null;
    draft[id] = {
      ...draft[id],
      world: o.world ? { ...o.world } : null,
      geo: geo ? { ...geo } : null,
      latText: geo ? String(geo.lat) : "",
      lonText: geo ? String(geo.lon) : "",
      pickedAt: o.pickedAt ?? null,
    };
  }
  return draft;
}

export function checkFromObservation(o: { world: LocalWorldCoordinate | null; gps?: GeoCoordinate | null; geo?: GeoCoordinate | null } | null): CheckDraft {
  if (!o) return emptyCheckDraft();
  const geo = o.gps ?? o.geo ?? null;
  return {
    world: o.world ? { ...o.world } : null,
    geo: geo ? { ...geo } : null,
    latText: geo ? String(geo.lat) : "",
    lonText: geo ? String(geo.lon) : "",
  };
}

function worldHorizDist(a: LocalWorldCoordinate, b: LocalWorldCoordinate): number {
  return Math.hypot(a.x - b.x, a.z - b.z);
}

export function captureControlWorld(
  world: LocalWorldCoordinate,
  existing: readonly (LocalWorldCoordinate | null)[],
): CaptureWorldResult {
  if (!Number.isFinite(world.x) || !Number.isFinite(world.y) || !Number.isFinite(world.z)) {
    return { ok: false, error: "invalid_world_point" };
  }
  for (const other of existing) {
    if (!other) continue;
    if (worldHorizDist(world, other) < MIN_WORLD_SEPARATION) {
      return { ok: false, error: "duplicate_world_point" };
    }
  }
  return { ok: true, world: { x: world.x, y: world.y, z: world.z } };
}

export function applyGpsPasteToSlot(
  latText: string,
  lonText: string,
  otherGeos: readonly (GeoCoordinate | null)[],
): ApplyGpsResult {
  const split = applyPasteToGpsFields(latText, lonText);
  return applyGpsToSlot(split.latText, split.lonText, otherGeos);
}

export function applyGpsToSlot(
  latText: string,
  lonText: string,
  otherGeos: readonly (GeoCoordinate | null)[],
): ApplyGpsResult {
  const parsed = validateGpsInput(latText, lonText);
  if (!parsed.ok || !parsed.geo) return { ok: false, error: parsed.error ?? "invalid_gps" };
  for (const other of otherGeos) {
    if (!other) continue;
    const d = horizontalDistanceMeters(wgs84ToLocalMeters(parsed.geo), wgs84ToLocalMeters(other));
    if (d < MIN_SEPARATION_M) return { ok: false, error: "duplicate_gps_point" };
  }
  return parsed.warning ? { ok: true, geo: parsed.geo, warning: parsed.warning } : { ok: true, geo: parsed.geo };
}

export function clearCalibrationSlot(draft: CalibrationDraft, slot: CalibrationSlotId): CalibrationDraft {
  return {
    ...draft,
    [slot]: { id: slot, label: slot, world: null, geo: null, latText: "", lonText: "", pickedAt: null },
  };
}

function pairDistance(a?: GeoControlPoint, b?: GeoControlPoint): number | null {
  if (!a || !b) return null;
  return horizontalDistanceMeters(wgs84ToLocalMeters(a.geo), wgs84ToLocalMeters(b.geo));
}

export function controlPointDistances(draft: CalibrationDraft): ControlPointDistances {
  const complete = completeControlPoints(draft);
  const a = complete.find((p) => p.id === "A");
  const b = complete.find((p) => p.id === "B");
  const c = complete.find((p) => p.id === "C");
  const ab = pairDistance(a, b);
  const ac = pairDistance(a, c);
  const bc = pairDistance(b, c);
  const shortPairs: string[] = [];
  if (ab != null && ab < RECOMMENDED_SEPARATION_M) shortPairs.push("A-B");
  if (ac != null && ac < RECOMMENDED_SEPARATION_M) shortPairs.push("A-C");
  if (bc != null && bc < RECOMMENDED_SEPARATION_M) shortPairs.push("B-C");
  return { ab, ac, bc, recommendedM: RECOMMENDED_SEPARATION_M, shortPairs };
}

export function worldHorizDistance(a: LocalWorldCoordinate, b: LocalWorldCoordinate): number {
  return worldHorizDist(a, b);
}

export function worldPairDistances(draft: CalibrationDraft): ControlPointDistances {
  const a = draft.A.world;
  const b = draft.B.world;
  const c = draft.C.world;
  const ab = a && b ? worldHorizDist(a, b) : null;
  const ac = a && c ? worldHorizDist(a, c) : null;
  const bc = b && c ? worldHorizDist(b, c) : null;
  const shortPairs: string[] = [];
  if (ab != null && ab < 40) shortPairs.push("A-B");
  if (ac != null && ac < 40) shortPairs.push("A-C");
  if (bc != null && bc < 40) shortPairs.push("B-C");
  return { ab, ac, bc, recommendedM: RECOMMENDED_SEPARATION_M, shortPairs };
}

/** Planar XZ triangle area in world units (model space). */
export function worldTriangleArea(
  a: LocalWorldCoordinate,
  b: LocalWorldCoordinate,
  c: LocalWorldCoordinate,
): number {
  return Math.abs((b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x)) / 2;
}

export function isCollinearWorld(
  a: LocalWorldCoordinate,
  b: LocalWorldCoordinate,
  c: LocalWorldCoordinate,
  minHeight = 25,
): boolean {
  const area = worldTriangleArea(a, b, c);
  const ab = worldHorizDist(a, b);
  const ac = worldHorizDist(a, c);
  const bc = worldHorizDist(b, c);
  const longest = Math.max(ab, ac, bc, 1);
  return (2 * area) / longest < minHeight;
}

export type CheckDraft = {
  world: LocalWorldCoordinate | null;
  geo: GeoCoordinate | null;
  latText: string;
  lonText: string;
};

export type CheckEvaluation = {
  predicted: GeoCoordinate | null;
  actual: GeoCoordinate | null;
  errorMeters: number | null;
  eastErrorMeters: number | null;
  northErrorMeters: number | null;
  includedInSolver: false;
};

export function emptyCheckDraft(): CheckDraft {
  return { world: null, geo: null, latText: "", lonText: "" };
}

/** Independent hold-out. Never added to A/B/C solver points. */
export function evaluateCheckPoint(
  check: CheckDraft,
  solve: CalibrationSolveResult | null,
): CheckEvaluation {
  const cal = solve?.calibration ?? null;
  if (!check.world || !cal) {
    return {
      predicted: null,
      actual: check.geo,
      errorMeters: null,
      eastErrorMeters: null,
      northErrorMeters: null,
      includedInSolver: false,
    };
  }
  const predicted = worldToGeo(check.world, cal);
  if (!check.geo) {
    return {
      predicted,
      actual: null,
      errorMeters: null,
      eastErrorMeters: null,
      northErrorMeters: null,
      includedInSolver: false,
    };
  }
  const predEnu = wgs84ToLocalMeters(predicted);
  const actEnu = wgs84ToLocalMeters(check.geo);
  const eastErrorMeters = predEnu.east - actEnu.east;
  const northErrorMeters = predEnu.north - actEnu.north;
  const errorMeters = Math.hypot(eastErrorMeters, northErrorMeters);
  return { predicted, actual: check.geo, errorMeters, eastErrorMeters, northErrorMeters, includedInSolver: false };
}

export function completeControlPoints(draft: CalibrationDraft): GeoControlPoint[] {
  const out: GeoControlPoint[] = [];
  for (const id of CALIBRATION_SLOTS) {
    const p = draft[id];
    if (!p.world || !p.geo) continue;
    out.push({ id, label: p.label, geo: p.geo, world: p.world, pickedAt: p.pickedAt ?? undefined, coordinateSpace: "world" });
  }
  return out;
}

export function evaluateCalibrationDraft(draft: CalibrationDraft): CalibrationEvaluation {
  const complete = completeControlPoints(draft);
  const a = complete.find((p) => p.id === "A");
  const b = complete.find((p) => p.id === "B");
  const c = complete.find((p) => p.id === "C");
  let duplicateError: string | null = null;
  for (let i = 0; i < complete.length; i++) {
    for (let j = i + 1; j < complete.length; j++) {
      if (worldHorizDist(complete[i].world, complete[j].world) < MIN_WORLD_SEPARATION) {
        duplicateError = "duplicate_world_point";
      }
      const d = horizontalDistanceMeters(
        wgs84ToLocalMeters(complete[i].geo),
        wgs84ToLocalMeters(complete[j].geo),
      );
      if (d < MIN_SEPARATION_M) duplicateError = "duplicate_gps_point";
    }
  }

  let provisional: CalibrationSolveResult | null = null;
  let independentResidualMeters: number | null = null;
  let final: CalibrationSolveResult | null = null;
  let provisionalStatus: CalibrationEvaluation["provisionalStatus"] = "NONE";

  if (a && b && !duplicateError) {
    provisional = solveCalibrationWithAxisInference([a, b], AUTHORED_CALIBRATION_SOURCE);
    provisionalStatus = provisional.calibration ? "PROVISIONAL" : "INVALID";
    if (c) {
      independentResidualMeters = independentHoldoutResidual([a, b], c);
      final = solveCalibrationWithAxisInference([a, b, c], AUTHORED_CALIBRATION_SOURCE);
      if (final) final = { ...final, independentResidualMeters };
    }
  }

  const distances = controlPointDistances(draft);
  const worldDistances = worldPairDistances(draft);
  const wa = draft.A.world;
  const wb = draft.B.world;
  const wc = draft.C.world;
  const triangleArea = wa && wb && wc ? worldTriangleArea(wa, wb, wc) : null;
  const collinear = !!(wa && wb && wc && isCollinearWorld(wa, wb, wc));
  const canSave = !!final?.calibration && canPersistQuality(final.quality) && complete.length >= 3 && !duplicateError;
  const canSavePoor =
    !!final?.calibration && final.quality === "POOR" && complete.length >= 3 && !duplicateError;

  return {
    complete,
    duplicateError,
    provisional,
    independentResidualMeters,
    final,
    canSave,
    canSavePoor,
    provisionalStatus,
    distances,
    worldDistances,
    triangleArea,
    collinear,
  };
}

export function buildAuthoredRecord(input: {
  solve: CalibrationSolveResult;
  controlPoints: GeoControlPoint[];
  modelFingerprint: string;
  independentResidualMeters?: number | null;
  timestamp?: string;
  allowPoor?: boolean;
  modelRoot?: AuthoredCalibrationRecord["modelRoot"];
}): AuthoredCalibrationRecord | null {
  const cal = input.solve.calibration;
  if (!cal || !canPersistQuality(input.solve.quality, input.allowPoor)) return null;
  return {
    version: 3,
    schemaVersion: 3,
    coordinateSpace: "world",
    source: AUTHORED_CALIBRATION_SOURCE,
    confidence: "CALIBRATED",
    timestamp: input.timestamp ?? new Date().toISOString(),
    modelFingerprint: input.modelFingerprint,
    controlPoints: input.controlPoints,
    origin: cal.origin,
    geoOrigin: { ...ODESSA_GEO_ORIGIN },
    worldOrigin: cal.worldOrigin,
    translation: { ...cal.worldOrigin },
    rotationRadians: cal.rotationRadians,
    metersPerWorldUnit: cal.metersPerWorldUnit,
    scale: 1 / cal.metersPerWorldUnit,
    axisMapping: cal.axisMapping,
    quality: input.solve.quality,
    modelRoot: input.modelRoot,
    observations: input.controlPoints.map((p) => ({
      id: p.id,
      world: { ...p.world },
      gps: { ...p.geo },
      pickedAt: p.pickedAt ?? null,
      coordinateSpace: "world" as const,
    })),
    meanErrorMeters: input.solve.meanErrorMeters ?? 0,
    maxErrorMeters: input.solve.maxErrorMeters ?? 0,
    meanErrorMeters3d: input.solve.meanErrorMeters3d ?? null,
    maxErrorMeters3d: input.solve.maxErrorMeters3d ?? null,
    independentResidualMeters: input.independentResidualMeters ?? input.solve.independentResidualMeters ?? null,
    pointErrors: input.solve.pointErrors,
  };
}

export function formatCalibrationSessionDebug(
  draft: CalibrationDraft,
  check: CheckDraft,
): string {
  const ev = evaluateCalibrationDraft(draft);
  const chk = evaluateCheckPoint(check, ev.final);
  const fmtP = (p: DraftControlPoint) =>
    [
      `${p.id} WORLD ${p.world ? `${p.world.x.toFixed(3)} ${p.world.y.toFixed(3)} ${p.world.z.toFixed(3)}` : "—"}`,
      `${p.id} GPS ${p.geo ? `${p.geo.lat.toFixed(6)} ${p.geo.lon.toFixed(6)}` : "—"}`,
    ].join("\n");
  return [
    fmtP(draft.A),
    fmtP(draft.B),
    fmtP(draft.C),
    `AB distance ${ev.worldDistances.ab ?? "—"}`,
    `AC distance ${ev.worldDistances.ac ?? "—"}`,
    `BC distance ${ev.worldDistances.bc ?? "—"}`,
    `triangle area ${ev.triangleArea ?? "—"}`,
    `yaw ${ev.final?.rotation ?? ev.provisional?.rotation ?? "—"}`,
    `scale ${ev.final?.scale ?? ev.provisional?.scale ?? "—"}`,
    `translation ${ev.final?.calibration ? `${ev.final.calibration.worldOrigin.x.toFixed(3)} ${ev.final.calibration.worldOrigin.z.toFixed(3)}` : "—"}`,
    `mean residual ${ev.final?.meanErrorMeters ?? "—"}`,
    `max residual ${ev.final?.maxErrorMeters ?? "—"}`,
    `CHECK predicted GPS ${chk.predicted ? `${chk.predicted.lat.toFixed(6)} ${chk.predicted.lon.toFixed(6)}` : "—"}`,
    `CHECK actual GPS ${chk.actual ? `${chk.actual.lat.toFixed(6)} ${chk.actual.lon.toFixed(6)}` : "—"}`,
    `CHECK error ${chk.errorMeters ?? "—"}`,
  ].join("\n");
}

export function copyCalibrationDebugData(point: DraftControlPoint): string {
  const lat = point.geo ? point.geo.lat.toFixed(6) : "—";
  const lon = point.geo ? point.geo.lon.toFixed(6) : "—";
  const x = point.world ? point.world.x.toFixed(3) : "—";
  const y = point.world ? point.world.y.toFixed(3) : "—";
  const z = point.world ? point.world.z.toFixed(3) : "—";
  return [
    `Label: ${point.label}`,
    `World X: ${x}`,
    `World Y: ${y}`,
    `World Z: ${z}`,
    `Latitude: ${lat}`,
    `Longitude: ${lon}`,
  ].join("\n");
}
