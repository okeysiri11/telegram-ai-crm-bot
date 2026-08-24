/**
 * Odessa 3D camera clip range + distance-aware pan.
 * Runtime-only: does not move city geometry or change geoTransform.
 */

export const CAMERA_NEAR_MIN = 1.0;
export const CAMERA_NEAR_MAX = 4.0;

/** Map-style OrbitControls mouse mapping (left=pan, right=orbit, wheel=zoom). */
export const CAMERA_MOUSE_LEFT = 2 as const; /* THREE.MOUSE.PAN */
export const CAMERA_MOUSE_MIDDLE = 1 as const; /* THREE.MOUSE.DOLLY */
export const CAMERA_MOUSE_RIGHT = 0 as const; /* THREE.MOUSE.ROTATE */

/** 3D: keep the camera above the horizon; never flip under the city. */
export const CAMERA_POLAR_3D_MIN = 0.22; /* ~12.6° from nadir */
export const CAMERA_POLAR_3D_MAX = Math.PI / 2.08; /* ~86.5° — not underground */

/** 2D: almost top-down, slight tilt allowed so buildings still read as volumes. */
export const CAMERA_POLAR_2D_MIN = 0.02;
export const CAMERA_POLAR_2D_MAX = 0.28;

/** Street-level approach without entering typical building interiors. */
export const CAMERA_MIN_DISTANCE_M = 12;
export const CAMERA_MIN_HEIGHT_ABOVE_BASE_M = 4;

export const HOME_TWEEN_MS = 1100;
export const FOCUS_TWEEN_MS = 900;

/**
 * STEP 29.9: the metric package makes the city ~84 km across. A fixed 4 m
 * near cap (tuned for the ~1.4 km legacy world) would collapse 24-bit depth
 * precision at overview distances, while a diagonal-derived near would clip
 * street-level views. The cap therefore scales with the diagonal: legacy
 * (≤1.6 km) keeps the exact 4 m envelope, the metric city gets a
 * proportional one (~210 m at full overview), and the distance-adaptive
 * clip below still tightens near when zooming in.
 */
export function cameraNearMaxFor(diagonal: number): number {
  return Math.max(CAMERA_NEAR_MAX, diagonal * 0.0025);
}
export const BASE_PAN_SPEED = 0.85;
export const PAN_COMPENSATION_MIN = 1;
export const PAN_COMPENSATION_MAX = 4;
/** Keep screen-space panning — city-map drag stays parallel to the view, not world-up. */
export const CITY_SCREEN_SPACE_PANNING = true;
/**
 * Zoom toward the pointer so the orbit target follows the inspected district.
 * Native OrbitControls.zoomToCursor; configurable, default on.
 */
export const CITY_ZOOM_TOWARD_POINTER = true;
/** Logarithmic depth is OFF — clip range + water guard are sufficient. */
export const LOGARITHMIC_DEPTH_BUFFER = false;
/** Smooth but responsive — slightly snappier than 0.06, still damped. */
export const CAMERA_DAMPING_FACTOR = 0.085;
export const CAMERA_ROTATE_SPEED = 0.58;
export const CAMERA_ZOOM_SPEED = 0.82;

export type ClipBoundsInput = {
  size: { x: number; y: number; z: number };
  diagonal: number;
};

export type CameraClipRange = {
  near: number;
  far: number;
};

export function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/**
 * Tightest safe PerspectiveCamera near/far from current city bounds.
 * Avoids tiny near (0.001) that destroys depth precision on a km-scale city.
 */
export function computeCameraClipRange(bounds: ClipBoundsInput, farCap?: number): CameraClipRange {
  const maxDim = Math.max(bounds.size.x, bounds.size.y, bounds.size.z, 1);
  const diagonal = Math.max(bounds.diagonal, 1);
  const near = clampNumber(
    Math.max(diagonal * 0.002, maxDim / 800, 1),
    CAMERA_NEAR_MIN,
    cameraNearMaxFor(diagonal),
  );

  /** Cover overview + modest zoom-out. Do not use 4× diagonal as the far plane (destroys depth precision). */
  let far = Math.max(diagonal * 2.6, maxDim * 2.8, 2200);
  if (farCap && farCap > near * 20) {
    far = Math.min(far, farCap);
  }
  if (far < near * 20) far = near * 20;
  return { near, far };
}

/** Hysteresis clip from camera distance — tighter near when zoomed in, without per-frame oscillation. */
export function computeAdaptiveCameraClip(
  bounds: ClipBoundsInput,
  cameraDistance: number,
  farCap?: number,
): CameraClipRange {
  const base = computeCameraClipRange(bounds, farCap);
  const dist = Math.max(cameraDistance, 1);
  /* Distance-driven near: zooming in must be able to REDUCE near below the
   * diagonal-derived base (street level in an 84 km metric city), zooming
   * out raises it toward the scale-aware cap for depth precision. */
  const nearMax = cameraNearMaxFor(Math.max(bounds.diagonal, 1));
  const near = clampNumber(Math.max(dist * 0.004, CAMERA_NEAR_MIN), CAMERA_NEAR_MIN, nearMax);
  const far = Math.max(base.far, dist + Math.max(bounds.diagonal, 1) * 0.85);
  return { near, far };
}

/**
 * Distance compensation so OrbitControls pan does not collapse near the target.
 * OrbitControls already scales pan with camera-target distance; this multiplier
 * restores useful city-block travel when zoomed in.
 *
 * far ≈ 1.0x · medium ≈ 1.2–1.5x · near ≈ 2–4x · very near capped.
 */
export function distancePanCompensation(distance: number, cityDiagonal: number): number {
  const farRef = Math.max(cityDiagonal * 0.85, 200);
  const nearRef = Math.max(cityDiagonal * 0.025, 12);
  const span = Math.max(farRef - nearRef, 1);
  const t = clampNumber((farRef - distance) / span, 0, 1);
  let scale: number;
  if (t < 0.5) {
    scale = 1 + 0.5 * (t / 0.5);
  } else if (t < 0.85) {
    scale = 1.5 + (2.8 - 1.5) * ((t - 0.5) / 0.35);
  } else {
    scale = 2.8 + (PAN_COMPENSATION_MAX - 2.8) * ((t - 0.85) / 0.15);
  }
  return clampNumber(scale, PAN_COMPENSATION_MIN, PAN_COMPENSATION_MAX);
}

export function viewportPanCompensation(viewportHeight: number): number {
  return clampNumber(640 / Math.max(viewportHeight, 1), 0.85, 1.25);
}

export type PanSpeedInput = {
  distance: number;
  cityDiagonal: number;
  viewportHeight: number;
  basePanSpeed?: number;
};

/** Keep the orbit target and camera above the city base — no underground views. */
export function applyCameraGroundConstraint(
  camera: { position: { x: number; y: number; z: number } },
  target: { x: number; y: number; z: number },
  cityBaseY: number,
  minHeight = CAMERA_MIN_HEIGHT_ABOVE_BASE_M,
): boolean {
  let changed = false;
  const floor = cityBaseY + minHeight;
  if (target.y < cityBaseY) {
    target.y = cityBaseY;
    changed = true;
  }
  if (camera.position.y < floor) {
    camera.position.y = floor;
    changed = true;
  }
  return changed;
}

export function panSpeedForDistance(input: PanSpeedInput): number {
  const base = input.basePanSpeed ?? BASE_PAN_SPEED;
  const distanceCompensation = distancePanCompensation(input.distance, input.cityDiagonal);
  const viewportCompensation = viewportPanCompensation(input.viewportHeight);
  return clampNumber(base * distanceCompensation * viewportCompensation, 0.5, 5);
}
