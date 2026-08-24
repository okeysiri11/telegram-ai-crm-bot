/**
 * Manual WGS84 entry for calibration. No map provider.
 */

import type { GeoCoordinate } from "./types";
import { horizontalDistanceMeters, isFiniteGeo, wgs84ToLocalMeters, ODESSA_ENU_ORIGIN } from "./localMeters";

export const ODESSA_GPS_MAX_M = 80_000;

export type GpsValidationResult = {
  ok: boolean;
  geo?: GeoCoordinate;
  error?: string;
  warning?: string;
};

export function parseGpsNumber(raw: string): number | null {
  const t = raw.trim().replace(",", ".");
  if (!t) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

export function validateGpsInput(latText: string, lonText: string): GpsValidationResult {
  const lat = parseGpsNumber(latText);
  const lon = parseGpsNumber(lonText);
  if (lat == null || lon == null) {
    return { ok: false, error: "invalid_gps_number" };
  }
  if (Math.abs(lat) > 90) return { ok: false, error: "latitude_out_of_range" };
  if (Math.abs(lon) > 180) return { ok: false, error: "longitude_out_of_range" };
  const geo: GeoCoordinate = { lat, lon };
  if (!isFiniteGeo(geo)) return { ok: false, error: "invalid_gps" };
  const dist = horizontalDistanceMeters(wgs84ToLocalMeters(geo), wgs84ToLocalMeters(ODESSA_ENU_ORIGIN));
  if (dist > ODESSA_GPS_MAX_M) {
    return { ok: false, error: `outside_odessa_range:${Math.round(dist)}m` };
  }
  return { ok: true, geo };
}

/**
 * Split a pasted pair. Placeholder text is never treated as a value.
 * Accepts "46.482526, 30.723309" or "46.482526 30.723309".
 */
export function parseLatLonPair(raw: string): { latText: string; lonText: string } | null {
  const t = raw.trim();
  if (!t) return null;
  const m = t.match(/(-?\d+(?:[.,]\d+)?)\s*[,;\s]\s*(-?\d+(?:[.,]\d+)?)/);
  if (!m) return null;
  return { latText: m[1].replace(",", "."), lonText: m[2].replace(",", ".") };
}

export function applyPasteToGpsFields(
  latText: string,
  lonText: string,
): { latText: string; lonText: string } {
  const fromLat = parseLatLonPair(latText);
  if (fromLat) return fromLat;
  const fromLon = parseLatLonPair(lonText);
  if (fromLon) return fromLon;
  return { latText, lonText };
}

/** External Odessa search — does not assign coordinates. */
export function odessaMapHelperUrl(): string {
  return `https://www.openstreetmap.org/#map=14/${ODESSA_ENU_ORIGIN.lat}/${ODESSA_ENU_ORIGIN.lon}`;
}
