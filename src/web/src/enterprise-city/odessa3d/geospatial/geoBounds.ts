/**
 * Geographic bounds of the loaded model — only when calibration is READY.
 */

import type { BoundsClass, GeoBounds, GeoCalibration, GeoCoordinate, WorldBox } from "./types";
import { worldToGeo } from "./worldTransform";

export function worldBoxToGeoBounds(box: WorldBox, calibration: GeoCalibration): GeoBounds {
  const corners: GeoCoordinate[] = [];
  const xs = [box.min.x, box.max.x];
  const ys = [box.min.y, box.max.y];
  const zs = [box.min.z, box.max.z];
  for (const x of xs) {
    for (const y of ys) {
      for (const z of zs) {
        corners.push(worldToGeo({ x, y, z }, calibration));
      }
    }
  }
  let north = -Infinity;
  let south = Infinity;
  let east = -Infinity;
  let west = Infinity;
  for (const c of corners) {
    if (c.lat > north) north = c.lat;
    if (c.lat < south) south = c.lat;
    if (c.lon > east) east = c.lon;
    if (c.lon < west) west = c.lon;
  }
  return { north, south, east, west };
}

export function classifyGeoAgainstBounds(coord: GeoCoordinate, bounds: GeoBounds): BoundsClass {
  const latSpan = Math.max(bounds.north - bounds.south, 1e-9);
  const lonSpan = Math.max(bounds.east - bounds.west, 1e-9);
  const latPad = latSpan * 0.1;
  const lonPad = lonSpan * 0.1;
  const inCore =
    coord.lat >= bounds.south &&
    coord.lat <= bounds.north &&
    coord.lon >= bounds.west &&
    coord.lon <= bounds.east;
  if (inCore) return "IN_BOUNDS";
  const inPad =
    coord.lat >= bounds.south - latPad &&
    coord.lat <= bounds.north + latPad &&
    coord.lon >= bounds.west - lonPad &&
    coord.lon <= bounds.east + lonPad;
  return inPad ? "NEAR_BOUNDS" : "OUT_OF_BOUNDS";
}
