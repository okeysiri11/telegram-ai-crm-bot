/**
 * WGS84 → ENU meters → calibrated Three.js world.
 * Inverse is defined only when calibration status is READY_*.
 */

import type {
  AxisMapping,
  GeoCalibration,
  GeoCoordinate,
  HorizontalAxis,
  LocalMeters,
  LocalWorldCoordinate,
  VerticalAxis,
} from "./types";
import { localMetersToWgs84, wgs84ToLocalMeters } from "./localMeters";

export const IDENTITY_AXIS_MAPPING: AxisMapping = {
  east: "x",
  north: "z",
  up: "y",
};

/**
 * Mapping implied by the uncalibrated GeoTransform (east=+X, north=−Z, Y-up).
 * Recorded for diagnostics only — not applied until calibration is READY.
 */
export const UNCALIBRATED_GEOTRANSFORM_AXES: AxisMapping = {
  east: "x",
  north: "-z",
  up: "y",
};

function axisSign(axis: HorizontalAxis | VerticalAxis): number {
  return axis.startsWith("-") ? -1 : 1;
}

function horizontalComponent(axis: HorizontalAxis, world: LocalWorldCoordinate): number {
  const v = axis.endsWith("x") ? world.x : world.z;
  return axisSign(axis) * v;
}

function writeHorizontal(axis: HorizontalAxis, value: number, world: LocalWorldCoordinate) {
  const signed = axisSign(axis) * value;
  if (axis.endsWith("x")) world.x = signed;
  else world.z = signed;
}

/** Map a world XZ delta into the calibration's east/north plane. */
export function mappedHorizontalAxes(
  rel: LocalWorldCoordinate,
  mapping: AxisMapping,
): { east: number; north: number } {
  return {
    east: horizontalComponent(mapping.east, rel),
    north: horizontalComponent(mapping.north, rel),
  };
}

export function localMetersToWorld(
  enu: LocalMeters,
  calibration: GeoCalibration,
  out: LocalWorldCoordinate = { x: 0, y: 0, z: 0 },
): LocalWorldCoordinate {
  const s = 1 / calibration.metersPerWorldUnit;
  const c = Math.cos(calibration.rotationRadians);
  const sn = Math.sin(calibration.rotationRadians);
  const eastR = enu.east * c - enu.north * sn;
  const northR = enu.east * sn + enu.north * c;
  const rel: LocalWorldCoordinate = { x: 0, y: 0, z: 0 };
  writeHorizontal(calibration.axisMapping.east, eastR * s, rel);
  writeHorizontal(calibration.axisMapping.north, northR * s, rel);
  rel.y = axisSign(calibration.axisMapping.up) * enu.up * s;
  out.x = rel.x + calibration.worldOrigin.x;
  out.y = rel.y + calibration.worldOrigin.y;
  out.z = rel.z + calibration.worldOrigin.z;
  return out;
}

export function worldToLocalMeters(
  world: LocalWorldCoordinate,
  calibration: GeoCalibration,
  out: LocalMeters = { east: 0, north: 0, up: 0 },
): LocalMeters {
  const dx = world.x - calibration.worldOrigin.x;
  const dy = world.y - calibration.worldOrigin.y;
  const dz = world.z - calibration.worldOrigin.z;
  const rel: LocalWorldCoordinate = { x: dx, y: dy, z: dz };
  const eastW = horizontalComponent(calibration.axisMapping.east, rel) * calibration.metersPerWorldUnit;
  const northW = horizontalComponent(calibration.axisMapping.north, rel) * calibration.metersPerWorldUnit;
  const upW = axisSign(calibration.axisMapping.up) * rel.y * calibration.metersPerWorldUnit;
  const c = Math.cos(-calibration.rotationRadians);
  const sn = Math.sin(-calibration.rotationRadians);
  out.east = eastW * c - northW * sn;
  out.north = eastW * sn + northW * c;
  out.up = upW;
  return out;
}

export function geoToWorld(
  coord: GeoCoordinate,
  calibration: GeoCalibration,
  out?: LocalWorldCoordinate,
): LocalWorldCoordinate {
  const enu = wgs84ToLocalMeters(coord, calibration.origin);
  return localMetersToWorld(enu, calibration, out);
}

export function worldToGeo(
  world: LocalWorldCoordinate,
  calibration: GeoCalibration,
  out?: GeoCoordinate,
): GeoCoordinate {
  const enu = worldToLocalMeters(world, calibration);
  return localMetersToWgs84(enu, calibration.origin, out);
}

export function describeAxisMapping(mapping: AxisMapping): string {
  return `E→${mapping.east} N→${mapping.north} U→${mapping.up}`;
}
