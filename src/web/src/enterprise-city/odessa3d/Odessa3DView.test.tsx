/**
 * Regression: Odessa 3D first paint must survive missing/partial progress
 * and keep a local diagnostic panel instead of the route error boundary.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { LoadingProgress, OdessaPerfDiagnostics } from "./types";
import { Odessa3DErrorBoundary } from "./Odessa3DErrorBoundary";

const onProgressRef: { current?: (p: LoadingProgress) => void } = {};
const onPerfRef: { current?: (s: OdessaPerfDiagnostics) => void } = {};
const onInitErrorRef: { current?: (msg: string, error?: Error) => void } = {};
const mountCount = { current: 0 };
const failNextMount = { current: false };
const throwOnConstruct = { current: false };

vi.mock("./odessaSceneController", () => {
  class FakeOdessaSceneController {
    constructor(
      _settings: unknown,
      callbacks: {
        onProgress?: (p: LoadingProgress) => void;
        onPerfStats?: (s: OdessaPerfDiagnostics) => void;
        onInitError?: (msg: string, error?: Error) => void;
      },
    ) {
      if (throwOnConstruct.current) {
        throw new Error("controller construct failed");
      }
      onProgressRef.current = callbacks.onProgress;
      onPerfRef.current = callbacks.onPerfStats;
      onInitErrorRef.current = callbacks.onInitError;
    }
    runtimeStatus() {
      return {
        phase: failNextMount.current ? "failed" : "ready",
        disposed: false,
        manifest: failNextMount.current ? "pending" : "ok:45 tiles",
        controller: failNextMount.current ? "failed" : "mounted",
        webgl: failNextMount.current ? "missing" : "ok",
        canvas: "800x520",
      };
    }
    async mount() {
      mountCount.current += 1;
      if (failNextMount.current) {
        const err = new Error("WebGLRenderer: Error creating WebGL context");
        err.name = "TypeError";
        onInitErrorRef.current?.("WebGLRenderer: Error creating WebGL context", err);
      }
    }
    dispose() {}
    resetCamera() {}
    setCameraViewMode() {}
    getCameraViewMode() {
      return "3d";
    }
    consumePendingGeoFocus() {}
    copyGeoDebug() {
      return "GEOREFERENCE";
    }
    focusGeo() {}
    cityDebugSnapshot() {
      return {
        fps: 48,
        camera: { x: 0, y: 40, z: 80 },
        target: { x: 0, y: 0, z: 0 },
        hovered: null,
        selected: null,
        hoveredCoords: null,
        selectedCoords: null,
        viewMode: "3d" as const,
      };
    }
    layerList() {
      return [];
    }
    diagnostics() {
      return {
        loadedAssets: 2,
        queuedAssets: 3,
        failedAssets: 0,
        camera: { x: 0, y: 40, z: 80 },
        activeLayers: ["city"],
        quality: "medium" as const,
        tilesActive: ["TILE_02_00"],
      };
    }
    handleClick() {}
    setInteractionEnabled() {}
    clearSelection() {}
    focusSelected() {}
    setShowSelectionBounds() {}
    setShowGeoGrid() {}
    copyClickCoordinates() {
      return null;
    }
    georeferenceStatus() {
      return "CALIBRATION_REQUIRED";
    }
    modelFingerprint() {
      return "odessa:test";
    }
    reloadGeoreference() {}
    setCalibrationPicking() {}
    setCalibrationMarkers() {}
    calibrationCameraPreset() {}
    hoverWorld() {
      return null;
    }
    modelRootTransform() {
      return { position: { x: 0, y: 0, z: 0 }, rotation: { x: 0, y: 0, z: 0 }, scale: { x: 1, y: 1, z: 1 } };
    }
    toggleLayer() {
      return true;
    }
    setShowTileBounds() {}
    setWaterDebug() {}
    setRenderIsolation() {}
    setFogEnabled() {}
    setDebugView() {}
    setVerticalRecoveryMode() {}
    exportSpikeReport() {
      return "{}";
    }
    bisect() {
      return {
        active: false,
        totalMeshes: 0,
        currentCount: 0,
        showing: "ALL",
        depth: 0,
        path: "-",
        currentNames: [],
      };
    }
    getRenderIsolation() { return { baseModelOnly: false, disableWater: false, disableOverlays: false, neutralMaterial: false }; }
  }
  return { OdessaSceneController: FakeOdessaSceneController };
});

import { Odessa3DView } from "./Odessa3DView";

const STUB_PERF: OdessaPerfDiagnostics = {
  fps: 48,
  frameMs: 20,
  drawCalls: 10,
  triangles: 1000,
  points: 0,
  lines: 0,
  visibleObjects: 4,
  loadedGlbs: 2,
  visibleGlbs: 2,
  queuedAssets: 3,
  activeTiles: 2,
  cameraDistance: 220,
  pixelRatio: 1,
  adaptiveTier: "medium",
  continuousRender: true,
  runtimeMode: "IDLE",
  streamingPaused: false,
  bootState: "INTERACTIVE",
  parsedCount: 2,
  downloadedCount: 2,
  pipeline: {
    fetching: 1,
    waitingParse: 0,
    parsing: 0,
    parsed: 2,
    waitingActivation: 0,
    active: 1,
    hidden: 0,
    failed: 0,
    fetchingMb: 4,
    waitingParseMb: 0,
    parsingMb: 0,
    currentParseId: null,
    currentParseSizeMb: 0,
    currentParseElapsedMs: 0,
    lastParseMs: 12,
    averageParseMs: 12,
    worstParseMs: 12,
    longTasks50: 0,
    longTasks100: 0,
    longTasks250: 0,
    longTasks500: 0,
    fetchQueue: 3,
    parseQueue: 0,
    activationQueue: 0,
    fetchConcurrent: 2,
    parseConcurrent: 1,
    backpressure: false,
    worstOffenders: [],
  },
};

const MANIFEST_PROGRESS: LoadingProgress = {
  total: 45,
  loaded: 2,
  failed: 0,
  queued: 3,
  loading: 1,
  percent: 4,
  bootState: "INTERACTIVE",
  activeCount: 1,
  downloadedCount: 2,
  parsedCount: 2,
  loadedMb: 3.2,
  totalMb: 382,
  currentAssetId: "TILE_02_00",
};

async function waitUntilMounted(minCount: number) {
  await waitFor(() => expect(mountCount.current).toBeGreaterThanOrEqual(minCount));
}

describe("Odessa3DView render", () => {
  beforeEach(() => {
    mountCount.current = 0;
    failNextMount.current = false;
    throwOnConstruct.current = false;
    onProgressRef.current = undefined;
    onPerfRef.current = undefined;
    onInitErrorRef.current = undefined;
  });

  it("renders with undefined progress before the loader emits (total = 0)", async () => {
    render(<Odessa3DView />);
    const shell = screen.getByTestId("odessa-3d-view");
    expect(shell.getAttribute("data-hud-total")).toBe("0");
    expect(shell.getAttribute("data-hud-boot")).toBe("BOOTSTRAP");
    expect(screen.getByTestId("odessa-3d-canvas")).toBeTruthy();
    expect(screen.getByTestId("odessa-pick-toggle")).toBeTruthy();
    expect(screen.getByTestId("odessa-home-view")).toBeTruthy();
    expect(screen.getByText("Общий вид")).toBeTruthy();
    expect(screen.getByTestId("odessa-view-2d")).toBeTruthy();
    expect(screen.getByTestId("odessa-view-3d")).toBeTruthy();
    expect(screen.queryByTestId("odessa-city-debug")).toBeNull();
    expect(screen.getByText("Выбор объектов")).toBeTruthy();
    expect(screen.getByText(/BOOTSTRAP · 0\/0/)).toBeTruthy();
    expect(screen.queryByText(/This view failed to render/)).toBeNull();
    await waitUntilMounted(1);
    expect(screen.getByTestId("odessa-3d-view").getAttribute("data-hud-total")).toBe("0");
  });

  it("renders with partial progress (no total yet)", async () => {
    render(<Odessa3DView />);
    await waitUntilMounted(1);
    act(() => {
      onProgressRef.current?.({
        loaded: 1,
        queued: 2,
        loading: 1,
        percent: 2,
        downloadedCount: 1,
        parsedCount: 0,
        activeCount: 0,
      } as LoadingProgress);
    });
    const shell = screen.getByTestId("odessa-3d-view");
    expect(shell.getAttribute("data-hud-total")).toBe("0");
    expect(shell.getAttribute("data-hud-queued")).toBe("2");
    expect(shell.getAttribute("data-hud-loading")).toBe("1");
    expect(screen.getByText(/BOOTSTRAP · 0\/0/)).toBeTruthy();
  });

  it("updates total 0 -> 45 when the manifest/loader progress arrives", async () => {
    render(<Odessa3DView />);
    expect(screen.getByTestId("odessa-3d-view").getAttribute("data-hud-total")).toBe("0");
    await waitUntilMounted(1);
    act(() => {
      onProgressRef.current?.(MANIFEST_PROGRESS);
    });
    await waitFor(() => {
      expect(screen.getByTestId("odessa-3d-view").getAttribute("data-hud-total")).toBe("45");
      expect(screen.getByText(/INTERACTIVE · 1\/45/)).toBeTruthy();
    });
  });

  it("survives 2D -> 3D -> 2D -> 3D remount", async () => {
    const first = render(<Odessa3DView />);
    await waitUntilMounted(1);
    expect(mountCount.current).toBe(1);
    first.unmount();
    const second = render(<Odessa3DView />);
    await waitUntilMounted(2);
    expect(mountCount.current).toBe(2);
    second.unmount();
    render(<Odessa3DView />);
    await waitUntilMounted(3);
    expect(mountCount.current).toBe(3);
    expect(screen.getByTestId("odessa-3d-canvas")).toBeTruthy();
    expect(screen.getByTestId("odessa-3d-view")).toBeTruthy();
  });

  it("shows a local diagnostic panel on controller init failure and keeps the canvas", async () => {
    failNextMount.current = true;
    render(<Odessa3DView />);
    await waitUntilMounted(1);
    const panel = screen.getByTestId("odessa-runtime-fault");
    expect(panel).toBeTruthy();
    expect(panel.textContent).toMatch(/TypeError/);
    expect(panel.textContent).toMatch(/WebGLRenderer/);
    expect(screen.getByTestId("odessa-fault-phase").textContent).toMatch(/failed|init/);
    expect(screen.getByTestId("odessa-3d-canvas")).toBeTruthy();
    expect(screen.getByTestId("odessa-3d-view")).toBeTruthy();
    expect(screen.queryByText(/This view failed to render/)).toBeNull();
  });

  it("does not throw a HUD ReferenceError for missing fields", async () => {
    render(<Odessa3DView showDev />);
    await waitUntilMounted(1);
    expect(() => {
      act(() => {
        onProgressRef.current?.(undefined as unknown as LoadingProgress);
      });
    }).not.toThrow();
    expect(() => {
      act(() => {
        onProgressRef.current?.({} as LoadingProgress);
      });
    }).not.toThrow();
    expect(screen.getByTestId("odessa-3d-view").getAttribute("data-hud-total")).toBe("0");
  });

  it("opens the owner calibration wizard from Геопривязка, not the debug panel", async () => {
    render(<Odessa3DView />);
    await waitUntilMounted(1);
    fireEvent.click(screen.getByTestId("odessa-cal-toggle"));
    expect(screen.getByTestId("odessa-cal-wizard")).toBeTruthy();
    expect(screen.queryByTestId("odessa-calibration-panel")).toBeNull();
    expect(screen.getByTestId("odessa-cal-wizard").textContent).toMatch(/шаг 1\/4/);
  });

  it("renders diagnostics using hud.total after manifest progress", async () => {
    render(<Odessa3DView showDev />);
    await waitUntilMounted(1);
    act(() => {
      onProgressRef.current?.(MANIFEST_PROGRESS);
      onPerfRef.current?.(STUB_PERF);
    });
    fireEvent.click(screen.getByTestId("odessa-perf-toggle"));
    await waitFor(() => expect(screen.getByText("3D Performance")).toBeTruthy());
    expect(screen.getByTestId("odessa-glb-pipeline")).toBeTruthy();
    expect(screen.getByTestId("odessa-boot-state").textContent).toBe("INTERACTIVE");
    const panel = screen.getByText("3D Performance").closest("section");
    expect(panel?.textContent).toMatch(/2\/45/);
    expect(panel?.textContent).toMatch(/1\/45/);
  });
});

describe("Odessa3DErrorBoundary", () => {
  it("shows the local diagnostic fallback instead of crashing the parent", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    function Boom() {
      throw new Error("hud boom");
    }
    render(
      <Odessa3DErrorBoundary
        fallback={(error) => (
          <div data-testid="odessa-runtime-fault">
            {error.name}:{error.message}
          </div>
        )}
      >
        <Boom />
      </Odessa3DErrorBoundary>,
    );
    expect(screen.getByTestId("odessa-runtime-fault").textContent).toMatch(/hud boom/);
    spy.mockRestore();
  });
});
