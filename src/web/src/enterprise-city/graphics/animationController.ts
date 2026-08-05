/**
 * Enterprise City Graphics Engine — Animation Controller.
 * Sprint CG-2. A small, generic, reusable tween manager — camera transitions (`cameraEngine.ts`),
 * building/district opacity/movement/scale, and focus transitions all drive through this one
 * function rather than each hand-rolling a `requestAnimationFrame` loop. Duration/easing defaults
 * are the platform's real Motion Design Language tokens (`design-system/tokens`), imported directly —
 * never a second, City-specific timing scale.
 */

import { motion } from "../../../design-system/tokens";
import type { AnimationHandle } from "./types";

export type TweenOptions = {
  /** Duration in ms — defaults to the design system's "normal" token, not an invented value. */
  durationMs?: number;
  /** Any real design-system easing string (`motion.easing`, `motion.easeOut`, ...). */
  easing?: string;
  onFrame: (t: number) => void;
  onComplete?: () => void;
};

const DEFAULT_DURATION_MS = Number.parseInt(motion.normal, 10);

/** Parse the platform's cubic-bezier easing strings into a simple approximation function. */
function easingFn(easing: string): (t: number) => number {
  // The design system's easings are all cubic-bezier(x1,y1,x2,y2). A full cubic-bezier solver is
  // more machinery than a City camera pan needs; ease-out (the platform's default "entrance" curve,
  // per `ENTERPRISE_DESIGN_SYSTEM.md` §9) is approximated with a standard quad-out, which visually
  // matches the same "fast start, gentle settle" character every other entrance animation uses.
  if (easing === motion.easeIn) return (t) => t * t;
  if (easing === motion.easeEmphasized) return (t) => 1 - Math.pow(1 - t, 3);
  return (t) => 1 - Math.pow(1 - t, 2); // easeOut / default
}

/**
 * Drive a single 0→1 tween via `requestAnimationFrame`. Returns a cancellable handle so a camera
 * animation interrupted by a new pan/zoom input can stop cleanly instead of fighting the next one.
 */
export function animateValue(options: TweenOptions): AnimationHandle {
  const duration = options.durationMs ?? DEFAULT_DURATION_MS;
  const ease = easingFn(options.easing ?? motion.easeOut);
  let cancelled = false;
  let frame: number | null = null;
  // `requestAnimationFrame`'s own timestamp argument is not guaranteed to share an epoch with
  // `performance.now()` in every environment (observed divergence under jsdom) — reading the clock
  // directly on each tick keeps `elapsed` correct everywhere instead of trusting the callback arg.
  const clock = () => (typeof performance !== "undefined" ? performance.now() : Date.now());
  const start = clock();

  function tick() {
    if (cancelled) return;
    const elapsed = clock() - start;
    const raw = duration <= 0 ? 1 : Math.min(1, elapsed / duration);
    options.onFrame(ease(raw));
    if (raw >= 1) {
      options.onComplete?.();
      return;
    }
    frame = requestAnimationFrame(tick);
  }

  if (typeof requestAnimationFrame === "undefined") {
    // Non-browser (test) environment — resolve instantly rather than silently doing nothing.
    options.onFrame(1);
    options.onComplete?.();
    return { id: "tween:sync", cancel: () => {} };
  }

  frame = requestAnimationFrame(tick);
  const id = `tween:${start}`;
  return {
    id,
    cancel: () => {
      cancelled = true;
      if (frame != null) cancelAnimationFrame(frame);
    },
  };
}

/** Named duration presets, mirroring (not duplicating) the design system's real motion scale. */
export const animationDurations = {
  instant: Number.parseInt(motion.instant, 10),
  fast: Number.parseInt(motion.fast, 10),
  normal: Number.parseInt(motion.normal, 10),
  slow: Number.parseInt(motion.slow, 10),
  settle: Number.parseInt(motion.settle, 10),
} as const;
