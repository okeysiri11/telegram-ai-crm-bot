/**
 * Enterprise City Graphics Engine — Camera Engine.
 * Sprint CG-2. Extends the real `cityEngine.ts` camera primitives (clampViewport, panToBuilding,
 * zoomBy, applyPanDelta, viewportRect) with smooth-animation, focus-district, and reset-animation
 * behavior. Deliberately does NOT reimplement viewport math, clamping, or persistence — every one of
 * those stays owned by `cityEngine.ts` and is imported directly. This file adds only what
 * `cityEngine.ts` intentionally does not do (it is a "presentation camera controller," per its own
 * header comment, not an animation engine) — smoothing a transition between two viewports over time.
 *
 * Reusable by every City screen: nothing here depends on `EnterpriseCityPage.tsx` or any other
 * specific consumer.
 */

import {
  clampViewport,
  DEFAULT_VIEWPORT,
  panToBuilding,
  type CityViewport,
} from "../cityEngine";
import type { CityBuilding } from "../cityCatalog";
import type { CityDistrictMeta } from "../cityDistricts";
import type { AnimationHandle } from "./types";
import { animateValue } from "./animationController";

export type CameraAnimationOptions = {
  durationMs?: number;
  reducedMotion?: boolean;
  onFrame: (viewport: CityViewport) => void;
  onComplete?: (viewport: CityViewport) => void;
};

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpViewport(from: CityViewport, to: CityViewport, t: number): CityViewport {
  return clampViewport({
    x: lerp(from.x, to.x, t),
    y: lerp(from.y, to.y, t),
    zoom: lerp(from.zoom, to.zoom, t),
  });
}

/**
 * Animate the camera from one viewport to another. Reduced-motion collapses this to a single,
 * instant frame — the same contract every other animated surface in the platform honors
 * (`ENTERPRISE_DESIGN_SYSTEM.md` §5.5), applied here rather than reinvented.
 */
export function animateViewport(
  from: CityViewport,
  to: CityViewport,
  options: CameraAnimationOptions,
): AnimationHandle {
  const target = clampViewport(to);
  if (options.reducedMotion) {
    options.onFrame(target);
    options.onComplete?.(target);
    return { id: "camera:instant", cancel: () => {} };
  }
  return animateValue({
    durationMs: options.durationMs ?? 320,
    onFrame: (t) => options.onFrame(lerpViewport(from, target, t)),
    onComplete: () => options.onComplete?.(target),
  });
}

/** Focus a single building — thin wrapper over the real `panToBuilding`, animated. */
export function focusBuilding(
  current: CityViewport,
  building: CityBuilding,
  options: Omit<CameraAnimationOptions, "onFrame"> & { onFrame: CameraAnimationOptions["onFrame"] },
): AnimationHandle {
  const target = panToBuilding(building, current);
  return animateViewport(current, target, options);
}

/**
 * Focus an entire district — centers on the district's centroid (`CityDistrictMeta.x/y`) at a wider
 * zoom than a single-building focus, so the whole district reads as one framed group.
 */
export function focusDistrict(
  current: CityViewport,
  district: CityDistrictMeta,
  options: Omit<CameraAnimationOptions, "onFrame"> & { onFrame: CameraAnimationOptions["onFrame"] },
): AnimationHandle {
  const target = clampViewport({
    x: 50 - district.x,
    y: 50 - district.y,
    zoom: 0.85,
  });
  return animateViewport(current, target, options);
}

/** Animate back to the default viewport — the camera's one "home" position. */
export function resetCamera(
  current: CityViewport,
  options: Omit<CameraAnimationOptions, "onFrame"> & { onFrame: CameraAnimationOptions["onFrame"] },
): AnimationHandle {
  return animateViewport(current, DEFAULT_VIEWPORT, options);
}

/**
 * Camera bounds — restated here (not redefined) from `cityEngine.ts`'s real clamp behavior, exposed
 * as data so a UI (e.g. a zoom slider) can read the real bounds without reaching into `cityEngine.ts`
 * internals.
 */
export function cameraBounds(): { zoomMin: number; zoomMax: number; panLimit: number } {
  // Derived by probing the real clamp function rather than re-declaring the constants a second time.
  const probedMax = clampViewport({ x: 0, y: 0, zoom: 999 }).zoom;
  const probedMin = clampViewport({ x: 0, y: 0, zoom: -999 }).zoom;
  const probedPan = clampViewport({ x: 999, y: 0, zoom: 1 }).x;
  return { zoomMin: probedMin, zoomMax: probedMax, panLimit: probedPan };
}
