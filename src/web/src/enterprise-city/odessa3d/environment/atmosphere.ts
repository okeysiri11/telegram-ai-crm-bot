/**
 * Lightweight distance fog / coastal haze. No volumetrics.
 */

import * as THREE from "three";
import type { EnvironmentQuality } from "./environmentPresets";

/** FogExp2 density so ~50% mix occurs near `distanceM`. */
export function fogDensityAtDistance(distanceM: number): number {
  const dist = Math.max(280, distanceM);
  return 0.8325546 / dist;
}

export function fogDensityForCity(
  cityDiagonal: number,
  quality: EnvironmentQuality,
  haze = 1,
): number {
  const factor = quality === "low" ? 0.72 : quality === "high" ? 0.92 : 0.84;
  const target = Math.max(420, cityDiagonal * factor);
  const density = fogDensityAtDistance(target) * haze;
  /* STEP 29.9: the floor must scale with the city — a fixed 0.00022 floor
   * (tuned for the ~1.4 km legacy world) would fully fog the 84 km metric
   * city. Never denser than 50% mix at 2.5× the diagonal. */
  const floor = Math.min(0.00022, fogDensityAtDistance(cityDiagonal * 2.5));
  return THREE.MathUtils.clamp(density, floor, 0.00135);
}

export function createCityFog(color: number, density: number): THREE.FogExp2 {
  return new THREE.FogExp2(color, density);
}

export function applyFog(scene: THREE.Scene, fog: THREE.FogExp2 | null) {
  scene.fog = fog;
}
