/**
 * Cached georeference runtime: calibration, conversions, anchors, diagnostics.
 * Cheap lookups. Recalibration is explicit, never per frame.
 */

import type { CityEntity } from "../types";
import type {
  AuthoredCalibrationRecord,
  BoundsClass,
  CalibrationSolveResult,
  GeoAnchor,
  GeoBounds,
  GeoCalibration,
  GeoCoordinate,
  GeoreferenceStatus,
  LocalWorldCoordinate,
  WorldBox,
} from "./types";
import { overlaysEnabled, resolveOdessaCalibration } from "./geoCalibration";
import { loadAuthoredCalibration } from "./calibrationStore";
import { cacheAnchorWorlds, collectEnterpriseAnchors, DEV_GEO_ANCHORS } from "./geoAnchors";
import { classifyGeoAgainstBounds, worldBoxToGeoBounds } from "./geoBounds";
import { geoToWorld, worldToGeo, describeAxisMapping, UNCALIBRATED_GEOTRANSFORM_AXES } from "./worldTransform";
import { formatLatLon, isFiniteGeo, ODESSA_ENU_ORIGIN } from "./localMeters";
import type { CachedAnchor } from "./geoAnchors";

export const ALTITUDE_POLICY = {
  terrainElevationKnown: false as const,
  visualOffsetWorld: 2.4,
  preserveAltitudeForTrackers: true as const,
};

export type GeoreferenceDiagnostics = {
  status: GeoreferenceStatus;
  source: string;
  confidence: string;
  originLat: number | null;
  originLon: number | null;
  worldOrigin: LocalWorldCoordinate | null;
  metersPerWorldUnit: number | null;
  rotation: number | null;
  axisMapping: string;
  controlPoints: number;
  meanError: number | null;
  maxError: number | null;
  quality: string;
  modelGeoBounds: GeoBounds | null;
  anchors: number;
  inBounds: number;
  outOfBounds: number;
  selectedWorld: LocalWorldCoordinate | null;
  selectedGeo: GeoCoordinate | null;
  cameraGeo: GeoCoordinate | null;
  cameraWorld: LocalWorldCoordinate | null;
  cameraTargetWorld: LocalWorldCoordinate | null;
  cameraTargetGeo: GeoCoordinate | null;
  overlays: boolean;
  reasons: string[];
  modelFingerprint: string | null;
  modelMismatch: boolean;
};

let warnedCalibration = false;

export class GeoReferenceRuntime {
  private solve: CalibrationSolveResult;
  private cachedAnchors: CachedAnchor[] = [];
  private geoBounds: GeoBounds | null = null;
  private worldBox: WorldBox | null = null;

  private currentFingerprint: string | null = null;

  constructor() {
    this.solve = resolveOdessaCalibration({});
  }

  resolve(input?: {
    originLat?: number;
    originLng?: number;
    calibrated?: boolean;
    loadPersisted?: boolean;
    currentFingerprint?: string | null;
    saved?: AuthoredCalibrationRecord | null;
  }) {
    this.currentFingerprint = input?.currentFingerprint ?? this.currentFingerprint;
    let saved = input?.saved;
    if (saved === undefined && input?.loadPersisted) {
      saved = loadAuthoredCalibration();
    }
    this.solve = resolveOdessaCalibration({
      manifest: input
        ? { originLat: input.originLat, originLng: input.originLng, calibrated: input.calibrated }
        : undefined,
      saved: saved ?? undefined,
      currentFingerprint: this.currentFingerprint,
    });
    if (!overlaysEnabled(this.solve.status) && !warnedCalibration) {
      warnedCalibration = true;
      console.warn(
        `[Odessa3D] georeference ${this.solve.status}: ${this.solve.reasons.join("; ")}. Overlays disabled.`,
      );
    }
    this.cachedAnchors = cacheAnchorWorlds(
      this.cachedAnchors.map((r) => r.anchor),
      this.calibration(),
    );
    this.refreshGeoBounds();
  }

  status(): GeoreferenceStatus {
    return this.solve.status;
  }

  overlaysOn(): boolean {
    return overlaysEnabled(this.solve.status);
  }

