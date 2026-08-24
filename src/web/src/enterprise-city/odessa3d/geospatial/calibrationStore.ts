/**
 * Authored calibration persistence. localStorage only — never writes GLB/manifest.
 */

import type {
  AuthoredCalibrationRecord,
  AxisMapping,
  CalibrationModelRoot,
  GeoControlPoint,
  GeoCoordinate,
  GeoOrigin,
  LocalWorldCoordinate,
  PointErrorMeters,
  RawControlObservation,
} from "./types";
import { AUTHORED_CALIBRATION_SOURCE, canPersistQuality } from "./geoCalibration";
import { ODESSA_GEO_ORIGIN } from "./localMeters";
import { IDENTITY_MODEL_ROOT, type ModelRootTransform } from "./calibrationDiagnostics";

export const AUTHORED_CALIBRATION_STORAGE_KEY_V1 = "ados.odessa3d.authored_calibration.v1";
export const AUTHORED_CALIBRATION_STORAGE_KEY = "ados.odessa3d.georeference.v2";
export const AUTHORED_CALIBRATION_STORAGE_KEY_V3 = "ados.odessa3d.georeference.v3";
export const RAW_OBSERVATIONS_STORAGE_KEY = "ados.odessa3d.georeference.observations.v3";

export type CalibrationStorage = {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
};

export type ImportCalibrationResult =
  | { ok: true; record: AuthoredCalibrationRecord }
  | { ok: false; error: string };

function browserStorage(): CalibrationStorage | null {
  try {
    if (typeof localStorage === "undefined") return null;
    return localStorage;
  } catch {
    return null;
  }
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}

