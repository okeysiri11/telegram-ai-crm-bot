/**
 * GeoTransform — legacy streaming fallback (tile center when centerScene is missing).
 * Authoritative WGS84 ↔ world conversion lives in `odessa3d/geospatial/`.
 * This class must not be treated as a calibrated georeference (`calibrated: false` in the manifest).
 */

import type { GeoLocation } from "@/runtime/spatialRuntime/spatialTypes";
import type { GeoTransformCalibration } from "./types";

const DEFAULT_LAT_SCALE = 111_000;
const DEFAULT_LNG_SCALE = 75_000;

export class GeoTransform {
  readonly calibration: GeoTransformCalibration;

  constructor(calibration: GeoTransformCalibration) {
    this.calibration = calibration;
  }

  geoToScene(lat: number, lng: number, alt = 0): { x: number; y: number; z: number } {
    const latScale = this.calibration.scaleMetersPerDegreeLat ?? DEFAULT_LAT_SCALE;
    const lngScale = this.calibration.scaleMetersPerDegreeLng ?? DEFAULT_LNG_SCALE;
    const rot = this.calibration.rotationY ?? 0;
    const dx = (lng - this.calibration.originLng) * lngScale;
    const dz = -(lat - this.calibration.originLat) * latScale;
    const y = alt + (this.calibration.elevationOffset ?? 0);
    if (!rot) return { x: dx, y, z: dz };
    const c = Math.cos(rot);
    const s = Math.sin(rot);
    return { x: dx * c - dz * s, y, z: dx * s + dz * c };
  }

  sceneToGeo(x: number, y: number, z: number): GeoLocation {
    const latScale = this.calibration.scaleMetersPerDegreeLat ?? DEFAULT_LAT_SCALE;
    const lngScale = this.calibration.scaleMetersPerDegreeLng ?? DEFAULT_LNG_SCALE;
    const rot = this.calibration.rotationY ?? 0;
    let dx = x;
    let dz = z;
    if (rot) {
      const c = Math.cos(-rot);
      const s = Math.sin(-rot);
      dx = x * c - z * s;
      dz = x * s + z * c;
    }
    const lat = this.calibration.originLat - dz / latScale;
    const lng = this.calibration.originLng + dx / lngScale;
    return { lat, lng, x, y };
  }

  distanceMeters(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
    const p1 = this.geoToScene(a.lat, a.lng);
    const p2 = this.geoToScene(b.lat, b.lng);
    const dx = p1.x - p2.x;
    const dz = p1.z - p2.z;
    return Math.hypot(dx, dz);
  }
}

export function defaultOdessaGeoTransform(): GeoTransform {
  return new GeoTransform({
    originLat: 46.4825,
    originLng: 30.7233,
    calibrated: false,
  });
}
