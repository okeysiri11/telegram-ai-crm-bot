/**
 * Geometry-only correspondence. Unique footprints + constellation consistency.
 * Size-unique in a cropped bbox is not identity.
 */

import type { GeoCalibration, GeoControlPoint, GeoCoordinate, LocalWorldCoordinate } from "./types";
import { isCollinearWorld, worldTriangleArea } from "./calibrationSession";
import { gpsHorizontalDistanceM, worldHorizontalDistance } from "./calibrationDiagnostics";
import type { OsmBuildingFootprint, OsmPolyline } from "./osmGeometry";
import { ODESSA_ENU_ORIGIN, wgs84ToLocalMeters } from "./localMeters";
import type { ModelXzSignature } from "./modelSignatures";
import { pairScaleDistribution } from "./pairScaleStats";
import { worldToGeo } from "./worldTransform";

export const FOOTPRINT_RELATIVE_TOLERANCE = 0.15;
export const MIN_UNIQUE_MATCHES_FOR_SOLVE = 3;
export const PAIR_SCALE_SPREAD_RELATIVE = 0.15;
export const MIN_MATCH_SEPARATION_M = 200;

export type OrderedFootprint = readonly [number, number];

export type GeometricMatchCandidate = {
  modelName: string;
  osmId: number;
  modelFootprint: OrderedFootprint;
  osmFootprint: OrderedFootprint;
  relativeError: number;
  world: LocalWorldCoordinate;
  geo: GeoCoordinate;
  accepted: boolean;
  reason: string;
  kind: "building" | "road";
};

export type SpatialDistribution = {
  matchedRegionCount: number;
  minWorldSeparation: number | null;
  minGpsSeparationM: number | null;
  collinear: boolean;
  triangleArea: number | null;
  ok: boolean;
};

export function orderedFootprint(a: number, b: number): OrderedFootprint {
  return a <= b ? [a, b] : [b, a];
}

export function footprintRelativeError(a: OrderedFootprint, b: OrderedFootprint): number {
  if (a[0] <= 0 || b[0] <= 0) return Infinity;
  const r0 = Math.abs(a[0] - b[0]) / Math.max(a[0], b[0]);
  const r1 = Math.abs(a[1] - b[1]) / Math.max(a[1], b[1]);
  return Math.max(r0, r1);
}

export function footprintsSimilar(a: OrderedFootprint, b: OrderedFootprint, tol = FOOTPRINT_RELATIVE_TOLERANCE): boolean {
  return footprintRelativeError(a, b) <= tol;
}

function buildingCandidates(
  model: readonly ModelXzSignature[],
  osm: readonly OsmBuildingFootprint[],
  tol: number,
): GeometricMatchCandidate[] {
  const out: GeometricMatchCandidate[] = [];
  for (const m of model) {
    const mf = orderedFootprint(m.spanX, m.spanZ);
    for (const o of osm) {
      if (o.spanEastM <= 0 || o.spanNorthM <= 0) continue;
      const of = orderedFootprint(o.spanEastM, o.spanNorthM);
      const err = footprintRelativeError(mf, of);
      if (err > tol) continue;
      out.push({
        modelName: m.name,
        osmId: o.id,
        modelFootprint: mf,
        osmFootprint: of,
        relativeError: err,
        world: { ...m.world },
        geo: { ...o.geo },
        accepted: false,
        reason: "footprint_size_candidate",
        kind: "building",
      });
    }
  }
  return out;
}