function isNum(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function isHorizontalAxis(v: unknown): v is AxisMapping["east"] {
  return v === "x" || v === "-x" || v === "z" || v === "-z";
}

function parseGeo(v: unknown): GeoCoordinate | null {
  if (!isRecord(v) || !isNum(v.lat) || !isNum(v.lon)) return null;
  if (Math.abs(v.lat) > 90 || Math.abs(v.lon) > 180) return null;
  const geo: GeoCoordinate = { lat: v.lat, lon: v.lon };
  if (v.altitude != null) {
    if (!isNum(v.altitude)) return null;
    geo.altitude = v.altitude;
  }
  return geo;
}

function parseWorld(v: unknown): LocalWorldCoordinate | null {
  if (!isRecord(v) || !isNum(v.x) || !isNum(v.y) || !isNum(v.z)) return null;
  return { x: v.x, y: v.y, z: v.z };
}

function parsePoint(v: unknown): GeoControlPoint | null {
  if (!isRecord(v) || typeof v.id !== "string") return null;
  const geo = parseGeo(v.geo);
  const world = parseWorld(v.world);
  if (!geo || !world) return null;
  const point: GeoControlPoint = { id: v.id, geo, world, coordinateSpace: "world" };
  if (v.label != null) {
    if (typeof v.label !== "string") return null;
    point.label = v.label;
  }
  if (typeof v.pickedAt === "string") point.pickedAt = v.pickedAt;
  return point;
}

function parseObservation(v: unknown): RawControlObservation | null {
  if (!isRecord(v) || typeof v.id !== "string") return null;
  const world = v.world == null ? null : parseWorld(v.world);
  const gps = v.gps == null && v.geo == null ? null : parseGeo(v.gps ?? v.geo);
  if (v.world != null && !world) return null;
  if ((v.gps != null || v.geo != null) && !gps) return null;
  return {
    id: v.id,
    world,
    gps,
    pickedAt: typeof v.pickedAt === "string" ? v.pickedAt : null,
    coordinateSpace: "world",
  };
}

function parseModelRoot(v: unknown): CalibrationModelRoot | null {
  if (!isRecord(v)) return null;
  const position = parseWorld(v.position);
  const rotation = parseWorld(v.rotation);
  const scale = parseWorld(v.scale);
  if (!position || !rotation || !scale) return null;
  return { position, rotation, scale };
}

export function observationsFromControlPoints(points: readonly GeoControlPoint[]): RawControlObservation[] {
  return points.map((p) => ({
    id: p.id,
    world: { ...p.world },
    gps: { ...p.geo },
    pickedAt: p.pickedAt ?? null,
    coordinateSpace: "world" as const,
  }));
}

function parseAxisMapping(v: unknown): AxisMapping | null {
  if (!isRecord(v) || !isHorizontalAxis(v.east) || !isHorizontalAxis(v.north)) return null;
  if (v.up !== "y" && v.up !== "-y") return null;
  return { east: v.east, north: v.north, up: v.up };
}

export function parseAuthoredCalibration(raw: unknown): ImportCalibrationResult {
  if (!isRecord(raw)) return { ok: false, error: "invalid_json_root" };
  if (raw.version !== 1 && raw.version !== 2 && raw.version !== 3 && raw.version !== 4) {
    return { ok: false, error: "unsupported_version" };
  }
  if (raw.source !== AUTHORED_CALIBRATION_SOURCE) return { ok: false, error: "invalid_source" };
  if (raw.confidence !== "CALIBRATED") return { ok: false, error: "invalid_confidence" };
  if (typeof raw.timestamp !== "string" || !raw.timestamp) return { ok: false, error: "invalid_timestamp" };
  if (typeof raw.modelFingerprint !== "string" || !raw.modelFingerprint) {
    return { ok: false, error: "invalid_model_fingerprint" };
  }
  if (!Array.isArray(raw.controlPoints) || raw.controlPoints.length < 2) {
    return { ok: false, error: "invalid_control_points" };
  }
  const controlPoints: GeoControlPoint[] = [];
  for (const item of raw.controlPoints) {
    const p = parsePoint(item);
    if (!p) return { ok: false, error: "invalid_control_point" };
    controlPoints.push(p);
  }
  const origin = parseGeo(raw.origin);
  const worldOrigin = parseWorld(raw.worldOrigin);
  const translation = parseWorld(raw.translation) ?? worldOrigin;
  const axisMapping = parseAxisMapping(raw.axisMapping);
  if (!origin || !worldOrigin || !translation || !axisMapping) return { ok: false, error: "invalid_transform" };
  if (!isNum(raw.rotationRadians) || !isNum(raw.metersPerWorldUnit) || !isNum(raw.scale)) {
    return { ok: false, error: "invalid_transform" };
  }
  if (raw.metersPerWorldUnit <= 0 || raw.scale <= 0) return { ok: false, error: "invalid_scale" };
  const quality = raw.quality;
  if (
    quality !== "EXCELLENT" &&
    quality !== "GOOD" &&
    quality !== "ACCEPTABLE" &&
    quality !== "POOR" &&
    quality !== "INVALID" &&
    quality !== "UNAVAILABLE"
  ) {
    return { ok: false, error: "invalid_quality" };
  }
  if (!canPersistQuality(quality, quality === "POOR")) return { ok: false, error: "quality_not_acceptable" };
  if (!isNum(raw.meanErrorMeters) || !isNum(raw.maxErrorMeters)) return { ok: false, error: "invalid_errors" };
  let independentResidualMeters: number | null | undefined;
  if (raw.independentResidualMeters != null) {
    if (raw.independentResidualMeters !== null && !isNum(raw.independentResidualMeters)) {
      return { ok: false, error: "invalid_independent_residual" };
    }
    independentResidualMeters = raw.independentResidualMeters as number | null;
  }
  let geoOrigin: GeoOrigin | undefined;
  if (raw.geoOrigin != null) {
    if (!isRecord(raw.geoOrigin) || !isNum(raw.geoOrigin.referenceLat) || !isNum(raw.geoOrigin.referenceLon)) {
      return { ok: false, error: "invalid_geo_origin" };
    }
    geoOrigin = {
      referenceLat: raw.geoOrigin.referenceLat,
      referenceLon: raw.geoOrigin.referenceLon,
      referenceAltitude: isNum(raw.geoOrigin.referenceAltitude) ? raw.geoOrigin.referenceAltitude : 0,
    };
  }
  let pointErrors: PointErrorMeters[] | undefined;
  if (Array.isArray(raw.pointErrors)) {
    pointErrors = raw.pointErrors.flatMap((row) => {
      if (!isRecord(row) || typeof row.id !== "string" || !isNum(row.errorMeters)) return [];
      const item: PointErrorMeters = { id: row.id, errorMeters: row.errorMeters };
      if (isNum(row.horizontalErrorMeters)) item.horizontalErrorMeters = row.horizontalErrorMeters;
      if (isNum(row.error3dMeters)) item.error3dMeters = row.error3dMeters;
      return [item];
    });
  }
  let observations = observationsFromControlPoints(controlPoints);
  if (Array.isArray(raw.observations)) {
    const parsedObs = raw.observations.map(parseObservation).filter((o): o is RawControlObservation => !!o);
    if (parsedObs.length) observations = parsedObs;
  }
  const modelRoot = raw.modelRoot != null ? parseModelRoot(raw.modelRoot) : undefined;
  const version = raw.version === 4 ? 4 : raw.version === 3 ? 3 : raw.version === 2 ? 2 : 1;
  return {
    ok: true,
    record: {
      version,
      source: AUTHORED_CALIBRATION_SOURCE,
      confidence: "CALIBRATED",
      timestamp: raw.timestamp,
      modelFingerprint: raw.modelFingerprint,
      controlPoints,
      observations,
      schemaVersion: version === 4 ? 4 : 3,
      independentChecks: Array.isArray(raw.independentChecks)
        ? raw.independentChecks.map(parseObservation).filter((o): o is RawControlObservation => !!o)
        : undefined,
      solverVersion: typeof raw.solverVersion === "string" ? raw.solverVersion : undefined,
      coordinateSpace: "world",
      modelRoot: modelRoot ?? undefined,
      origin,
      geoOrigin: geoOrigin ?? { ...ODESSA_GEO_ORIGIN },
      worldOrigin,
      translation,
      rotationRadians: raw.rotationRadians,
      metersPerWorldUnit: raw.metersPerWorldUnit,
      scale: raw.scale,
      axisMapping,
      quality,
      meanErrorMeters: raw.meanErrorMeters,
      maxErrorMeters: raw.maxErrorMeters,
      meanErrorMeters3d: isNum(raw.meanErrorMeters3d) ? raw.meanErrorMeters3d : null,
      maxErrorMeters3d: isNum(raw.maxErrorMeters3d) ? raw.maxErrorMeters3d : null,
      independentResidualMeters,
      pointErrors,
    },
  };
}

export function parseAuthoredCalibrationJson(text: string): ImportCalibrationResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return { ok: false, error: "invalid_json" };
  }
  if (typeof parsed === "function") return { ok: false, error: "invalid_json_root" };
  return parseAuthoredCalibration(parsed);
}

