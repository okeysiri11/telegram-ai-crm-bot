/**
 * Visual sun direction from elevation / azimuth.
 * Matches Three.js Sky spherical convention. Not an ephemeris.
 */

import * as THREE from "three";

export function sunDirectionFromElevationAzimuth(elevationDeg: number, azimuthDeg: number, out = new THREE.Vector3()): THREE.Vector3 {
  const phi = THREE.MathUtils.degToRad(90 - elevationDeg);
  const theta = THREE.MathUtils.degToRad(azimuthDeg);
  return out.setFromSphericalCoords(1, phi, theta);
}

export function sunPositionOnRadius(
  direction: THREE.Vector3,
  radius: number,
  out = new THREE.Vector3(),
): THREE.Vector3 {
  return out.copy(direction).multiplyScalar(Math.max(80, radius));
}
