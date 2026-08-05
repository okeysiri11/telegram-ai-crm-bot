/**
 * Enterprise City Graphics Engine — Runtime Integration Hook.
 * Sprint CG-3. The one integration point `EnterpriseCityPage.tsx` uses to consume the CG-2 Graphics
 * Engine (camera, render pipeline, effects, config) as live behavior. Owns no business logic and no
 * new store — it composes the existing engine modules (`cameraEngine`, `animationController`,
 * `visualEffects`, `renderPipeline`, `graphicsConfig`) plus the real `cityEngine.ts` persistence
 * (`writeViewport`) into React-friendly state and imperative helpers.
 *
 * Performance contract this hook exists to satisfy:
 *  - Camera transitions write `transform` directly to the plane DOM node on every animation frame;
 *    React state (and `sessionStorage` via `writeViewport`) is only touched once, when the transition
 *    completes — an animated focus/reset/zoom no longer costs one re-render per frame.
 *  - Every animation loop is driven by the CG-2 `animateValue` (`requestAnimationFrame`); nothing in
 *    this module uses `setInterval`/polling.
 *  - A single `fpsLimit`-derived throttle (`shouldAdmitFrame`) gates DOM writes and dev-overlay
 *    sampling so a High/Ultra-quality display doesn't do more work than its configured budget.
 *  - `document.visibilitychange` snaps any in-flight camera transition to its target and sets
 *    `data-tab-hidden` on the City root, which one CSS rule (`motion.css`) uses to pause every
 *    continuous City animation (AI dot, road flow, focus breathe) at once.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import type { CityBuilding, CityBuildingId, CityDistrictId, CityLiveStatus } from "../cityCatalog";
import type { CityDistrictMeta } from "../cityDistricts";
import { writeViewport, type CityViewport } from "../cityEngine";
import { animateViewport, focusBuilding, focusDistrict, resetCamera, type CameraAnimationOptions } from "./cameraEngine";
import { resolveEffect } from "./visualEffects";
import { readGraphicsSettings, writeGraphicsSettings } from "./graphicsConfig";
import { createCityFrame, type CityFrame } from "./renderPipeline";
import { isReducedMotionActive } from "./reducedMotion";
import { createPerformanceMonitor, shouldAdmitFrame, type PerformanceSnapshot } from "./performanceMonitor";
import type { AnimationHandle, EffectKind, GraphicsSettings, ResolvedEffect } from "./types";

const PORTAL_MAX_DELAY_MS = 260;

export type TransientEffectMap = Record<string, ResolvedEffect>;

export type CityGraphicsRuntime = {
  frame: CityFrame;
  settings: GraphicsSettings;
  reducedMotion: boolean;
  perf: PerformanceSnapshot;
  buildingEffects: TransientEffectMap;
  districtEffects: TransientEffectMap;
  animationQueueLength: number;
  updateSettings: (next: GraphicsSettings) => void;
  /** Synchronous read of the camera's true current position, including mid-animation — for callers
   * (e.g. drag-start) that need the live value rather than the React-state snapshot, which is
   * deliberately not updated per animation frame. */
  getLiveViewport: () => CityViewport;
  /** Cancel any in-flight camera tween immediately (e.g. the user grabbed the map mid-transition). */
  cancelActiveAnimation: () => void;
  animateViewportTo: (target: CityViewport, opts?: { durationMs?: number }) => void;
  focusBuildingAnimated: (building: CityBuilding, opts?: { durationMs?: number }) => void;
  focusDistrictAnimated: (district: CityDistrictMeta, opts?: { durationMs?: number }) => void;
  resetCameraAnimated: () => void;
  triggerBuildingEffect: (id: CityBuildingId, kind: EffectKind) => void;
  triggerDistrictEffect: (id: CityDistrictId, kind: EffectKind) => void;
  playPortalEffect: (id: CityBuildingId) => Promise<void>;
};

/** Detects a meaningful runtime change worth an activation flash — not every field mutation. */
function statusChangedMeaningfully(prev: CityLiveStatus | undefined, next: CityLiveStatus): boolean {
  if (!prev) return false;
  return (
    prev.tone !== next.tone ||
    prev.tasks !== next.tasks ||
    prev.notifications !== next.notifications ||
    prev.aiActive !== next.aiActive
  );
}