export function loadAuthoredCalibration(storage: CalibrationStorage | null = browserStorage()): AuthoredCalibrationRecord | null {
  if (!storage) return null;
  const raw =
    storage.getItem(AUTHORED_CALIBRATION_STORAGE_KEY_V3) ??
    storage.getItem(AUTHORED_CALIBRATION_STORAGE_KEY) ??
    storage.getItem(AUTHORED_CALIBRATION_STORAGE_KEY_V1);
  if (!raw) return null;
  const parsed = parseAuthoredCalibrationJson(raw);
  return parsed.ok ? parsed.record : null;
}

export function saveAuthoredCalibration(
  record: AuthoredCalibrationRecord,
  storage: CalibrationStorage | null = browserStorage(),
): boolean {
  if (!storage) return false;
  if (!canPersistQuality(record.quality, record.quality === "POOR")) return false;
  const observations = record.observations?.length
    ? record.observations
    : observationsFromControlPoints(record.controlPoints);
  const payload: AuthoredCalibrationRecord = {
    ...record,
    version: record.version === 4 ? 4 : 3,
    schemaVersion: record.version === 4 ? 4 : 3,
    coordinateSpace: "world",
    observations,
    modelRoot: record.modelRoot ?? IDENTITY_MODEL_ROOT,
    geoOrigin: record.geoOrigin ?? { ...ODESSA_GEO_ORIGIN },
  };
  const text = JSON.stringify(payload);
  storage.setItem(AUTHORED_CALIBRATION_STORAGE_KEY_V3, text);
  storage.setItem(AUTHORED_CALIBRATION_STORAGE_KEY, text);
  return true;
}

