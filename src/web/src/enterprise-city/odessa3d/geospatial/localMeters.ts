/**
 * Local tangent (ENU-like) meters around a WGS84 origin.
 * City-scale only — not a full map projection. No GIS dependency.
 */

import type { GeoCoordinate, GeoOrigin, LocalMeters } from "./types";
import { ODESSA_CITY } from "@/runtime/spatialRuntime/spatialTypes";

const DEG = Math.PI / 180;
const WGS84_A = 6378137;
const WGS84_E2 = 0.00669437999014;

/**
 * Published approximate Odessa city center (spatialTypes.ODESSA_CITY).
 * Used only as the ENU tangent origin for metric math — not a model calibration.
 */
/** Approximate published Odessa center. ENU math origin only — not a model lock. */
export const ODESSA_GEO_ORIGIN: GeoOrigin = {
  referenceLat: ODESSA_CITY.lat,
  referenceLon: ODESSA_CITY.lng,
  referenceAltitude: 0,
};

export const ODESSA_ENU_ORIGIN: GeoCoordinate = {
  lat: ODESSA_GEO_ORIGIN.referenceLat,
  lon: ODESSA_GEO_ORIGIN.referenceLon,
  altitude: ODESSA_GEO_ORIGIN.referenceAltitude,
};

export function metersPerDegreeLatitude(latDeg: number): number {
  const lat = latDeg * DEG;
  return 111132.92 - 559.82 * Math.cos(2 * lat) + 1.175 * Math.cos(4 * lat);
}

export function metersPerDegreeLongitude(latDeg: number): number {
  const lat = latDeg * DEG;
  const sin = Math.sin(lat);
  const n = WGS84_A / Math.sqrt(1 - WGS84_E2 * sin * sin);
  return n * Math.cos(lat) * DEG;
}

export function wgs84ToLocalMeters(
  coord: GeoCoordinate,
  origin: GeoCoordinate = ODESSA_ENU_ORIGIN,
  out: LocalMeters = { east: 0, north: 0, up: 0 },
): LocalMeters {
  const mLat = metersPerDegreeLatitude(origin.lat);
  const mLon = metersPerDegreeLongitude(origin.lat);
  out.east = (coord.lon - origin.lon) * mLon;
  out.north = (coord.lat - origin.lat) * mLat;
  out.up = (coord.altitude ?? 0) - (origin.altitude ?? 0);
  return out;
}

export function localMetersToWgs84(
  meters: LocalMeters,
  origin: GeoCoordinate = ODESSA_ENU_ORIGIN,
  out: GeoCoordinate = { lat: 0, lon: 0 },
): GeoCoordinate {
  const mLat = metersPerDegreeLatitude(origin.lat);
  const mLon = metersPerDegreeLongitude(origin.lat);
  out.lat = origin.lat + meters.north / mLat;
  out.lon = origin.lon + meters.east / mLon;
  const alt = (origin.altitude ?? 0) + meters.up;
  if (alt !== 0) out.altitude = alt;
  else delete out.altitude;
  return out;
}

export function enuDistanceMeters(a: LocalMeters, b: LocalMeters): number {
  return Math.hypot(a.east - b.east, a.north - b.north, a.up - b.up);
}

export function horizontalDistanceMeters(a: LocalMeters, b: LocalMeters): number {
  return Math.hypot(a.east - b.east, a.north - b.north);
}

export function isFiniteGeo(coord: GeoCoordinate | null | undefined): coord is GeoCoordinate {
  if (!coord) return false;
  return Number.isFinite(coord.lat) && Number.isFinite(coord.lon) && Math.abs(coord.lat) <= 90 && Math.abs(coord.lon) <= 180;
}

export function formatLatLon(coord: GeoCoordinate, digits = 6): string {
  return `${coord.lat.toFixed(digits)}, ${coord.lon.toFixed(digits)}`;
}