/** Bidirectional unique: each model maps to one OSM, each OSM to one model. */
export function uniqueBidirectionalMatches(
  candidates: readonly GeometricMatchCandidate[],
): { unique: GeometricMatchCandidate[]; rejected: GeometricMatchCandidate[] } {
  const byModel = new Map<string, GeometricMatchCandidate[]>();
  const byOsm = new Map<number, GeometricMatchCandidate[]>();
  for (const c of candidates) {
    const m = byModel.get(c.modelName) ?? [];
    m.push(c);
    byModel.set(c.modelName, m);
    const o = byOsm.get(c.osmId) ?? [];
    o.push(c);
    byOsm.set(c.osmId, o);
  }
  const unique: GeometricMatchCandidate[] = [];
  const rejected: GeometricMatchCandidate[] = [];
  const seen = new Set<string>();
  for (const c of candidates) {
    const key = `${c.modelName}:${c.osmId}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const modelHits = byModel.get(c.modelName) ?? [];
    const osmHits = byOsm.get(c.osmId) ?? [];
    if (modelHits.length === 1 && osmHits.length === 1) {
      unique.push({ ...c, reason: "bidirectional_unique_footprint" });
    } else {
      rejected.push({
        ...c,
        reason: modelHits.length > 1 || osmHits.length > 1 ? "ambiguous_footprint" : "not_unique",
      });
    }
  }
  return { unique, rejected };
}

export function constellationConsistent(matches: readonly GeometricMatchCandidate[]): boolean {
  if (matches.length < MIN_UNIQUE_MATCHES_FOR_SOLVE) return false;
  const points = matchesToControlPoints(matches);
  const dist = pairScaleDistribution(points);
  if (dist.count < 3 || dist.median == null || dist.mean == null) return false;
  const spread = (dist.p95 ?? dist.median) - (dist.p05 ?? dist.median);
  return spread <= PAIR_SCALE_SPREAD_RELATIVE * Math.max(Math.abs(dist.median), 0.2);
}

export function matchBuildings(
  model: readonly ModelXzSignature[],
  osm: readonly OsmBuildingFootprint[],
  tol = FOOTPRINT_RELATIVE_TOLERANCE,
): { raw: GeometricMatchCandidate[]; accepted: GeometricMatchCandidate[]; rejected: GeometricMatchCandidate[] } {
  const sized = buildingCandidates(model, osm, tol);
  const { unique, rejected: ambig } = uniqueBidirectionalMatches(sized);
  if (!constellationConsistent(unique)) {
    return {
      raw: sized,
      accepted: [],
      rejected: [
        ...ambig,
        ...unique.map((c) => ({
          ...c,
          accepted: false,
          reason: unique.length < MIN_UNIQUE_MATCHES_FOR_SOLVE ? "insufficient_unique_constellation" : "pair_scale_inconsistent",
        })),
      ],
    };
  }
  return {
    raw: sized,
    accepted: unique.map((c) => ({ ...c, accepted: true, reason: "unique_constellation" })),
    rejected: ambig,
  };
}

export function matchRoads(
  model: readonly ModelXzSignature[],
  osm: readonly OsmPolyline[],
  tol = FOOTPRINT_RELATIVE_TOLERANCE,
): { raw: GeometricMatchCandidate[]; accepted: GeometricMatchCandidate[]; rejected: GeometricMatchCandidate[] } {
  const sized: GeometricMatchCandidate[] = [];
  for (const m of model) {
    const mf = orderedFootprint(m.spanX, m.spanZ);
    for (const o of osm) {
      if (o.spanEastM <= 0 || o.spanNorthM <= 0) continue;
      const of = orderedFootprint(o.spanEastM, o.spanNorthM);
      const err = footprintRelativeError(mf, of);
      if (err > tol) continue;
      const mid = o.points[Math.floor(o.points.length / 2)] ?? o.points[0];
      sized.push({
        modelName: m.name,
        osmId: o.id,
        modelFootprint: mf,
        osmFootprint: of,
        relativeError: err,
        world: { ...m.world },
        geo: { ...mid },
        accepted: false,
        reason: "road_span_candidate",
        kind: "road",
      });
    }
  }
  const { unique, rejected: ambig } = uniqueBidirectionalMatches(sized);
  if (!constellationConsistent(unique)) {
    return {
      raw: sized,
      accepted: [],
      rejected: [
        ...ambig,
        ...unique.map((c) => ({
          ...c,
          accepted: false,
          reason: unique.length < MIN_UNIQUE_MATCHES_FOR_SOLVE ? "insufficient_unique_constellation" : "pair_scale_inconsistent",
        })),
      ],
    };
  }
  return {
    raw: sized,
    accepted: unique.map((c) => ({ ...c, accepted: true, reason: "unique_road_constellation" })),
    rejected: ambig,
  };
}

export function matchesToControlPoints(matches: readonly GeometricMatchCandidate[]): GeoControlPoint[] {
  return matches.map((m, i) => ({
    id: i < 3 ? (["A", "B", "C"] as const)[i] : `G${i}`,
    label: `${m.kind}:${m.modelName}->${m.osmId}`,
    world: m.world,
    geo: m.geo,
    coordinateSpace: "world",
  }));
}

export function spatialDistribution(points: readonly GeoControlPoint[]): SpatialDistribution {
  let minWorld: number | null = null;
  let minGps: number | null = null;
  const cells = new Set<string>();
  for (let i = 0; i < points.length; i++) {
    const cellX = Math.floor(points[i].world.x / 500);
    const cellZ = Math.floor(points[i].world.z / 500);
    cells.add(`${cellX}:${cellZ}`);
    for (let j = i + 1; j < points.length; j++) {
      const w = worldHorizontalDistance(points[i].world, points[j].world);
      const g = gpsHorizontalDistanceM(points[i].geo, points[j].geo);
      minWorld = minWorld == null ? w : Math.min(minWorld, w);
      minGps = minGps == null ? g : Math.min(minGps, g);
    }
  }
  const a = points[0]?.world;
  const b = points[1]?.world;
  const c = points[2]?.world;
  const collinear = !!(a && b && c && isCollinearWorld(a, b, c));
  const triangleArea = a && b && c ? worldTriangleArea(a, b, c) : null;
  const ok =
    points.length >= MIN_UNIQUE_MATCHES_FOR_SOLVE &&
    cells.size >= 2 &&
    !collinear &&
    (minWorld == null || minWorld >= MIN_MATCH_SEPARATION_M);
  return {
    matchedRegionCount: cells.size,
    minWorldSeparation: minWorld,
    minGpsSeparationM: minGps,
    collinear,
    triangleArea,
    ok,
  };
}

export type CoastlineMetric = {
  available: boolean;
  rmsM: number | null;
  sampleCount: number;
  precisionNote: string;
};

function nearestDistanceM(point: GeoCoordinate, polyline: readonly GeoCoordinate[]): number {
  const p = wgs84ToLocalMeters(point, ODESSA_ENU_ORIGIN);
  let best = Infinity;
  for (const q of polyline) {
    const e = wgs84ToLocalMeters(q, ODESSA_ENU_ORIGIN);
    best = Math.min(best, Math.hypot(p.east - e.east, p.north - e.north));
  }
  return best;
}

export function aabbBoundaryGeo(
  world: LocalWorldCoordinate,
  spanX: number,
  spanZ: number,
  calibration: GeoCalibration,
  samples = 8,
): GeoCoordinate[] {
  const pts: GeoCoordinate[] = [];
  const hx = spanX / 2;
  const hz = spanZ / 2;
  const corners: LocalWorldCoordinate[] = [];
  for (let i = 0; i < samples; i++) {
    const t = i / samples;
    corners.push({ x: world.x - hx + spanX * t, y: world.y, z: world.z - hz });
    corners.push({ x: world.x + hx, y: world.y, z: world.z - hz + spanZ * t });
    corners.push({ x: world.x + hx - spanX * t, y: world.y, z: world.z + hz });
    corners.push({ x: world.x - hx, y: world.y, z: world.z + hz - spanZ * t });
  }
  for (const w of corners) pts.push(worldToGeo(w, calibration));
  return pts;
}

/**
 * Horizontal RMS from OSM coastline samples to the nearest model water/coast
 * polyline (or AABB boundary if that is all the model has).
 */
export function coastlineMetric(
  modelWater: readonly ModelXzSignature[],
  osmCoast: readonly OsmPolyline[],
  _calibration: GeoCalibration | null,
): CoastlineMetric {
  const osmPts = osmCoast.flatMap((p) => p.points);
  if (!osmPts.length) {
    return { available: false, rmsM: null, sampleCount: 0, precisionNote: "NO_OSM_COASTLINE" };
  }
  if (!modelWater.length) {
    return { available: false, rmsM: null, sampleCount: 0, precisionNote: "NO_MODEL_WATER_OR_COAST" };
  }
  return {
    available: false,
    rmsM: null,
    sampleCount: osmPts.length,
    precisionNote: "MODEL_COAST_IS_AABB_NOT_A_POLYLINE — OSM coastline exists; model water/sand is city-scale boxes",
  };
}

/** Test helper: RMS between two ENU polylines already expressed as GeoCoordinates. */
export function polylineNearestRmsM(source: readonly GeoCoordinate[], target: readonly GeoCoordinate[]): number | null {
  if (!source.length || !target.length) return null;
  const sq = source.map((p) => {
    const d = nearestDistanceM(p, target);
    return d * d;
  });
  return Math.sqrt(sq.reduce((s, n) => s + n, 0) / sq.length);
}
