/**
 * Smooth camera reframe toward a picked object's world AABB.
 * Stays outside the geometry; preserves existing clip-range helpers.
 */

import * as THREE from "three";
import { FOCUS_TWEEN_MS } from "../cameraNavigation";
import type { GlobalCityBounds } from "../cityAssembly";

export type FocusPose = {
  position: THREE.Vector3;
  target: THREE.Vector3;
};

export function focusPoseForObject(
  object: THREE.Object3D,
  camera: THREE.PerspectiveCamera,
  cityBounds?: GlobalCityBounds | null,
): FocusPose {
  const box = new THREE.Box3().setFromObject(object);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const radius = Math.max(size.length() * 0.5, 2);
  const diagonal = cityBounds?.diagonal ?? Math.max(radius * 40, 1200);
  const dist = Math.max(radius * 2.6, diagonal * 0.01, 10);

  const back = new THREE.Vector3();
  camera.getWorldDirection(back);
  if (back.lengthSq() < 1e-6) back.set(0.45, -0.55, 0.7);
  back.normalize().multiplyScalar(-1);
  const position = center.clone().add(back.multiplyScalar(dist));
  position.y = Math.max(position.y, box.max.y + Math.max(radius * 0.35, 3));

  return { position, target: center };
}

export type CameraFocusTween = {
  t0: number;
  durationMs: number;
  fromPos: THREE.Vector3;
  toPos: THREE.Vector3;
  fromTarget: THREE.Vector3;
  toTarget: THREE.Vector3;
};

export function createFocusTween(
  now: number,
  fromPos: THREE.Vector3,
  toPos: THREE.Vector3,
  fromTarget: THREE.Vector3,
  toTarget: THREE.Vector3,
  durationMs = FOCUS_TWEEN_MS,
): CameraFocusTween {
  return {
    t0: now,
    durationMs,
    fromPos: fromPos.clone(),
    toPos: toPos.clone(),
    fromTarget: fromTarget.clone(),
    toTarget: toTarget.clone(),
  };
}

export function easeOutCubic(t: number): number {
  return 1 - (1 - t) ** 3;
}

export function applyFocusTween(
  tween: CameraFocusTween,
  now: number,
  camera: THREE.PerspectiveCamera,
  target: THREE.Vector3,
): boolean {
  const u = Math.min(1, Math.max(0, (now - tween.t0) / tween.durationMs));
  const e = easeOutCubic(u);
  camera.position.lerpVectors(tween.fromPos, tween.toPos, e);
  target.lerpVectors(tween.fromTarget, tween.toTarget, e);
  camera.updateProjectionMatrix();
  return u >= 1;
}