export function useCityGraphicsRuntime(
  planeRef: RefObject<HTMLDivElement | null>,
  cityRootRef: RefObject<HTMLDivElement | null>,
  viewport: CityViewport,
  commitViewport: (v: CityViewport) => void,
  statusById: Record<CityBuildingId, CityLiveStatus>,
): CityGraphicsRuntime {
  const [settings, setSettings] = useState<GraphicsSettings>(() => readGraphicsSettings());
  const [reducedMotion, setReducedMotion] = useState(() => isReducedMotionActive(settings.reducedMotion));
  const [perf, setPerf] = useState<PerformanceSnapshot>({ fps: 0, cpuTimeMs: 0, renderTimeMs: 0, memoryMb: null });
  const [buildingEffects, setBuildingEffects] = useState<TransientEffectMap>({});
  const [districtEffects, setDistrictEffects] = useState<TransientEffectMap>({});
  const [animationQueueLength, setAnimationQueueLength] = useState(0);

  const monitorRef = useRef(createPerformanceMonitor());
  const activeHandleRef = useRef<AnimationHandle | null>(null);
  const queueSizeRef = useRef(0);
  const tabHiddenRef = useRef(false);
  const lastAdmittedFrameRef = useRef(0);
  const lastPerfSampleRef = useRef(0);
  const effectTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  // The true current visual viewport — updated on every animation frame, not just at commit. Using
  // the `viewport` prop directly as an animation's "from" would be stale for the whole duration of
  // any in-flight tween (React state is deliberately not touched per-frame, see module header), which
  // would make a second rapid input (e.g. two fast wheel ticks) restart from a stale position and
  // visibly stutter. This ref is always the source of truth for "where the camera actually is now".
  const liveViewportRef = useRef<CityViewport>(viewport);

  useEffect(() => {
    if (!activeHandleRef.current) liveViewportRef.current = viewport;
  }, [viewport]);

  const updateSettings = useCallback((next: GraphicsSettings) => {
    writeGraphicsSettings(next);
    setSettings(next);
  }, []);

  const frame = useMemo(
    () => createCityFrame({ viewport, settings }),
    [viewport, settings],
  );

  // Re-derive reduced motion whenever graphics settings change; the OS-level query is re-checked
  // per animation call (isReducedMotionActive), this state only tracks the settings-driven half.
  useEffect(() => {
    setReducedMotion(isReducedMotionActive(settings.reducedMotion));
  }, [settings.reducedMotion]);

  const bumpQueue = useCallback((delta: number) => {
    queueSizeRef.current = Math.max(0, queueSizeRef.current + delta);
    setAnimationQueueLength(queueSizeRef.current);
  }, []);

  const runCameraTween = useCallback(
    (run: (opts: CameraAnimationOptions) => AnimationHandle, durationMs?: number) => {
      activeHandleRef.current?.cancel();
      const plane = planeRef.current;
      const effectiveReducedMotion = reducedMotion || tabHiddenRef.current;
      if (plane) plane.classList.add("ec-plane--js-anim");
      bumpQueue(1);

      const finish = (v: CityViewport) => {
        if (plane) plane.classList.remove("ec-plane--js-anim");
        liveViewportRef.current = v;
        commitViewport(v);
        writeViewport(v);
        activeHandleRef.current = null;
        bumpQueue(-1);
      };

      const handle = run({
        durationMs,
        reducedMotion: effectiveReducedMotion,
        onFrame: (v) => {
          monitorRef.current.measureFrame(() => {
            liveViewportRef.current = v;
            const fpsLimit = settings.fpsLimit || 60;
            if (!shouldAdmitFrame(lastAdmittedFrameRef.current, fpsLimit)) return;
            lastAdmittedFrameRef.current = performance.now();
            if (plane) {
              monitorRef.current.measureRender(() => {
                plane.style.transform = `translate(${v.x}%, ${v.y}%) scale(${v.zoom})`;
              });
            }
          });
        },
        onComplete: finish,
      });
      activeHandleRef.current = handle;
    },
    [bumpQueue, commitViewport, planeRef, reducedMotion, settings.fpsLimit],
  );

  const animateViewportTo = useCallback<CityGraphicsRuntime["animateViewportTo"]>(
    (target, opts) => runCameraTween((o) => animateViewport(liveViewportRef.current, target, o), opts?.durationMs),
    [runCameraTween],
  );

  const focusBuildingAnimated = useCallback<CityGraphicsRuntime["focusBuildingAnimated"]>(
    (building, opts) =>
      runCameraTween((o) => focusBuilding(liveViewportRef.current, building, o), opts?.durationMs ?? 320),
    [runCameraTween],
  );

  const focusDistrictAnimated = useCallback<CityGraphicsRuntime["focusDistrictAnimated"]>(
    (district, opts) =>
      runCameraTween((o) => focusDistrict(liveViewportRef.current, district, o), opts?.durationMs ?? 320),
    [runCameraTween],
  );

  const resetCameraAnimated = useCallback<CityGraphicsRuntime["resetCameraAnimated"]>(
    () => runCameraTween((o) => resetCamera(liveViewportRef.current, o), 400),
    [runCameraTween],
  );

  const scheduleEffectClear = useCallback((key: string, durationMs: number, clear: () => void) => {
    const existing = effectTimersRef.current.get(key);
    if (existing) clearTimeout(existing);
    const timer = setTimeout(() => {
      clear();
      effectTimersRef.current.delete(key);
    }, Math.max(durationMs, 1));
    effectTimersRef.current.set(key, timer);
  }, []);

  const triggerBuildingEffect = useCallback<CityGraphicsRuntime["triggerBuildingEffect"]>(
    (id, kind) => {
      if (reducedMotion || tabHiddenRef.current || !frame.layers.isEnabled("effects")) return;
      const resolved = resolveEffect(kind, false);
      setBuildingEffects((prev) => ({ ...prev, [id]: resolved }));
      scheduleEffectClear(`building:${id}`, resolved.durationMs, () =>
        setBuildingEffects((prev) => {
          if (prev[id] !== resolved) return prev;
          const { [id]: _drop, ...rest } = prev;
          return rest;
        }),
      );
    },
    [frame.layers, reducedMotion, scheduleEffectClear],
  );

  const triggerDistrictEffect = useCallback<CityGraphicsRuntime["triggerDistrictEffect"]>(
    (id, kind) => {
      if (reducedMotion || tabHiddenRef.current || !frame.layers.isEnabled("effects")) return;
      const resolved = resolveEffect(kind, false);
      setDistrictEffects((prev) => ({ ...prev, [id]: resolved }));
      scheduleEffectClear(`district:${id}`, resolved.durationMs, () =>
        setDistrictEffects((prev) => {
          if (prev[id] !== resolved) return prev;
          const { [id]: _drop, ...rest } = prev;
          return rest;
        }),
      );
    },
    [frame.layers, reducedMotion, scheduleEffectClear],
  );

  const playPortalEffect = useCallback<CityGraphicsRuntime["playPortalEffect"]>(
    (id) => {
      const skip = reducedMotion || tabHiddenRef.current || settings.quality === "low" || !frame.layers.isEnabled("effects");
      if (skip) return Promise.resolve();
      const resolved = resolveEffect("building_activation", false);
      const delay = Math.min(resolved.durationMs, PORTAL_MAX_DELAY_MS);
      setBuildingEffects((prev) => ({ ...prev, [id]: { ...resolved, className: "is-portal" } }));
      return new Promise((resolve) => {
        scheduleEffectClear(`building:${id}`, delay, () => {
          setBuildingEffects((prev) => {
            const { [id]: _drop, ...rest } = prev;
            return rest;
          });
          resolve();
        });
      });
    },
    [frame.layers, reducedMotion, scheduleEffectClear, settings.quality],
  );

  // Runtime event animations: flash a building only when its real live status changed meaningfully.
  const prevStatusRef = useRef<Record<string, CityLiveStatus>>({});
  useEffect(() => {
    const prev = prevStatusRef.current;
    for (const [id, status] of Object.entries(statusById)) {
      if (statusChangedMeaningfully(prev[id], status)) {
        triggerBuildingEffect(id as CityBuildingId, "building_activation");
      }
    }
    prevStatusRef.current = statusById;
  }, [statusById, triggerBuildingEffect]);

  // Tab-visibility: pause continuous CSS loops and snap any in-flight camera tween to its target.
  useEffect(() => {
    function onVisibility() {
      const hidden = document.hidden;
      tabHiddenRef.current = hidden;
      cityRootRef.current?.setAttribute("data-tab-hidden", hidden ? "true" : "false");
      if (hidden) {
        activeHandleRef.current?.cancel();
        activeHandleRef.current = null;
        queueSizeRef.current = 0;
        setAnimationQueueLength(0);
        monitorRef.current.reset();
      }
    }
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [cityRootRef]);

  // Dev-overlay sampler: throttled to ~4Hz React updates regardless of the underlying rAF rate, so
  // the overlay never becomes its own source of 60Hz re-renders.
  useEffect(() => {
    let raf = 0;
    function tick() {
      if (!tabHiddenRef.current) {
        const now = performance.now();
        if (now - lastPerfSampleRef.current > 250) {
          lastPerfSampleRef.current = now;
          setPerf(monitorRef.current.snapshot());
        }
        monitorRef.current.measureFrame(() => {});
      }
      raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const timers = effectTimersRef.current;
    return () => {
      activeHandleRef.current?.cancel();
      timers.forEach((t) => clearTimeout(t));
    };
  }, []);

  const getLiveViewport = useCallback(() => liveViewportRef.current, []);

  const cancelActiveAnimation = useCallback(() => {
    if (!activeHandleRef.current) return;
    activeHandleRef.current.cancel();
    activeHandleRef.current = null;
    planeRef.current?.classList.remove("ec-plane--js-anim");
    bumpQueue(-1);
  }, [bumpQueue, planeRef]);

  return {
    frame,
    settings,
    reducedMotion,
    perf,
    buildingEffects,
    districtEffects,
    animationQueueLength,
    updateSettings,
    getLiveViewport,
    cancelActiveAnimation,
    animateViewportTo,
    focusBuildingAnimated,
    focusDistrictAnimated,
    resetCameraAnimated,
    triggerBuildingEffect,
    triggerDistrictEffect,
    playPortalEffect,
  };
}