export type RawObservationBundle = {
  schemaVersion: 3;
  coordinateSpace: "world";
  updatedAt: string;
  modelRoot: ModelRootTransform;
  observations: RawControlObservation[];
  check: RawControlObservation | null;
};

export function saveRawObservations(
  bundle: Omit<RawObservationBundle, "schemaVersion" | "coordinateSpace" | "updatedAt"> & {
    updatedAt?: string;
  },
  storage: CalibrationStorage | null = browserStorage(),
): boolean {
  if (!storage) return false;
  const payload: RawObservationBundle = {
    schemaVersion: 3,
    coordinateSpace: "world",
    updatedAt: bundle.updatedAt ?? new Date().toISOString(),
    modelRoot: bundle.modelRoot ?? IDENTITY_MODEL_ROOT,
    observations: bundle.observations,
    check: bundle.check ?? null,
  };
  storage.setItem(RAW_OBSERVATIONS_STORAGE_KEY, JSON.stringify(payload));
  return true;
}

export function loadRawObservations(storage: CalibrationStorage | null = browserStorage()): RawObservationBundle | null {
  if (!storage) return null;
  const raw = storage.getItem(RAW_OBSERVATIONS_STORAGE_KEY);
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as unknown;
      if (isRecord(parsed) && Array.isArray(parsed.observations)) {
        const observations = parsed.observations
          .map(parseObservation)
          .filter((o): o is RawControlObservation => !!o);
        const check = parsed.check ? parseObservation(parsed.check) : null;
        return {
          schemaVersion: 3,
          coordinateSpace: "world",
          updatedAt: typeof parsed.updatedAt === "string" ? parsed.updatedAt : "",
          modelRoot: parseModelRoot(parsed.modelRoot) ?? IDENTITY_MODEL_ROOT,
          observations,
          check,
        };
      }
    } catch {
      /* fall through to authored record */
    }
  }
  const authored = loadAuthoredCalibration(storage);
  if (!authored?.controlPoints?.length) return null;
  return {
    schemaVersion: 3,
    coordinateSpace: "world",
    updatedAt: authored.timestamp,
    modelRoot: authored.modelRoot ?? IDENTITY_MODEL_ROOT,
    observations: authored.observations?.length
      ? authored.observations
      : observationsFromControlPoints(authored.controlPoints),
    check: null,
  };
}

/** Removes authored calibration and raw observations only. Model is unchanged. */
export function resetAuthoredCalibration(storage: CalibrationStorage | null = browserStorage()): void {
  storage?.removeItem(AUTHORED_CALIBRATION_STORAGE_KEY);
  storage?.removeItem(AUTHORED_CALIBRATION_STORAGE_KEY_V1);
  storage?.removeItem(AUTHORED_CALIBRATION_STORAGE_KEY_V3);
  storage?.removeItem(RAW_OBSERVATIONS_STORAGE_KEY);
}

export function exportAuthoredCalibrationJson(record: AuthoredCalibrationRecord): string {
  return JSON.stringify(record, null, 2);
}

export function importAuthoredCalibrationJson(text: string): ImportCalibrationResult {
  return parseAuthoredCalibrationJson(text);
}
