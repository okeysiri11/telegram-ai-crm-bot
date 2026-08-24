/**
 * Event-driven / throttled raycasts. Never call from every render frame.
 */

import * as THREE from "three";

export const HOVER_RAYCAST_INTERVAL_MS = 55;
/** ~18 checks/sec */
export const HOVER_RAYCAST_MAX_PER_SEC = Math.round(1000 / HOVER_RAYCAST_INTERVAL_MS);

export const BROADPHASE_MESH_THRESHOLD = 600;

export function pointerToNdc(
  clientX: number,
  clientY: number,
  canvas: HTMLElement,
  out: THREE.Vector2,
): boolean {
  const rect = canvas.getBoundingClientRect();
  if (rect.width < 1 || rect.height < 1) return false;
  out.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  out.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  return true;
}

export function rayIntersectsBox(ray: THREE.Ray, box: THREE.Box3): boolean {
  return ray.intersectsBox(box);
}

export type RaycastMeter = {
  windowStartMs: number;
  countInWindow: number;
  perSec: number;
  lastMs: number;
  lastHits: number;
  lastCandidates: number;
};

export function createRaycastMeter(): RaycastMeter {
  return {
    windowStartMs: 0,
    countInWindow: 0,
    perSec: 0,
    lastMs: 0,
    lastHits: 0,
    lastCandidates: 0,
  };
}

export function recordRaycast(meter: RaycastMeter, now: number, durationMs: number, hits: number, candidates: number) {
  meter.lastMs = durationMs;
  meter.lastHits = hits;
  meter.lastCandidates = candidates;
  if (meter.windowStartMs === 0 || now - meter.windowStartMs >= 1000) {
    meter.perSec = meter.windowStartMs === 0 ? 1 : meter.countInWindow;
    meter.windowStartMs = now;
    meter.countInWindow = 1;
  } else {
    meter.countInWindow += 1;
  }
}
