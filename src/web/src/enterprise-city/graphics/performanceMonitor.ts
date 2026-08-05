/**
 * Enterprise City Graphics Engine — Performance Monitor.
 * Sprint CG-3. Framework-agnostic `requestAnimationFrame`-driven sampler feeding the Developer
 * Overlay: FPS, JS frame ("CPU") time, DOM-write ("render") time, and heap memory where the browser
 * exposes it. No polling — every sample is recorded from inside a real rAF tick the caller already
 * scheduled; this module does not start its own timer loop.
 */

export type PerformanceSnapshot = {
  fps: number;
  cpuTimeMs: number;
  renderTimeMs: number;
  memoryMb: number | null;
};

function clock(): number {
  return typeof performance !== "undefined" ? performance.now() : Date.now();
}

export type PerformanceMonitor = {
  /** Wrap the whole per-frame JS work (camera tween step, effect bookkeeping, ...) — feeds FPS + CPU time. */
  measureFrame<T>(work: () => T): T;
  /** Wrap just the DOM-mutating portion of a frame (e.g. the transform write) — feeds render time. */
  measureRender<T>(work: () => T): T;
  snapshot(): PerformanceSnapshot;
  /** Clear the rolling FPS window — call when animation resumes after a pause so stale gaps don't skew it. */
  reset(): void;
};

/** `historyMs` bounds the rolling window used to derive FPS from recent frame timestamps. */
export function createPerformanceMonitor(historyMs = 1000): PerformanceMonitor {
  let frameTimestamps: number[] = [];
  let lastCpuTimeMs = 0;
  let lastRenderTimeMs = 0;

  function recordFrameTimestamp() {
    const now = clock();
    frameTimestamps.push(now);
    const cutoff = now - historyMs;
    while (frameTimestamps.length && frameTimestamps[0] < cutoff) frameTimestamps.shift();
  }

  function fps(): number {
    if (frameTimestamps.length < 2) return 0;
    const spanMs = frameTimestamps[frameTimestamps.length - 1]! - frameTimestamps[0]!;
    if (spanMs <= 0) return 0;
    return ((frameTimestamps.length - 1) * 1000) / spanMs;
  }

  function memoryMb(): number | null {
    const mem = (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory;
    return mem ? mem.usedJSHeapSize / (1024 * 1024) : null;
  }

  return {
    measureFrame(work) {
      const start = clock();
      const result = work();
      lastCpuTimeMs = clock() - start;
      recordFrameTimestamp();
      return result;
    },
    measureRender(work) {
      const start = clock();
      const result = work();
      lastRenderTimeMs = clock() - start;
      return result;
    },
    snapshot() {
      return { fps: fps(), cpuTimeMs: lastCpuTimeMs, renderTimeMs: lastRenderTimeMs, memoryMb: memoryMb() };
    },
    reset() {
      frameTimestamps = [];
    },
  };
}

/** True if at least `1000 / fpsLimit` ms have elapsed since `lastMs` — the engine's one throttle rule. */
export function shouldAdmitFrame(lastMs: number, fpsLimit: number): boolean {
  if (fpsLimit <= 0) return true;
  return clock() - lastMs >= 1000 / fpsLimit;
}

export function now(): number {
  return clock();
}
