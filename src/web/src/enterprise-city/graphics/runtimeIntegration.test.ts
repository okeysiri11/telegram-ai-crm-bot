import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { isReducedMotionActive } from "./reducedMotion";
import { createPerformanceMonitor, shouldAdmitFrame } from "./performanceMonitor";

describe("Sprint CG-3 City Runtime Integration", () => {
  describe("reduced motion", () => {
    const root = document.documentElement;

    afterEach(() => {
      root.removeAttribute("data-reduced-motion");
    });

    it("is forced true when the graphics settings flag is set, regardless of anything else", () => {
      expect(isReducedMotionActive(true)).toBe(true);
    });

    it("reads the platform's real data-reduced-motion attribute", () => {
      root.setAttribute("data-reduced-motion", "true");
      expect(isReducedMotionActive(false)).toBe(true);
      root.setAttribute("data-reduced-motion", "false");
      expect(isReducedMotionActive(false)).toBe(false);
    });

    it("falls back to false when no signal indicates reduced motion", () => {
      root.removeAttribute("data-reduced-motion");
      expect(isReducedMotionActive(false)).toBe(false);
    });
  });

  describe("frame admission throttle", () => {
    it("always admits when fpsLimit is 0 or negative (no throttle configured)", () => {
      expect(shouldAdmitFrame(performance.now(), 0)).toBe(true);
      expect(shouldAdmitFrame(performance.now(), -5)).toBe(true);
    });

    it("rejects a frame that arrives before the fps budget has elapsed", () => {
      const now = performance.now();
      expect(shouldAdmitFrame(now, 30)).toBe(false);
    });

    it("admits a frame once the fps budget has elapsed", () => {
      const past = performance.now() - 1000;
      expect(shouldAdmitFrame(past, 30)).toBe(true);
    });
  });

  describe("performance monitor", () => {
    let nowValue = 0;

    beforeEach(() => {
      nowValue = 0;
      vi.spyOn(performance, "now").mockImplementation(() => nowValue);
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it("derives FPS from a rolling window of recorded frame timestamps", () => {
      const monitor = createPerformanceMonitor(1000);
      for (let i = 0; i < 10; i++) {
        nowValue += 16; // ~60fps spacing
        monitor.measureFrame(() => {});
      }
      const snap = monitor.snapshot();
      expect(snap.fps).toBeGreaterThan(50);
      expect(snap.fps).toBeLessThan(70);
    });

    it("reports 0 fps with fewer than two recorded frames", () => {
      const monitor = createPerformanceMonitor(1000);
      expect(monitor.snapshot().fps).toBe(0);
      monitor.measureFrame(() => {});
      expect(monitor.snapshot().fps).toBe(0);
    });

    it("measures CPU time as the wrapped work's own duration", () => {
      const monitor = createPerformanceMonitor(1000);
      monitor.measureFrame(() => {
        nowValue += 5;
      });
      expect(monitor.snapshot().cpuTimeMs).toBe(5);
    });

    it("measures render time independently of frame (CPU) time", () => {
      const monitor = createPerformanceMonitor(1000);
      monitor.measureFrame(() => {
        nowValue += 4;
        monitor.measureRender(() => {
          nowValue += 1;
        });
      });
      const snap = monitor.snapshot();
      expect(snap.cpuTimeMs).toBe(5);
      expect(snap.renderTimeMs).toBe(1);
    });

    it("drops frame timestamps that fall outside the rolling window", () => {
      const monitor = createPerformanceMonitor(100);
      monitor.measureFrame(() => {});
      nowValue += 500; // well past the 100ms window
      monitor.measureFrame(() => {});
      // Only the most recent timestamp should remain in-window, so fps collapses to 0 (fewer than 2 samples).
      expect(monitor.snapshot().fps).toBe(0);
    });

    it("reset() clears the rolling window", () => {
      const monitor = createPerformanceMonitor(1000);
      monitor.measureFrame(() => {});
      nowValue += 16;
      monitor.measureFrame(() => {});
      expect(monitor.snapshot().fps).toBeGreaterThan(0);
      monitor.reset();
      expect(monitor.snapshot().fps).toBe(0);
    });

    it("reports memory as null when performance.memory is unavailable (non-Chrome)", () => {
      const monitor = createPerformanceMonitor(1000);
      expect(monitor.snapshot().memoryMb).toBeNull();
    });
  });
});
