/**
 * In-scene 2D / 3D camera poses. Never remounts the city or changes coordinates.
 */

import * as THREE from "three";
import type { GlobalCityBounds } from "./cityAssembly";
import { fitCameraToOdessaBounds } from "./cityAssembly";
import {
  CAMERA_POLAR_2D_MAX,
  CAMERA_POLAR_2D_MIN,
  CAMERA_POLAR_3D_MAX,
  CAMERA_POLAR_3D_MIN,
} from "./cameraNavigation";

export type CityCameraViewMode = "3d" | "2d";

export type CameraPose = {
  position: THREE.Vector3;
  target: THREE.Vector3;
};

export type PolarLimits = {
  minPolarAngle: number;
  maxPolarAngle: number;
};

export function polarLimitsForViewMode(mode: CityCameraViewMode): PolarLimits {
  if (mode === "2d") {
    return { minPolarAngle: CAMERA_POLAR_2D_MIN, maxPolarAngle: CAMERA_POLAR_2D_MAX };
  }
  return { minPolarAngle: CAMERA_POLAR_3D_MIN, maxPolarAngle: CAMERA_POLAR_3D_MAX };
}

/** Near-nadir overview — buildings stay visible, perspective is minimal. */
export function topDownPose(bounds: GlobalCityBounds): CameraPose {
  const height = Math.max(bounds.diagonal * 0.72, 280);
  return {
    position: new THREE.Vector3(bounds.center.x, bounds.center.y + height, bounds.center.z + 1),
    target: bounds.center.clone(),
  };
}

export function perspectiveOverviewPose(
  bounds: GlobalCityBounds,
  camera: THREE.PerspectiveCamera,
  aspect: number,
): CameraPose {
  const fit = fitCameraToOdessaBounds(bounds, camera, aspect);
  return { position: fit.position.clone(), target: fit.target.clone() };
}
