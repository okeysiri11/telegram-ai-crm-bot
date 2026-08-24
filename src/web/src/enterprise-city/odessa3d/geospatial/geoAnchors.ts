/**
 * GeoAnchor data objects. Not Three.js meshes.
 * Never invent WGS84 from the 2D city-plane mapping.
 */

import type { CityEntity } from "../types";
import type { GeoLocation } from "@/runtime/spatialRuntime/spatialTypes";
import type { GeoAnchor, GeoCoordinate, LocalWorldCoordinate } from "./types";
import type { GeoCalibration } from "./types";
import { geoToWorld } from "./worldTransform";
import { isFiniteGeo, ODESSA_GEO_ORIGIN } from "./localMeters";

/**
 * Pure WGS84: lat/lon present and NOT derived from Enterprise City 0–100 plane.
 * `planeToGeo` always stamps x/y — those must not become 3D anchors.
 */
export function isPureWgs84(geo: GeoLocation | undefined | null): geo is GeoLocation {
  if (!geo) return false;
  if (!Number.isFinite(geo.lat) || !Number.isFinite(geo.lng)) return false;
  if (geo.x != null || geo.y != null) return false;
  return true;
}

export function geoLocationToCoordinate(geo: GeoLocation): GeoCoordinate {
  const coord: GeoCoordinate = { lat: geo.lat, lon: geo.lng };
  if (geo.altitudeM != null) coord.altitude = geo.altitudeM;
  return coord;
}

export function cityEntityToGeoAnchor(entity: CityEntity): GeoAnchor | null {
  if (!isPureWgs84(entity.geo)) return null;
  return {
    id: `anchor_${entity.id}`,
    coordinate: geoLocationToCoordinate(entity.geo),
    entityId: entity.id,
    type: entity.kind === "building" ? "enterprise" : entity.kind === "marker" ? "poi" : "custom",
    label: entity.label,
  };
}

export function collectEnterpriseAnchors(entities: Iterable<CityEntity>): GeoAnchor[] {
  const out: GeoAnchor[] = [];
  for (const e of entities) {
    const a = cityEntityToGeoAnchor(e);
    if (a) out.push(a);
  }
  return out;
}

export type CachedAnchor = {
  anchor: GeoAnchor;
  world: LocalWorldCoordinate | null;
};

/**
 * DEV foundation only. The ENU origin is a math reference, not a landmark
 * and not a claimed model lock. Do not invent street addresses.
 */
export const DEV_GEO_ANCHORS: GeoAnchor[] = [
  {
    id: "dev_enu_origin",
    name: "Odessa ENU reference origin",
    label: "Odessa ENU reference origin",
    type: "poi",
    coordinate: {
      lat: ODESSA_GEO_ORIGIN.referenceLat,
      lon: ODESSA_GEO_ORIGIN.referenceLon,
      altitude: ODESSA_GEO_ORIGIN.referenceAltitude,
    },
    metadata: { role: "enu_origin_only", notALandmark: true },
  },
];

export function cacheAnchorWorlds(anchors: readonly GeoAnchor[], calibration: GeoCalibration | null): CachedAnchor[] {
  return anchors.map((anchor) => ({
    anchor,
    world: calibration && isFiniteGeo(anchor.coordinate) ? geoToWorld(anchor.coordinate, calibration) : null,
  }));
}
