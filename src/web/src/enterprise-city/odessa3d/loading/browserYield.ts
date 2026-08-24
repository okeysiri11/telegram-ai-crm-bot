/**
 * Safari-safe yield primitives for the GLB parse scheduler.
 * Never requires scheduler.postTask, requestIdleCallback, SharedArrayBuffer, or WebGPU.
 */

import { yieldToNextFrame } from "../idleCallback";

type SchedulerLike = {
  postTask?: (fn: () => unknown, opts?: { priority?: string }) => Promise<unknown>;
};

export function hasSchedulerPostTask(): boolean {
  const s = (globalThis as { scheduler?: SchedulerLike }).scheduler;
  return typeof s?.postTask === "function";
}

/** Noncritical continuation. Prefer postTask when present; otherwise one animation frame. */
export function yieldToScheduler(): Promise<void> {
  const s = (globalThis as { scheduler?: SchedulerLike }).scheduler;
  if (typeof s?.postTask === "function") {
    return s.postTask(() => undefined, { priority: "user-visible" }).then(
      () => undefined,
      () => undefined,
    );
  }
  return yieldToNextFrame();
}

/**
 * Guaranteed paint opportunity after a heavy GLTF.parse.
 * Double rAF is the portable "wait at least one rendered frame" pattern.
 */
export function yieldForRenderOpportunity(): Promise<void> {
  return yieldToNextFrame().then(() => yieldToNextFrame());
}

export function yieldAfterParse(heavy: boolean): Promise<void> {
  return heavy ? yieldForRenderOpportunity() : yieldToScheduler();
}