  calibration(): GeoCalibration | null {
    return this.solve.calibration;
  }

  solveResult(): CalibrationSolveResult {
    return this.solve;
  }

  setWorldBox(box: WorldBox | null) {
    this.worldBox = box;
    this.refreshGeoBounds();
  }

  setAnchorsFromEntities(entities: Iterable<CityEntity>) {
    const anchors = collectEnterpriseAnchors(entities);
    this.cachedAnchors = cacheAnchorWorlds([...DEV_GEO_ANCHORS, ...anchors], this.calibration());
  }

  addAnchor(anchor: GeoAnchor) {
    const next = this.cachedAnchors.map((r) => r.anchor).filter((a) => a.id !== anchor.id);
    next.push(anchor);
    this.cachedAnchors = cacheAnchorWorlds(next, this.calibration());
  }

  cached(): CachedAnchor[] {
    return this.cachedAnchors;
  }

  toWorld(coord: GeoCoordinate): LocalWorldCoordinate | null {
    const cal = this.calibration();
    if (!cal || !isFiniteGeo(coord)) return null;
    return geoToWorld(coord, cal);
  }

  toGeo(world: LocalWorldCoordinate): GeoCoordinate | null {
    const cal = this.calibration();
    if (!cal) return null;
    return worldToGeo(world, cal);
  }

  classifyAnchor(coord: GeoCoordinate): BoundsClass | null {
    if (!this.geoBounds) return null;
    return classifyGeoAgainstBounds(coord, this.geoBounds);
  }

  diagnostics(input: {
    selectedWorld?: LocalWorldCoordinate | null;
    cameraWorld?: LocalWorldCoordinate | null;
    cameraTargetWorld?: LocalWorldCoordinate | null;
  } = {}): GeoreferenceDiagnostics {
    const cal = this.calibration();
    const selectedGeo = input.selectedWorld ? this.toGeo(input.selectedWorld) : null;
    const cameraGeo = input.cameraWorld ? this.toGeo(input.cameraWorld) : null;
    const cameraTargetGeo = input.cameraTargetWorld ? this.toGeo(input.cameraTargetWorld) : null;
    let inBounds = 0;
    let outOfBounds = 0;
    for (const row of this.cachedAnchors) {
      const cls = this.classifyAnchor(row.anchor.coordinate);
      if (cls === "OUT_OF_BOUNDS") outOfBounds += 1;
      else inBounds += 1;
    }
    return {
      status: this.solve.status,
      source: cal?.source ?? "none",
      confidence: cal?.confidence ?? "UNAVAILABLE",
      originLat: this.solve.origin?.lat ?? ODESSA_ENU_ORIGIN.lat,
      originLon: this.solve.origin?.lon ?? ODESSA_ENU_ORIGIN.lon,
      worldOrigin: cal?.worldOrigin ?? null,
      metersPerWorldUnit: cal?.metersPerWorldUnit ?? null,
      rotation: cal?.rotationRadians ?? null,
      axisMapping: cal ? describeAxisMapping(cal.axisMapping) : describeAxisMapping(UNCALIBRATED_GEOTRANSFORM_AXES),
      controlPoints: this.solve.controlPointCount,
      meanError: this.solve.meanErrorMeters,
      maxError: this.solve.maxErrorMeters,
      quality: this.solve.quality,
      modelGeoBounds: this.geoBounds,
      anchors: this.cachedAnchors.length,
      inBounds,
      outOfBounds,
      selectedWorld: input.selectedWorld ?? null,
      selectedGeo,
      cameraGeo,
      cameraWorld: input.cameraWorld ?? null,
      cameraTargetWorld: input.cameraTargetWorld ?? null,
      cameraTargetGeo,
      overlays: this.overlaysOn(),
      reasons: this.solve.reasons,
      modelFingerprint: this.currentFingerprint,
      modelMismatch: this.solve.status === "CALIBRATION_MODEL_MISMATCH",
    };
  }

  private refreshGeoBounds() {
    const cal = this.calibration();
    this.geoBounds = cal && this.worldBox ? worldBoxToGeoBounds(this.worldBox, cal) : null;
  }
}

export { formatLatLon };
