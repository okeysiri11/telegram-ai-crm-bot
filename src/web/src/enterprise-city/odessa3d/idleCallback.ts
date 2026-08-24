/**
 * Safari-safe idle scheduling + main-thread yield between GLB parses.
 * No Chromium-only APIs. No WebGPU.
 */

export type IdleDeadlineLike = {
  timeRemaining: () => number;
  didTimeout: boolean;
};

export function hasRequestIdleCallback(): boolean {
  return typeof requestIdleCallback === "function";
}

export function scheduleIdleWork(
  fn: (deadline: IdleDeadlineLike) => void,
  timeoutMs = 1000,
): { cancel: () => void } {
  if (typeof requestIdleCallback === "function" && typeof cancelIdleCallback === "function") {
    const id = requestIdleCallback((d) => fn({ timeRemaining: () => d.timeRemaining(), didTimeout: d.didTimeout }), {
      timeout: timeoutMs,
    });
    return { cancel: () => cancelIdleCallback(id) };
  }
  const t = setTimeout(() => {
    fn({ timeRemaining: () => 2, didTimeout: true });
  }, 16);
  return { cancel: () => clearTimeout(t) };
}

export function yieldToNextFrame(): Promise<void> {
  return new Promise((resolve) => {
    if (typeof requestAnimationFrame === "function") {
      requestAnimationFrame(() => resolve());
      return;
    }
    setTimeout(resolve, 0);
  });
}
