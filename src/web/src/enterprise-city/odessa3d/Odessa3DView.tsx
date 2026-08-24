/**
 * React shell for Odessa 3D — canvas + controls; scene in controller ref.
 * HUD values come only from normalizeHudProgress — never a free `total` binding.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { OdessaSceneController } from "./odessaSceneController";
import { resolveQuality, readQualityProfile } from "./qualityProfile";
import type { QualityProfile, LoadingProgress, OdessaPerfDiagnostics } from "./types";
import { getCityEntity, resolvePlatformRoute } from "./cityEntityRegistry";
import { HUD_THROTTLE_MS } from "./odessaPerformance";
import { normalizeHudProgress } from "./hudProgress";
import { Odessa3DErrorBoundary, OdessaRuntimeFaultPanel, type OdessaCaughtError } from "./Odessa3DErrorBoundary";
import { OdessaObjectPanel } from "./interaction/OdessaObjectPanel";
import type { EntityBindingResult, InteractionSnapshot, PickableEntity } from "./interaction";
import {
  CalibrationPanel,
  CalibrationWizard,
  CALIBRATION_SLOTS,
  emptyCheckDraft,
  buildAuthoredRecord,
  captureControlWorld,
  checkFromObservation,
  draftFromControlPoints,
  draftFromObservations,
  emptyCalibrationDraft,
  evaluateCalibrationDraft,
  exportAuthoredCalibrationJson,
  formatCalibrationSessionDebug,
  formatGeoreferenceDiagnosticV3,
  importAuthoredCalibrationJson,
  loadAuthoredCalibration,
  loadRawObservations,
  resetAuthoredCalibration,
  saveAuthoredCalibration,
  saveRawObservations,
  IDENTITY_MODEL_ROOT,
  PICK_COORDINATE_SPACE,
  geoSelectionBridge,
  type CalibrationDraft,
  type CalibrationSlotId,
  type CheckDraft,
} from "./geospatial";
import { DEFAULT_RENDER_ISOLATION, type RenderIsolationState } from "./renderStability";
import { DEFAULT_DEBUG_VIEW, type BisectStatus, type DebugViewState } from "./renderDebugTools";
import { ODESSA_VERTICAL_RECOVERY_MODE, type VerticalRecoveryMode } from "./verticalRecovery";
import { activeOdessaPackage, storePackageId, type OdessaPackageId } from "./odessaPackage";
import { emptyCityDebugSnapshot, formatCityGeoDebug, isCityDebugEnabled, type CityDebugSnapshot } from "./cityDebug";
import type { CityCameraViewMode } from "./cameraViewMode";

type Props = {
  qualityProfile?: QualityProfile;
  onOpenRoute?: (route: string) => void;
  onSelectBuildingId?: (buildingId: string | null) => void;
  showDev?: boolean;
};

type InitFault = {
  name: string;
  message: string;
  stack: string;
  phase: string;
  manifest: string;
  controller: string;
  webgl: string;
};

function fmtMs(v: number | null | undefined): string {
  return v == null ? "—" : `${Math.round(v)}`;
}

function stackHead(err: unknown): string {
  if (err instanceof Error && typeof err.stack === "string") {
    return err.stack.split("\n").slice(0, 8).join("\n");
  }
  return "";
}

export function Odessa3DView(props: Props) {
  return (
    <Odessa3DErrorBoundary
      fallback={(error: OdessaCaughtError, reset) => (
        <OdessaRuntimeFaultPanel
          phase="render"
          errorName={error.name}
          errorMessage={error.message}
          stack={error.stack}
          manifest="unknown"
          controller="render-throw"
          webgl="unknown"
          progressJson="{}"
          onRetry={reset}
        />
      )}
    >
      <Odessa3DViewInner {...props} />
    </Odessa3DErrorBoundary>
  );
}

function Odessa3DViewInner({
  qualityProfile: qualityProfileProp,
  onOpenRoute,
  onSelectBuildingId,
  showDev = false,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const controllerRef = useRef<OdessaSceneController | null>(null);
  const onSelectRef = useRef(onSelectBuildingId);
  onSelectRef.current = onSelectBuildingId;
  const [progress, setProgress] = useState<LoadingProgress | undefined>(undefined);
  const [layers, setLayers] = useState<{ id: string; label: string; visible: boolean }[]>([]);
  const [initFault, setInitFault] = useState<InitFault | null>(null);
  const [mountEpoch, setMountEpoch] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pickEnabled, setPickEnabled] = useState(true);
  const [pickable, setPickable] = useState<PickableEntity | null>(null);
  const [binding, setBinding] = useState<EntityBindingResult | null>(null);
  const [selectedActive, setSelectedActive] = useState(false);
  const [objectGeo, setObjectGeo] = useState<{ lat: number; lon: number } | null>(null);
  const [showPickBounds, setShowPickBounds] = useState(false);
  const [showGeoGrid, setShowGeoGrid] = useState(false);
  const [clickGeo, setClickGeo] = useState<{ lat: number; lon: number } | null>(null);
  const [geoReady, setGeoReady] = useState(false);
  const [geoStatus, setGeoStatus] = useState<string>("CALIBRATION_REQUIRED");
  const [calOpen, setCalOpen] = useState(false);
  const [calDraft, setCalDraft] = useState<CalibrationDraft>(() => emptyCalibrationDraft());
  const [pickingSlot, setPickingSlot] = useState<CalibrationSlotId | "CHECK" | null>(null);
  const [checkDraft, setCheckDraft] = useState<CheckDraft>(() => emptyCheckDraft());
  const [calSaved, setCalSaved] = useState(false);
  const [calMessage, setCalMessage] = useState<string | null>(null);
  const [cursorWorld, setCursorWorld] = useState<{ x: number; y: number; z: number } | null>(null);
  const [wizardKey, setWizardKey] = useState(0);
  const pickingSlotRef = useRef<CalibrationSlotId | "CHECK" | null>(null);
  pickingSlotRef.current = pickingSlot;
  const calDraftRef = useRef(calDraft);
  calDraftRef.current = calDraft;
  const [diag, setDiag] = useState<ReturnType<OdessaSceneController["diagnostics"]> | null>(null);
  const [perf, setPerf] = useState<OdessaPerfDiagnostics | null>(null);
  const [showTileBounds, setShowTileBounds] = useState(false);
  const [showPerfPanel, setShowPerfPanel] = useState(false);
  const [showWaterDebug, setShowWaterDebug] = useState(false);
  const [isolation, setIsolation] = useState<RenderIsolationState>({ ...DEFAULT_RENDER_ISOLATION });
  const [fogDisabled, setFogDisabled] = useState(false);
  const [debugView, setDebugView] = useState<DebugViewState>({ ...DEFAULT_DEBUG_VIEW });
  const [recoveryMode, setRecoveryMode] = useState<VerticalRecoveryMode>(ODESSA_VERTICAL_RECOVERY_MODE);
  const [bisect, setBisect] = useState<BisectStatus | null>(null);
  const [viewMode, setViewMode] = useState<CityCameraViewMode>("3d");
  const cityDebug = isCityDebugEnabled();
  const [debugSnap, setDebugSnap] = useState<CityDebugSnapshot>(() => emptyCityDebugSnapshot());
  const profile = qualityProfileProp ?? readQualityProfile();
  const quality = useMemo(() => resolveQuality(profile), [profile]);
  const showLoaderDiag = showDev && import.meta.env.DEV;
  const hud = normalizeHudProgress(progress, perf);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let cancelled = false;
    let started = false;
    let ctrl: OdessaSceneController | null = null;
    let raf = 0;
    let timer = 0;
    setInitFault(null);
    setProgress(undefined);
    setPerf(null);
    setShowWaterDebug(false);

    const captureFault = (err: unknown, phase: string) => {
      const error = err instanceof Error ? err : new Error(String(err));
      const status = ctrl?.runtimeStatus();
      setInitFault({
        name: error.name || "Error",
        message: error.message || String(err),
        stack: stackHead(error),
        phase: status?.phase || phase,
        manifest: status?.manifest || "pending",
        controller: status?.controller || "failed",
        webgl: status?.webgl || "unknown",
      });
    };

    const start = () => {
      if (cancelled || started) return;
      started = true;
      try {
        ctrl = new OdessaSceneController(quality, {
          onProgress: (p) => {
            if (!cancelled) setProgress(p);
          },
          onSelect: (id) => {
            setSelectedId(id);
            const ent = id ? getCityEntity(id) : null;
            onSelectRef.current?.(ent?.platformRef?.buildingId ?? null);
          },
          onInteraction: (snap: InteractionSnapshot) => {
            if (cancelled) return;
            setPickable(snap.pickable);
            setBinding(snap.binding);
            setSelectedActive(snap.selectedActive);
            setPickEnabled(snap.interactionEnabled);
            setClickGeo(snap.clickGeo ?? null);
            setObjectGeo(snap.objectGeo ?? null);
            setGeoReady(!!snap.georeferenceReady);
          },
          onCalibrationPick: (world) => {
            const slot = pickingSlotRef.current;
            if (!slot) return;
            if (slot === "CHECK") {
              const others = CALIBRATION_SLOTS.map((id) => calDraftRef.current[id].world);
              const cap = captureControlWorld(world, others);
              if (!cap.ok) {
                setCalMessage(cap.error);
                return;
              }
              setCalMessage(null);
              setPickingSlot(null);
              setCheckDraft((prev) => ({ ...prev, world: cap.world }));
              return;
              return;
            }
            setCalDraft((prev) => {
              const others = CALIBRATION_SLOTS.filter((id) => id !== slot).map((id) => prev[id].world);
              const cap = captureControlWorld(world, others);
              if (!cap.ok) {
                setCalMessage(cap.error);
                return prev;
              }
              setCalMessage(null);
              setPickingSlot(null);
              return { ...prev, [slot]: { ...prev[slot], world: cap.world, pickedAt: new Date().toISOString() } };
            });
          },
          onInitError: (msg, error) => {
            if (!cancelled) captureFault(error ?? new Error(msg), "init");
          },
          onPerfStats: showDev
            ? (stats) => {
                if (!cancelled) setPerf(stats);
              }
            : undefined,
        });
        controllerRef.current = ctrl;
        void ctrl
          .mount(canvas)
          .then(() => {
            if (!cancelled && ctrl) {
              setLayers(ctrl.layerList?.() ?? []);
              const status = ctrl.georeferenceStatus?.() ?? "CALIBRATION_REQUIRED";
              setGeoStatus(status);
              if (status === "READY_CALIBRATED") setCalSaved(true);
              const raw = loadRawObservations();
              if (raw?.observations?.length) {
                setCalDraft(draftFromObservations(raw.observations));
                if (raw.check) setCheckDraft(checkFromObservation(raw.check));
              } else {
                const saved = loadAuthoredCalibration();
                if (saved?.controlPoints?.length) setCalDraft(draftFromControlPoints(saved.controlPoints));
              }
              ctrl.consumePendingGeoFocus?.();
            }
          })
          .catch((e) => {
            if (!cancelled) captureFault(e, "mount");
          });
      } catch (e) {
        captureFault(e, "construct");
      }
    };

    raf = window.requestAnimationFrame(start);
    timer = window.setTimeout(start, 32);

    let diagTimer: number | undefined;
    if (showDev) {
      diagTimer = window.setInterval(() => {
        if (controllerRef.current) setDiag(controllerRef.current.diagnostics());
      }, HUD_THROTTLE_MS);
    }
    let debugTimer: number | undefined;
    if (cityDebug) {
      debugTimer = window.setInterval(() => {
        const snap = controllerRef.current?.cityDebugSnapshot?.();
        if (snap) setDebugSnap(snap);
      }, 250);
    }
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(raf);
      window.clearTimeout(timer);
      if (diagTimer) window.clearInterval(diagTimer);
      if (debugTimer) window.clearInterval(debugTimer);
      ctrl?.dispose();
      if (controllerRef.current === ctrl) controllerRef.current = null;
    };
  }, [
    quality.maxConcurrentLoads,
    quality.maxActiveTiles,
    quality.profile,
    quality.pixelRatioCap,
    showDev,
    mountEpoch,
    cityDebug,
  ]);

  const openSelected = useCallback(() => {
    const route = binding?.route ?? resolvePlatformRoute(selectedId ? getCityEntity(selectedId) : undefined);
    if (route) onOpenRoute?.(route);
  }, [binding, selectedId, onOpenRoute]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (pickingSlotRef.current) {
        setPickingSlot(null);
        return;
      }
      controllerRef.current?.clearSelection();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    const ctrl = controllerRef.current;
    if (!ctrl) return;
    ctrl.setCalibrationPicking?.(calOpen && pickingSlot != null);
    const points = [
      ...CALIBRATION_SLOTS.flatMap((id) => {
        const w = calDraft[id].world;
        return w ? [{ id, world: w }] : [];
      }),
      ...(checkDraft.world ? [{ id: "CHECK" as const, world: checkDraft.world }] : []),
    ];
    ctrl.setCalibrationMarkers?.(points, calOpen);
  }, [calOpen, pickingSlot, calDraft, checkDraft]);

  useEffect(() => {
    const hasAny =
      CALIBRATION_SLOTS.some((id) => calDraft[id].world || calDraft[id].geo) || checkDraft.world || checkDraft.geo;
    if (!hasAny) return;
    const root = controllerRef.current?.modelRootTransform?.() ?? IDENTITY_MODEL_ROOT;
    saveRawObservations({
      modelRoot: root,
      observations: CALIBRATION_SLOTS.map((id) => ({
        id,
        world: calDraft[id].world,
        gps: calDraft[id].geo,
        pickedAt: calDraft[id].pickedAt,
        coordinateSpace: "world" as const,
      })),
      check:
        checkDraft.world || checkDraft.geo
          ? { id: "CHECK", world: checkDraft.world, gps: checkDraft.geo, pickedAt: null, coordinateSpace: "world" }
          : null,
    });
  }, [calDraft, checkDraft]);

  useEffect(() => {
    if (!calOpen || !pickingSlot) {
      setCursorWorld(null);
      return;
    }
    const timer = window.setInterval(() => {
      setCursorWorld(controllerRef.current?.hoverWorld?.() ?? null);
    }, 250);
    return () => window.clearInterval(timer);
  }, [calOpen, pickingSlot]);

  const cityInteractive = hud.boot === "INTERACTIVE" || hud.boot === "FILLING" || hud.ready;
  const activeDiag =
    hud.loadDiagnostics.find((d) => d.id === hud.loadingAssetId) ?? hud.loadDiagnostics[0];
  const pipelineOffenders = Array.isArray(perf?.pipeline?.worstOffenders) ? perf.pipeline.worstOffenders : [];
  const firstLoadWorst = Array.isArray(perf?.firstLoad?.worst10) ? perf.firstLoad.worst10 : [];
  const fogDensity = typeof perf?.environment?.fogDensity === "number" ? perf.environment.fogDensity : 0;

  return (
    <div className="ec-3d-shell" data-testid="odessa-3d-view" data-hud-total={hud.total} data-hud-boot={hud.boot} data-hud-queued={hud.queued} data-hud-loading={hud.loading} data-hud-failed={hud.failed}>
      <div className="ec-3d-toolbar flex flex-wrap items-center gap-2 p-2">
        <Badge tone="info">ODESSA 3D</Badge>
        {hud.ready ? (
          <Badge tone="success">
            ODESSA READY — {hud.active}/{hud.total}
          </Badge>
        ) : (
          <Badge tone={cityInteractive ? "success" : "warning"}>
            {hud.boot} · {hud.active}/{hud.total}
          </Badge>
        )}
        <Button
          size="sm"
          className="min-h-11"
          variant="ghost"
          onClick={() => {
            controllerRef.current?.resetCamera();
            setViewMode("3d");
          }}
          data-testid="odessa-home-view"
        >
          Общий вид
        </Button>
        <Button
          size="sm"
          className="min-h-11"
          variant={viewMode === "3d" ? "primary" : "ghost"}
          onClick={() => {
            controllerRef.current?.setCameraViewMode?.("3d");
            setViewMode("3d");
          }}
          data-testid="odessa-view-3d"
        >
          3D
        </Button>
        <Button
          size="sm"
          className="min-h-11"
          variant={viewMode === "2d" ? "primary" : "ghost"}
          onClick={() => {
            controllerRef.current?.setCameraViewMode?.("2d");
            setViewMode("2d");
          }}
          data-testid="odessa-view-2d"
        >
          2D
        </Button>
        <Button
          size="sm"
          className="min-h-11"
          variant={pickEnabled ? "primary" : "ghost"}
          onClick={() => {
            const next = !pickEnabled;
            setPickEnabled(next);
            controllerRef.current?.setInteractionEnabled(next);
          }}
          data-testid="odessa-pick-toggle"
        >
          Выбор объектов
        </Button>
        <Button
          size="sm"
          className="min-h-11"
          variant={calOpen ? "primary" : "ghost"}
          onClick={() => {
            const next = !calOpen;
            setCalOpen(next);
            if (!next) setPickingSlot(null);
            if (next) {
              const raw = loadRawObservations();
              if (raw?.observations?.length) {
                setCalDraft(draftFromObservations(raw.observations));
                if (raw.check) setCheckDraft(checkFromObservation(raw.check));
              } else {
                const saved = loadAuthoredCalibration();
                if (saved?.controlPoints?.length) setCalDraft(draftFromControlPoints(saved.controlPoints));
              }
            }
          }}
          data-testid="odessa-cal-toggle"
        >
          Геопривязка
        </Button>
        <Badge
          tone={
            geoStatus === "READY_CALIBRATED" || geoStatus === "READY_APPROXIMATE" || geoStatus === "READY_EXACT"
              ? "success"
              : geoStatus === "CALIBRATION_POOR" || geoStatus === "CALIBRATION_MODEL_MISMATCH"
                ? "warning"
                : "info"
          }
          data-testid="odessa-geo-status"
        >
          {geoStatus}
        </Badge>
        {pickable ? (
          <span data-testid="odessa-selected-badge">
            <Badge tone={binding?.status === "BOUND" ? "success" : "info"}>
              {binding?.label || pickable.meshName || pickable.assetId}
            </Badge>
          </span>
        ) : null}
        {showDev ? (
          <>
            <Button
              size="sm"
              className="min-h-11"
              variant={showTileBounds ? "primary" : "ghost"}
              onClick={() => {
                const next = !showTileBounds;
                setShowTileBounds(next);
                controllerRef.current?.setShowTileBounds(next);
              }}
            >
              Показать границы тайлов
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={showPerfPanel ? "primary" : "ghost"}
              onClick={() => setShowPerfPanel((v) => !v)}
              data-testid="odessa-perf-toggle"
            >
              Диагностика
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={showWaterDebug ? "primary" : "ghost"}
              onClick={() => {
                const next = !showWaterDebug;
                setShowWaterDebug(next);
                controllerRef.current?.setWaterDebug(next);
              }}
              data-testid="odessa-water-debug-toggle"
            >
              WATER DEBUG
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={showPickBounds ? "primary" : "ghost"}
              onClick={() => {
                const next = !showPickBounds;
                setShowPickBounds(next);
                controllerRef.current?.setShowSelectionBounds(next);
              }}
              data-testid="odessa-pick-bounds-toggle"
            >
              BOX3
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={showGeoGrid ? "primary" : "ghost"}
              onClick={() => {
                const next = !showGeoGrid;
                setShowGeoGrid(next);
                controllerRef.current?.setShowGeoGrid(next);
              }}
              data-testid="odessa-geo-grid-toggle"
            >
              GEO GRID
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={isolation.baseModelOnly ? "primary" : "ghost"}
              onClick={() => {
                const next = { ...isolation, baseModelOnly: !isolation.baseModelOnly };
                if (next.baseModelOnly) {
                  next.disableWater = true;
                  next.disableOverlays = true;
                }
                setIsolation(next);
                controllerRef.current?.setRenderIsolation(next);
              }}
              data-testid="odessa-iso-base-toggle"
            >
              Base model only
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={isolation.disableWater ? "primary" : "ghost"}
              onClick={() => {
                const next = { ...isolation, disableWater: !isolation.disableWater };
                setIsolation(next);
                controllerRef.current?.setRenderIsolation(next);
              }}
              data-testid="odessa-iso-water-toggle"
            >
              Disable water
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={isolation.disableOverlays ? "primary" : "ghost"}
              onClick={() => {
                const next = { ...isolation, disableOverlays: !isolation.disableOverlays };
                setIsolation(next);
                controllerRef.current?.setRenderIsolation(next);
              }}
              data-testid="odessa-iso-overlays-toggle"
            >
              Disable overlays
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={isolation.neutralMaterial ? "primary" : "ghost"}
              onClick={() => {
                const next = { ...isolation, neutralMaterial: !isolation.neutralMaterial };
                setIsolation(next);
                controllerRef.current?.setRenderIsolation(next);
              }}
              data-testid="odessa-iso-neutral-toggle"
            >
              Neutral material diagnostic
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={fogDisabled ? "primary" : "ghost"}
              onClick={() => {
                const next = !fogDisabled;
                setFogDisabled(next);
                controllerRef.current?.setFogEnabled(!next);
              }}
              data-testid="odessa-iso-fog-toggle"
            >
              Disable fog
            </Button>
            {(
              [
                ["sourceCityOnly", "SOURCE CITY ONLY"],
                ["environmentOff", "ENV OFF"],
                ["lightsNeutral", "NEUTRAL LIGHT"],
                ["wireframe", "WIREFRAME"],
                ["depthDebug", "DEPTH DEBUG"],
                ["transparentOff", "TRANSPARENT OFF"],
                ["showMeshBounds", "MESH BOUNDS"],
                ["hideBasePlane", "HIDE BASE PLANE"],
                ["tightClip", "TIGHT CLIP"],
                ["spikesOnly", "SPIKES ONLY"],
                ["hideSpikes", "HIDE SPIKES"],
                ["colorSpikesRed", "SPIKES RED"],
                ["componentColors", "COMP COLORS"],
                ["componentRepairOff", "ORIGINAL GEOM"],
              ] as const
            ).map(([key, label]) => (
              <Button
                key={key}
                size="sm"
                className="min-h-11"
                variant={debugView[key] ? "primary" : "ghost"}
                onClick={() => {
                  const next = { ...debugView, [key]: !debugView[key] };
                  setDebugView(next);
                  controllerRef.current?.setDebugView({ [key]: next[key] });
                }}
                data-testid={`odessa-dbg-${key}`}
              >
                {label}
              </Button>
            ))}
            <Button
              size="sm"
              className="min-h-11"
              variant={debugView.sideMode !== "original" ? "primary" : "ghost"}
              onClick={() => {
                const order = ["original", "front", "double"] as const;
                const sideMode = order[(order.indexOf(debugView.sideMode) + 1) % order.length];
                setDebugView({ ...debugView, sideMode });
                controllerRef.current?.setDebugView({ sideMode });
              }}
              data-testid="odessa-dbg-side"
            >
              SIDE: {debugView.sideMode.toUpperCase()}
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={recoveryMode !== "selective" ? "primary" : "ghost"}
              onClick={() => {
                const order = ["selective", "legacy", "off"] as const;
                const next = order[(order.indexOf(recoveryMode) + 1) % order.length];
                setRecoveryMode(next);
                controllerRef.current?.setVerticalRecoveryMode(next);
              }}
              data-testid="odessa-dbg-recovery-mode"
            >
              REC: {recoveryMode.toUpperCase()}
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant={activeOdessaPackage().id === "CURRENT_BROKEN" ? "primary" : "ghost"}
              onClick={() => {
                /* STEP 29.9 A/B: swap the whole asset package; a reload is
                 * required because geometry is already parsed and attached. */
                const next: OdessaPackageId =
                  activeOdessaPackage().id === "REBUILT_METRIC" ? "CURRENT_BROKEN" : "REBUILT_METRIC";
                storePackageId(next);
                window.location.reload();
              }}
              data-testid="odessa-dbg-package"
            >
              PKG: {activeOdessaPackage().id === "REBUILT_METRIC" ? "METRIC" : "BROKEN"}
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant="ghost"
              onClick={() => {
                const json = controllerRef.current?.exportSpikeReport(false);
                if (!json) return;
                const blob = new Blob([json], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `odessa_spike_report_${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              data-testid="odessa-dbg-spike-export"
            >
              EXPORT SPIKE JSON
            </Button>
            {(
              [
                ["ACTIVATE", "BISECT ON"],
                ["ALL", "ALL"],
                ["HALF_A", "HALF A"],
                ["HALF_B", "HALF B"],
                ["NEXT_SPLIT", "NEXT SPLIT"],
                ["RESET", "RESET"],
                ["DEACTIVATE", "BISECT OFF"],
              ] as const
            ).map(([action, label]) => (
              <Button
                key={action}
                size="sm"
                className="min-h-11"
                variant="ghost"
                onClick={() => {
                  const status = controllerRef.current?.bisect(action);
                  if (status) setBisect(status);
                }}
                data-testid={`odessa-bisect-${action}`}
              >
                {label}
              </Button>
            ))}
            {bisect?.active ? (
              <Badge data-testid="odessa-bisect-status">
                bisect {bisect.showing} · {bisect.currentCount}/{bisect.totalMeshes} · depth {bisect.depth} ·{" "}
                {bisect.path}
                {bisect.currentNames.length ? ` · ${bisect.currentNames.join(", ")}` : ""}
              </Badge>
            ) : null}
          </>
        ) : null}
        {selectedId && binding?.status === "BOUND" ? (
          <>
            <Badge>{getCityEntity(selectedId)?.label || selectedId}</Badge>
            <Button size="sm" className="min-h-11" onClick={openSelected}>
              Открыть карточку
            </Button>
          </>
        ) : null}
      </div>

      {showLoaderDiag ? (
        <div className="ec-3d-loader-diag px-2 pb-2 text-xs" data-testid="odessa-loader-diag">
          {activeDiag ? (
            <p>
              <strong>{activeDiag.id}</strong> · {activeDiag.phase} · {activeDiag.url}
              {activeDiag.bytesLoaded
                ? ` · ${(activeDiag.bytesLoaded / 1024 / 1024).toFixed(2)} / ${((activeDiag.bytesTotal ?? activeDiag.bytesLoaded) / 1024 / 1024).toFixed(2)} MB`
                : ""}
              {activeDiag.meshCount ? ` · meshes ${activeDiag.meshCount}` : ""}
            </p>
          ) : null}
          {hud.firstError ? <p className="text-[var(--eds-danger)]">FAILED: {hud.firstError}</p> : null}
        </div>
      ) : null}

      <div className="ec-3d-layers flex flex-wrap gap-1 px-2 pb-2" role="group" aria-label="Слои 3D">
        {layers.map((l) => (
          <Button
            key={l.id}
            size="sm"
            variant={l.visible ? "primary" : "ghost"}
            className="min-h-11"
            onClick={() => {
              controllerRef.current?.toggleLayer(l.id);
              setLayers(controllerRef.current?.layerList() ?? []);
            }}
          >
            {l.label}
          </Button>
        ))}
      </div>
      <div className="ec-3d-canvas-wrap relative min-h-[420px] w-full overflow-hidden rounded-lg border border-[var(--ew-border)]">
        <canvas
          ref={canvasRef}
          className="h-full min-h-[420px] w-full touch-none"
          data-testid="odessa-3d-canvas"
        />
        {cityDebug ? (
          <aside className="ec-3d-city-debug" data-testid="odessa-city-debug">
            <p>cityDebug</p>
            <dl>
              <dt>FPS</dt>
              <dd>{debugSnap.fps.toFixed(1)}</dd>
              <dt>camera</dt>
              <dd>
                {debugSnap.camera.x.toFixed(1)} {debugSnap.camera.y.toFixed(1)} {debugSnap.camera.z.toFixed(1)}
              </dd>
              <dt>target</dt>
              <dd>
                {debugSnap.target.x.toFixed(1)} {debugSnap.target.y.toFixed(1)} {debugSnap.target.z.toFixed(1)}
              </dd>
              <dt>hover</dt>
              <dd>{debugSnap.hovered ?? "—"}</dd>
              <dt>select</dt>
              <dd>{debugSnap.selected ?? "—"}</dd>
              <dt>hover xyz</dt>
              <dd>
                {debugSnap.hoveredCoords
                  ? `${debugSnap.hoveredCoords.x.toFixed(1)} ${debugSnap.hoveredCoords.y.toFixed(1)} ${debugSnap.hoveredCoords.z.toFixed(1)}`
                  : "—"}
              </dd>
              <dt>select xyz</dt>
              <dd>
                {debugSnap.selectedCoords
                  ? `${debugSnap.selectedCoords.x.toFixed(1)} ${debugSnap.selectedCoords.y.toFixed(1)} ${debugSnap.selectedCoords.z.toFixed(1)}`
                  : "—"}
              </dd>
              <dt>mode</dt>
              <dd>{debugSnap.viewMode.toUpperCase()}</dd>
            </dl>
            {debugSnap.geo ? (
              <div className="mt-2" data-testid="odessa-geo-debug">
                <p>GEOREFERENCE</p>
                <dl>
                  <dt>Status</dt>
                  <dd>{debugSnap.geo.status}</dd>
                  <dt>Control points</dt>
                  <dd>{debugSnap.geo.controlPoints}</dd>
                  <dt>Yaw</dt>
                  <dd>{debugSnap.geo.yaw ?? "—"}</dd>
                  <dt>Scale</dt>
                  <dd>{debugSnap.geo.scale ?? "—"}</dd>
                  <dt>Axis</dt>
                  <dd>{debugSnap.geo.axis}</dd>
                  <dt>Mean error</dt>
                  <dd>{debugSnap.geo.meanError ?? "—"}</dd>
                  <dt>Max error</dt>
                  <dd>{debugSnap.geo.maxError ?? "—"}</dd>
                  <dt>Camera lat/lon</dt>
                  <dd>
                    {debugSnap.geo.cameraLat != null
                      ? `${debugSnap.geo.cameraLat.toFixed(6)}, ${debugSnap.geo.cameraLon?.toFixed(6)}`
                      : "—"}
                  </dd>
                  <dt>Selected lat/lon</dt>
                  <dd>
                    {debugSnap.geo.selectedLat != null
                      ? `${debugSnap.geo.selectedLat.toFixed(6)}, ${debugSnap.geo.selectedLon?.toFixed(6)}`
                      : "—"}
                  </dd>
                </dl>
                <button
                  type="button"
                  className="pointer-events-auto mt-1 underline"
                  data-testid="odessa-copy-geo-debug"
                  onClick={() => {
                    const text = [
                      controllerRef.current?.copyGeoDebug?.() ?? formatCityGeoDebug(debugSnap),
                      formatCalibrationSessionDebug(calDraft, checkDraft),
                    ].join("\n");
                    if (navigator.clipboard?.writeText) void navigator.clipboard.writeText(text);
                  }}
                >
                  COPY GEO DEBUG
                </button>
              </div>
            ) : null}
            <pre className="mt-2 max-h-56 overflow-auto text-[10px] leading-snug" data-testid="odessa-cal-session-debug">
              {formatCalibrationSessionDebug(calDraft, checkDraft)}
            </pre>
          </aside>
        ) : null}
        {calOpen && pickingSlot ? (
          <div className="pointer-events-none absolute inset-x-0 top-0 z-[4] bg-black/50 px-3 py-2 text-center text-sm text-white">
            GEO PICK: кликните точку {pickingSlot} на модели (точный intersection.point)
          </div>
        ) : null}
        <CalibrationWizard
          key={wizardKey}
          open={calOpen}
          draft={calDraft}
          check={checkDraft}
          pickingSlot={pickingSlot}
          georeferenceStatus={geoStatus}
          modelMismatch={geoStatus === "CALIBRATION_MODEL_MISMATCH"}
          message={calMessage}
          savedReady={calSaved || geoStatus === "READY_CALIBRATED"}
          cursorWorld={cursorWorld}
          modelRoot={controllerRef.current?.modelRootTransform?.() ?? IDENTITY_MODEL_ROOT}
          pickCoordinateSpace={PICK_COORDINATE_SPACE}
          onClose={() => {
            setCalOpen(false);
            setPickingSlot(null);
            controllerRef.current?.setCalibrationPicking(false);
            controllerRef.current?.setCalibrationMarkers([], false);
          }}
          onPick={(slot) => {
            setPickingSlot(slot);
            setCalMessage(null);
          }}
          onDraftChange={setCalDraft}
          onCheckChange={setCheckDraft}
          onCopyDiagnostic={() => {
            const text = formatGeoreferenceDiagnosticV3({
              draft: calDraft,
              check: checkDraft,
              modelRoot: controllerRef.current?.modelRootTransform?.() ?? IDENTITY_MODEL_ROOT,
              pickCoordinateSpace: PICK_COORDINATE_SPACE,
            });
            if (navigator.clipboard?.writeText) void navigator.clipboard.writeText(text);
          }}
          onExportJson={() => {
            const root = controllerRef.current?.modelRootTransform?.() ?? IDENTITY_MODEL_ROOT;
            const evaled = evaluateCalibrationDraft(calDraft);
            const fingerprint = controllerRef.current?.modelFingerprint() ?? "odessa:unknown";
            const fromDraft =
              evaled.final &&
              buildAuthoredRecord({
                solve: evaled.final,
                controlPoints: evaled.complete,
                modelFingerprint: fingerprint,
                independentResidualMeters: evaled.independentResidualMeters,
              });
            const record = fromDraft ?? loadAuthoredCalibration();
            const payload = {
              schemaVersion: 3,
              coordinateSpace: PICK_COORDINATE_SPACE,
              modelRoot: root,
              observations: CALIBRATION_SLOTS.map((id) => ({
                id,
                world: calDraft[id].world,
                gps: calDraft[id].geo,
                pickedAt: calDraft[id].pickedAt,
                coordinateSpace: "world",
              })),
              check: {
                world: checkDraft.world,
                gps: checkDraft.geo,
              },
              diagnostic: formatGeoreferenceDiagnosticV3({
                draft: calDraft,
                check: checkDraft,
                modelRoot: root,
                pickCoordinateSpace: PICK_COORDINATE_SPACE,
              }),
              authored: record,
            };
            const text = JSON.stringify(payload, null, 2);
            const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
            const a = document.createElement("a");
            a.href = url;
            a.download = "odessa-georeference-v3.json";
            a.click();
            URL.revokeObjectURL(url);
          }}
          onSave={() => {
            const evaled = evaluateCalibrationDraft(calDraft);
            const fingerprint = controllerRef.current?.modelFingerprint();
            if (!evaled.final || !fingerprint) {
              setCalMessage("cannot_save");
              return;
            }
            const record = buildAuthoredRecord({
              solve: evaled.final,
              controlPoints: evaled.complete,
              modelFingerprint: fingerprint,
              independentResidualMeters: evaled.independentResidualMeters,
              modelRoot: controllerRef.current?.modelRootTransform?.() ?? IDENTITY_MODEL_ROOT,
            });
            if (!record) {
              setCalMessage("quality_not_acceptable");
              return;
            }
            saveAuthoredCalibration(record);
            controllerRef.current?.reloadGeoreference();
            setGeoStatus(controllerRef.current?.georeferenceStatus() ?? "READY_CALIBRATED");
            setCalMessage("saved");
            setCalSaved(true);
            setPickingSlot(null);
          }}
          onReset={() => {
            resetAuthoredCalibration();
            setCalDraft(emptyCalibrationDraft());
            setCheckDraft(emptyCheckDraft());
            controllerRef.current?.reloadGeoreference();
            setGeoStatus(controllerRef.current?.georeferenceStatus() ?? "CALIBRATION_REQUIRED");
            setCalMessage("reset");
            setCalSaved(false);
            setPickingSlot(null);
            setWizardKey((k) => k + 1);
          }}
        />
        {cityDebug ? (
          <CalibrationPanel
            open={calOpen}
            draft={calDraft}
            pickingSlot={pickingSlot === "CHECK" ? null : pickingSlot}
            georeferenceStatus={geoStatus}
            modelMismatch={geoStatus === "CALIBRATION_MODEL_MISMATCH"}
            message={calMessage}
            onClose={() => {
              setCalOpen(false);
              setPickingSlot(null);
              controllerRef.current?.setCalibrationPicking(false);
              controllerRef.current?.setCalibrationMarkers([], false);
            }}
            onAddPoint={(slot) => {
              setPickingSlot(slot);
              setCalMessage(null);
            }}
            onDraftChange={setCalDraft}
            onSave={() => {
              const evaled = evaluateCalibrationDraft(calDraft);
              const fingerprint = controllerRef.current?.modelFingerprint();
              if (!evaled.final || !fingerprint) {
                setCalMessage("cannot_save");
                return;
              }
              const record = buildAuthoredRecord({
                solve: evaled.final,
                controlPoints: evaled.complete,
                modelFingerprint: fingerprint,
                independentResidualMeters: evaled.independentResidualMeters,
              });
              if (!record) {
                setCalMessage("quality_not_acceptable");
                return;
              }
              saveAuthoredCalibration(record);
              controllerRef.current?.reloadGeoreference();
              setGeoStatus(controllerRef.current?.georeferenceStatus() ?? "READY_CALIBRATED");
              setCalMessage("saved");
              setCalSaved(true);
              setPickingSlot(null);
            }}
            onSavePoor={() => {
              const evaled = evaluateCalibrationDraft(calDraft);
              const fingerprint = controllerRef.current?.modelFingerprint();
              if (!evaled.final || !fingerprint) return;
              const record = buildAuthoredRecord({
                solve: evaled.final,
                controlPoints: evaled.complete,
                modelFingerprint: fingerprint,
                independentResidualMeters: evaled.independentResidualMeters,
                allowPoor: true,
              });
              if (!record) return;
              saveAuthoredCalibration(record);
              controllerRef.current?.reloadGeoreference();
              setGeoStatus(controllerRef.current?.georeferenceStatus() ?? "CALIBRATION_POOR");
              setCalMessage("saved_poor");
            }}
            onReset={() => {
              resetAuthoredCalibration();
              setCalDraft(emptyCalibrationDraft());
              setCheckDraft(emptyCheckDraft());
              controllerRef.current?.reloadGeoreference();
              setGeoStatus(controllerRef.current?.georeferenceStatus() ?? "CALIBRATION_REQUIRED");
              setCalMessage("reset");
              setCalSaved(false);
              setPickingSlot(null);
              setWizardKey((k) => k + 1);
            }}
            onExport={() => {
            const evaled = evaluateCalibrationDraft(calDraft);
            const fingerprint = controllerRef.current?.modelFingerprint() ?? "odessa:unknown";
            const fromDraft =
              evaled.final &&
              buildAuthoredRecord({
                solve: evaled.final,
                controlPoints: evaled.complete,
                modelFingerprint: fingerprint,
                independentResidualMeters: evaled.independentResidualMeters,
              });
            const record = fromDraft ?? loadAuthoredCalibration();
            if (!record) {
              setCalMessage("nothing_to_export");
              return;
            }
            const text = exportAuthoredCalibrationJson(record);
            const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
            const a = document.createElement("a");
            a.href = url;
            a.download = "odessa-calibration.json";
            a.click();
            URL.revokeObjectURL(url);
          }}
          onImportText={(text) => {
            const parsed = importAuthoredCalibrationJson(text);
            if (!parsed.ok) {
              setCalMessage(parsed.error);
              return;
            }
            const current = controllerRef.current?.modelFingerprint();
            setCalDraft(draftFromControlPoints(parsed.record.controlPoints));
            if (current && parsed.record.modelFingerprint !== current) {
              setCalMessage("CALIBRATION_MODEL_MISMATCH");
              setGeoStatus("CALIBRATION_MODEL_MISMATCH");
              return;
            }
            saveAuthoredCalibration(parsed.record);
            controllerRef.current?.reloadGeoreference();
            setGeoStatus(controllerRef.current?.georeferenceStatus() ?? "READY_CALIBRATED");
            setCalMessage("imported");
          }}
          onCopyPoint={() => undefined}
          onCameraPreset={(kind) => {
            controllerRef.current?.calibrationCameraPreset(kind, {
              A: calDraft.A.world,
              B: calDraft.B.world,
              C: calDraft.C.world,
            });
          }}
        />
        ) : null}
        {pickable ? (
          <OdessaObjectPanel
            pickable={pickable}
            binding={binding}
            selectedActive={selectedActive}
            showDev={showDev}
            clickGeo={clickGeo}
            objectGeo={objectGeo}
            georeferenceReady={geoReady}
            onOpen={openSelected}
            onFocus={() => controllerRef.current?.focusSelected()}
            onClear={() => controllerRef.current?.clearSelection()}
            onCopyCoords={() => {
              const text = controllerRef.current?.copyClickCoordinates();
              if (text && navigator.clipboard?.writeText) void navigator.clipboard.writeText(text);
            }}
            onShowIn2d={() => {
              if (clickGeo) geoSelectionBridge.requestShowIn2d(clickGeo);
              else if (objectGeo) geoSelectionBridge.requestShowIn2d(objectGeo);
            }}
          />
        ) : null}
        {initFault ? (
          <div className="absolute inset-0 overflow-auto bg-black/70">
            <OdessaRuntimeFaultPanel
              phase={initFault.phase}
              errorName={initFault.name}
              errorMessage={initFault.message}
              stack={initFault.stack}
              manifest={initFault.manifest}
              controller={initFault.controller}
              webgl={initFault.webgl}
              progressJson={JSON.stringify(hud)}
              onRetry={() => {
                setInitFault(null);
                setMountEpoch((n) => n + 1);
              }}
            />
          </div>
        ) : null}
        {!hud.ready ? (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-black/40 p-2">
            <div className="h-2 overflow-hidden rounded bg-white/20">
              <div className="h-full bg-[var(--eds-primary)] transition-all" style={{ width: `${hud.percent}%` }} />
            </div>
          </div>
        ) : null}
      </div>
      {showDev && showPerfPanel && perf ? (
        <Card title="3D Performance" className="mt-2" data-testid="odessa-perf-panel">
          {diag?.interaction ? (
            <div className="mb-3 border-b border-[var(--ew-border)] pb-2 text-xs" data-testid="odessa-interaction-diag">
              <p className="mb-1 opacity-70">INTERACTION</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                <div>
                  <dt className="opacity-70">pickables</dt>
                  <dd>{diag.interaction.pickables}</dd>
                </div>
                <div>
                  <dt className="opacity-70">hovered</dt>
                  <dd>{diag.interaction.hovered ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">selected</dt>
                  <dd>{diag.interaction.selected ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">raycasts/sec</dt>
                  <dd>{diag.interaction.raycastsPerSec}</dd>
                </div>
                <div>
                  <dt className="opacity-70">lastRaycastMs</dt>
                  <dd>{diag.interaction.lastRaycastMs}</dd>
                </div>
                <div>
                  <dt className="opacity-70">candidates</dt>
                  <dd>{diag.interaction.candidates}</dd>
                </div>
                <div>
                  <dt className="opacity-70">hits</dt>
                  <dd>{diag.interaction.hits}</dd>
                </div>
                <div>
                  <dt className="opacity-70">boundEntities</dt>
                  <dd>{diag.interaction.boundEntities}</dd>
                </div>
                <div>
                  <dt className="opacity-70">unboundEntities</dt>
                  <dd>{diag.interaction.unboundEntities}</dd>
                </div>
                <div>
                  <dt className="opacity-70">registrySize</dt>
                  <dd>{diag.interaction.registrySize}</dd>
                </div>
                <div>
                  <dt className="opacity-70">materialClones</dt>
                  <dd>{diag.interaction.materialClones}</dd>
                </div>
                <div>
                  <dt className="opacity-70">interactionEnabled</dt>
                  <dd>{diag.interaction.interactionEnabled ? "on" : "off"}</dd>
                </div>
              </dl>
            </div>
          ) : null}
          {diag?.georeference ? (
            <div className="mb-3 border-b border-[var(--ew-border)] pb-2 text-xs" data-testid="odessa-georeference-diag">
              <p className="mb-1 opacity-70">GEOREFERENCE</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                <div>
                  <dt className="opacity-70">status</dt>
                  <dd>{diag.georeference.status}</dd>
                </div>
                <div>
                  <dt className="opacity-70">source</dt>
                  <dd>{diag.georeference.source}</dd>
                </div>
                <div>
                  <dt className="opacity-70">confidence</dt>
                  <dd>{diag.georeference.confidence}</dd>
                </div>
                <div>
                  <dt className="opacity-70">origin lat</dt>
                  <dd>{diag.georeference.originLat ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">origin lon</dt>
                  <dd>{diag.georeference.originLon ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">world origin</dt>
                  <dd>
                    {diag.georeference.worldOrigin
                      ? `${diag.georeference.worldOrigin.x.toFixed(1)}, ${diag.georeference.worldOrigin.y.toFixed(1)}, ${diag.georeference.worldOrigin.z.toFixed(1)}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">meters/world unit</dt>
                  <dd>{diag.georeference.metersPerWorldUnit ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">rotation</dt>
                  <dd>{diag.georeference.rotation ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">axis mapping</dt>
                  <dd>{diag.georeference.axisMapping}</dd>
                </div>
                <div>
                  <dt className="opacity-70">control points</dt>
                  <dd>{diag.georeference.controlPoints}</dd>
                </div>
                <div>
                  <dt className="opacity-70">mean error</dt>
                  <dd>{diag.georeference.meanError ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">max error</dt>
                  <dd>{diag.georeference.maxError ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">model geo bounds</dt>
                  <dd>
                    {diag.georeference.modelGeoBounds
                      ? `N${diag.georeference.modelGeoBounds.north.toFixed(5)} S${diag.georeference.modelGeoBounds.south.toFixed(5)} E${diag.georeference.modelGeoBounds.east.toFixed(5)} W${diag.georeference.modelGeoBounds.west.toFixed(5)}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">anchors</dt>
                  <dd>{diag.georeference.anchors}</dd>
                </div>
                <div>
                  <dt className="opacity-70">in bounds</dt>
                  <dd>{diag.georeference.inBounds}</dd>
                </div>
                <div>
                  <dt className="opacity-70">out of bounds</dt>
                  <dd>{diag.georeference.outOfBounds}</dd>
                </div>
                <div>
                  <dt className="opacity-70">selected world</dt>
                  <dd>
                    {diag.georeference.selectedWorld
                      ? `${diag.georeference.selectedWorld.x.toFixed(1)}, ${diag.georeference.selectedWorld.y.toFixed(1)}, ${diag.georeference.selectedWorld.z.toFixed(1)}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">selected geo</dt>
                  <dd>
                    {diag.georeference.selectedGeo
                      ? `${diag.georeference.selectedGeo.lat.toFixed(6)}, ${diag.georeference.selectedGeo.lon.toFixed(6)}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">camera geo</dt>
                  <dd>
                    {diag.georeference.cameraGeo
                      ? `${diag.georeference.cameraGeo.lat.toFixed(6)}, ${diag.georeference.cameraGeo.lon.toFixed(6)}`
                      : "—"}
                  </dd>
                </div>
              </dl>
              {diag.georeference.reasons?.length ? (
                <p className="mt-2 opacity-70">{diag.georeference.reasons.join(" · ")}</p>
              ) : null}
            </div>
          ) : null}
          {perf.quality ? (
            <div className="mb-3 border-b border-[var(--ew-border)] pb-2 text-xs" data-testid="odessa-quality-diag">
              <p className="mb-1 opacity-70">QUALITY</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                <div>
                  <dt className="opacity-70">mode</dt>
                  <dd>{perf.quality.mode}</dd>
                </div>
                <div>
                  <dt className="opacity-70">pixelRatio</dt>
                  <dd>{perf.quality.pixelRatio}</dd>
                </div>
                <div>
                  <dt className="opacity-70">antialias</dt>
                  <dd>{perf.quality.antialias ? "on" : "off"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">anisotropy</dt>
                  <dd>{perf.quality.anisotropy}</dd>
                </div>
                <div>
                  <dt className="opacity-70">FPS</dt>
                  <dd>{perf.quality.fps}</dd>
                </div>
                <div>
                  <dt className="opacity-70">interactionState</dt>
                  <dd>{perf.quality.interactionState}</dd>
                </div>
                <div>
                  <dt className="opacity-70">visibleAssets</dt>
                  <dd>{perf.quality.visibleAssets}</dd>
                </div>
                <div>
                  <dt className="opacity-70">hiddenAssets</dt>
                  <dd>{perf.quality.hiddenAssets}</dd>
                </div>
                <div>
                  <dt className="opacity-70">LOD transitions/sec</dt>
                  <dd>{perf.quality.lodTransitionsPerSec}</dd>
                </div>
                <div>
                  <dt className="opacity-70">triangles</dt>
                  <dd>{perf.quality.triangles}</dd>
                </div>
                <div>
                  <dt className="opacity-70">drawCalls</dt>
                  <dd>{perf.quality.drawCalls}</dd>
                </div>
              </dl>
            </div>
          ) : null}
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-3">
            <div>
              <dt className="opacity-70">FPS</dt>
              <dd>{hud.fps}</dd>
            </div>
            <div>
              <dt className="opacity-70">FRAME MS</dt>
              <dd>{perf.frameMs}</dd>
            </div>
            <div>
              <dt className="opacity-70">DRAW CALLS</dt>
              <dd>{perf.drawCalls}</dd>
            </div>
            <div>
              <dt className="opacity-70">TRIANGLES</dt>
              <dd>{perf.triangles}</dd>
            </div>
            <div>
              <dt className="opacity-70">POINTS</dt>
              <dd>{perf.points}</dd>
            </div>
            <div>
              <dt className="opacity-70">LINES</dt>
              <dd>{perf.lines}</dd>
            </div>
            <div>
              <dt className="opacity-70">VISIBLE OBJECTS</dt>
              <dd>{perf.visibleObjects}</dd>
            </div>
            <div>
              <dt className="opacity-70">RUNTIME</dt>
              <dd data-testid="odessa-runtime-mode">{perf.runtimeMode ?? "IDLE"}</dd>
            </div>
            <div>
              <dt className="opacity-70">LOADED GLBS</dt>
              <dd>{perf.loadedGlbs}</dd>
            </div>
            <div>
              <dt className="opacity-70">VISIBLE GLBS</dt>
              <dd>{perf.visibleGlbs ?? "—"}</dd>
            </div>
            <div>
              <dt className="opacity-70">QUEUED</dt>
              <dd>{perf.queuedAssets ?? "—"}</dd>
            </div>
            <div>
              <dt className="opacity-70">ACTIVE TILES</dt>
              <dd>{perf.activeTiles ?? "—"}</dd>
            </div>
            <div>
              <dt className="opacity-70">GEOMETRIES</dt>
              <dd>{perf.geometries ?? "—"}</dd>
            </div>
            <div>
              <dt className="opacity-70">TEXTURES</dt>
              <dd>{perf.textures ?? "—"}</dd>
            </div>
            <div>
              <dt className="opacity-70">CAMERA DISTANCE</dt>
              <dd>{perf.cameraDistance}</dd>
            </div>
            <div>
              <dt className="opacity-70">PIXEL RATIO</dt>
              <dd>{perf.pixelRatio}</dd>
            </div>
            <div>
              <dt className="opacity-70">ADAPTIVE</dt>
              <dd>{perf.adaptiveTier}</dd>
            </div>
            <div>
              <dt className="opacity-70">STREAM PAUSED</dt>
              <dd>{perf.streamingPaused ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt className="opacity-70">BOOT</dt>
              <dd data-testid="odessa-boot-state">{perf.bootState ?? hud.boot}</dd>
            </div>
            <div>
              <dt className="opacity-70">DOWNLOADED</dt>
              <dd>
                {hud.downloaded}/{hud.total}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">PARSED</dt>
              <dd>
                {hud.parsed}/{hud.total}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">ACTIVE</dt>
              <dd>
                {hud.active}/{hud.total}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">MB DOWNLOADED</dt>
              <dd>
                {hud.mb} / {hud.totalMb}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">CURRENT ASSET</dt>
              <dd>{hud.currentAssetId ?? "—"}</dd>
            </div>
          </dl>
          {perf.firstLoad ? (
            <div className="mt-3 border-t border-[var(--ew-border)] pt-2 text-xs" data-testid="odessa-first-load-kpis">
              <p className="mb-1 opacity-70">First-load KPIs (ms)</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                <div>
                  <dt className="opacity-70">MANIFEST</dt>
                  <dd>{fmtMs(perf.firstLoad.timeToManifest)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">FIRST PARSE</dt>
                  <dd>{fmtMs(perf.firstLoad.timeToFirstParse)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">FIRST GEOMETRY</dt>
                  <dd>{fmtMs(perf.firstLoad.timeToFirstGeometry)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">FIRST RENDER</dt>
                  <dd>{fmtMs(perf.firstLoad.timeToFirstRender)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">INTERACTIVE</dt>
                  <dd>{fmtMs(perf.firstLoad.timeToInteractive)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">50% ACTIVE</dt>
                  <dd>{fmtMs(perf.firstLoad.timeTo50PercentActive)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">READY</dt>
                  <dd>{fmtMs(perf.firstLoad.timeToReady)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">TOTAL PARSE</dt>
                  <dd>{perf.firstLoad.totalParseMs}</dd>
                </div>
                <div>
                  <dt className="opacity-70">AVG PARSE</dt>
                  <dd>{perf.firstLoad.averageParseMs}</dd>
                </div>
                <div>
                  <dt className="opacity-70">LONG TASKS</dt>
                  <dd>
                    {perf.firstLoad.longTaskCount}
                    {perf.firstLoad.longTasks50 != null
                      ? ` (50+:${perf.firstLoad.longTasks50} 100+:${perf.firstLoad.longTasks100 ?? 0} 250+:${perf.firstLoad.longTasks250 ?? 0} 500+:${perf.firstLoad.longTasks500 ?? 0})`
                      : ""}
                  </dd>
                </div>
              </dl>
              {firstLoadWorst.length ? (
                <ol className="mt-2 list-decimal pl-4">
                  {firstLoadWorst.map((row) => (
                    <li key={row.id}>
                      {row.id} · {row.parseMs} ms · {row.sizeMb} MB · {row.triangleCount} tris
                    </li>
                  ))}
                </ol>
              ) : null}
            </div>
          ) : null}
          {perf.environment ? (
            <div className="mt-3 border-t border-[var(--ew-border)] pt-2 text-xs" data-testid="odessa-environment-diag">
              <p className="mb-1 opacity-70">ENVIRONMENT</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                <div>
                  <dt className="opacity-70">PRESET</dt>
                  <dd>{perf.environment.preset}</dd>
                </div>
                <div>
                  <dt className="opacity-70">SUN ELEVATION</dt>
                  <dd>{perf.environment.sunElevation}°</dd>
                </div>
                <div>
                  <dt className="opacity-70">SUN AZIMUTH</dt>
                  <dd>{perf.environment.sunAzimuth}°</dd>
                </div>
                <div>
                  <dt className="opacity-70">SUN INTENSITY</dt>
                  <dd>{perf.environment.sunIntensity ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">FOG DENSITY</dt>
                  <dd>{fogDensity.toExponential(2)}</dd>
                </div>
                <div>
                  <dt className="opacity-70">FOG COLOR</dt>
                  <dd>{perf.environment.fogColor ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">EXPOSURE</dt>
                  <dd>{perf.environment.exposure}</dd>
                </div>
                <div>
                  <dt className="opacity-70">WATER MODE</dt>
                  <dd>{perf.environment.waterMode}</dd>
                </div>
                <div>
                  <dt className="opacity-70">SKY</dt>
                  <dd>{perf.environment.skyEnabled ? "on" : "off"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">ENV QUALITY</dt>
                  <dd>{perf.environment.environmentQuality}</dd>
                </div>
                <div>
                  <dt className="opacity-70">CLASSIFIED</dt>
                  <dd>{perf.environment.classifiedMaterials ?? "—"}</dd>
                </div>
                <div>
                  <dt className="opacity-70">NORMALIZED</dt>
                  <dd>{perf.environment.normalizedMaterials ?? 0}</dd>
                </div>
                <div>
                  <dt className="opacity-70">TEXTURED SKIPPED</dt>
                  <dd>{perf.environment.texturedMaterialsSkipped ?? 0}</dd>
                </div>
                <div>
                  <dt className="opacity-70">BUILDING VARIATION</dt>
                  <dd>{perf.environment.buildingVariationCount ?? 0}</dd>
                </div>
              </dl>
            </div>
          ) : null}
          {perf.pipeline ? (
            <div className="mt-3 border-t border-[var(--ew-border)] pt-2 text-xs" data-testid="odessa-glb-pipeline">
              <p className="mb-1 opacity-70">GLB PIPELINE</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                <div>
                  <dt className="opacity-70">FETCHING</dt>
                  <dd>
                    {perf.pipeline.fetching} · {perf.pipeline.fetchingMb} MB
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">WAITING_PARSE</dt>
                  <dd>
                    {perf.pipeline.waitingParse} · {perf.pipeline.waitingParseMb} MB
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">PARSING</dt>
                  <dd>
                    {perf.pipeline.parsing} · {perf.pipeline.parsingMb} MB
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">PARSED</dt>
                  <dd>{perf.pipeline.parsed}</dd>
                </div>
                <div>
                  <dt className="opacity-70">WAITING_ACTIVATION</dt>
                  <dd>{perf.pipeline.waitingActivation}</dd>
                </div>
                <div>
                  <dt className="opacity-70">ACTIVE / HIDDEN / FAILED</dt>
                  <dd>
                    {perf.pipeline.active} / {perf.pipeline.hidden} / {perf.pipeline.failed}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">CURRENT PARSE</dt>
                  <dd>
                    {perf.pipeline.currentParseId ?? "—"}
                    {perf.pipeline.currentParseId
                      ? ` · ${perf.pipeline.currentParseSizeMb} MB · ${Math.round(perf.pipeline.currentParseElapsedMs)} ms`
                      : ""}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">LAST / AVG / WORST PARSE</dt>
                  <dd>
                    {perf.pipeline.lastParseMs} / {perf.pipeline.averageParseMs} / {perf.pipeline.worstParseMs}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">LONG TASKS 50/100/250/500</dt>
                  <dd>
                    {perf.pipeline.longTasks50} / {perf.pipeline.longTasks100} / {perf.pipeline.longTasks250} /{" "}
                    {perf.pipeline.longTasks500}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">QUEUES F/P/A</dt>
                  <dd>
                    {perf.pipeline.fetchQueue} / {perf.pipeline.parseQueue} / {perf.pipeline.activationQueue}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">CONCURRENCY F/P</dt>
                  <dd>
                    {perf.pipeline.fetchConcurrent} / {perf.pipeline.parseConcurrent}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">BACKPRESSURE</dt>
                  <dd>{perf.pipeline.backpressure ? "yes" : "no"}</dd>
                </div>
              </dl>
              {pipelineOffenders.length ? (
                <ol className="mt-2 list-decimal pl-4">
                  {pipelineOffenders.map((row) => (
                    <li key={row.id}>
                      {row.id} · {row.parseMs} ms · {row.sizeMb} MB · {row.triangleCount} tris
                    </li>
                  ))}
                </ol>
              ) : null}
            </div>
          ) : null}
          {perf.lod ? (
            <div className="mt-3 border-t border-[var(--ew-border)] pt-2 text-xs" data-testid="odessa-lod-diag">
              <p className="mb-1 opacity-70">LOD / VISIBILITY</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
                <div>
                  <dt className="opacity-70">NEAR / MID / FAR / CULL</dt>
                  <dd>
                    {perf.lod.near} / {perf.lod.mid} / {perf.lod.far} / {perf.lod.cull}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">VISIBLE / HIDDEN</dt>
                  <dd>
                    {perf.lod.visible} / {perf.lod.hidden}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">SEA / TARGET PROTECTED</dt>
                  <dd>
                    {perf.lod.protectedSea} / {perf.lod.protectedTarget}
                  </dd>
                </div>
                <div>
                  <dt className="opacity-70">ACTIVE TRIS</dt>
                  <dd>{perf.lod.activeTriangles}</dd>
                </div>
                <div>
                  <dt className="opacity-70">HIDDEN TRIS</dt>
                  <dd>{perf.lod.hiddenTriangles}</dd>
                </div>
                <div>
                  <dt className="opacity-70">PRIORITY MS</dt>
                  <dd>{perf.lod.priorityMs}</dd>
                </div>
                <div>
                  <dt className="opacity-70">BOUNDS MS</dt>
                  <dd>{perf.lod.boundsMs}</dd>
                </div>
              </dl>
            </div>
          ) : null}
        </Card>
      ) : null}
      {showDev && showWaterDebug && diag?.waterAudit ? (
        <Card title="WATER DEBUG" className="mt-2" data-testid="odessa-water-debug-panel">
          <p className="eds-type-caption mb-2">
            meshes {diag.waterAudit.meshCount} · kept {diag.waterAudit.kept} · duplicates hidden{" "}
            {diag.waterAudit.duplicatesHidden} · near {diag.cameraNear} · far {diag.cameraFar} · pan {diag.panSpeed}
          </p>
          <pre className="overflow-x-auto text-xs">{JSON.stringify(diag.waterAudit.surfaces, null, 2)}</pre>
        </Card>
      ) : null}
      {showDev && diag?.renderStability ? (
        <Card title="Render stability" className="mt-2" data-testid="odessa-render-stability-panel">
          <dl className="eds-type-caption grid grid-cols-2 gap-x-4 gap-y-1">
            <div>
              <dt className="opacity-70">CITY ROOT INSTANCES</dt>
              <dd data-testid="odessa-city-root-instances">{diag.renderStability.cityRootInstances}</dd>
            </div>
            <div>
              <dt className="opacity-70">MESH COUNT</dt>
              <dd>{diag.renderStability.meshCount}</dd>
            </div>
            <div>
              <dt className="opacity-70">VISIBLE MESHES</dt>
              <dd>{diag.renderStability.visibleMeshes}</dd>
            </div>
            <div>
              <dt className="opacity-70">TRANSPARENT MATERIALS</dt>
              <dd>{diag.renderStability.transparentMaterials}</dd>
            </div>
            <div>
              <dt className="opacity-70">DEPTHWRITE FALSE COUNT</dt>
              <dd>{diag.renderStability.depthWriteFalseCount}</dd>
            </div>
            <div>
              <dt className="opacity-70">CAMERA NEAR</dt>
              <dd>{diag.renderStability.cameraNear}</dd>
            </div>
            <div>
              <dt className="opacity-70">CAMERA FAR</dt>
              <dd>{diag.renderStability.cameraFar}</dd>
            </div>
            <div>
              <dt className="opacity-70">FAR/NEAR RATIO</dt>
              <dd>{diag.renderStability.farNearRatio.toFixed(1)}</dd>
            </div>
            <div>
              <dt className="opacity-70">RENDERER PIXEL RATIO</dt>
              <dd>{diag.renderStability.rendererPixelRatio}</dd>
            </div>
            <div>
              <dt className="opacity-70">DRAW CALLS</dt>
              <dd>{diag.renderStability.drawCalls}</dd>
            </div>
            <div>
              <dt className="opacity-70">TRIANGLES</dt>
              <dd>{diag.renderStability.triangles}</dd>
            </div>
          </dl>
        </Card>
      ) : null}
      {showDev && diag?.lighting ? (
        <Card title="Lighting / washout audit" className="mt-2" data-testid="odessa-lighting-panel">
          <dl className="eds-type-caption grid grid-cols-2 gap-x-4 gap-y-1">
            <div>
              <dt className="opacity-70">OUTPUT COLOR SPACE</dt>
              <dd>{diag.lighting.outputColorSpace}</dd>
            </div>
            <div>
              <dt className="opacity-70">TONE MAPPING</dt>
              <dd>{diag.lighting.toneMapping}</dd>
            </div>
            <div>
              <dt className="opacity-70">EXPOSURE</dt>
              <dd>{diag.lighting.toneMappingExposure}</dd>
            </div>
            <div>
              <dt className="opacity-70">SUN / HEMI</dt>
              <dd>
                {diag.lighting.sunIntensity} / {diag.lighting.hemiIntensity}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">FOG</dt>
              <dd>
                {diag.lighting.fogEnabled ? "on" : "off"} · {diag.lighting.fogDensity} · {diag.lighting.fogColor}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">FOG MIX @ CAMERA / DIAGONAL</dt>
              <dd data-testid="odessa-fog-mix">
                {diag.lighting.fogMixAtCameraPct}% / {diag.lighting.fogMixAtDiagonalPct}%
              </dd>
            </div>
            <div>
              <dt className="opacity-70">EMISSIVE MATERIALS</dt>
              <dd>{diag.lighting.emissiveActiveMaterials}</dd>
            </div>
            <div>
              <dt className="opacity-70">METAL W/O METALNESS MAP</dt>
              <dd>{diag.lighting.metalTexturedMaterials}</dd>
            </div>
            <div>
              <dt className="opacity-70">SRGB DATA-MAP VIOLATIONS</dt>
              <dd data-testid="odessa-srgb-violations">{diag.lighting.srgbDataMapViolations}</dd>
            </div>
            <div>
              <dt className="opacity-70">VERTEX-COLOR MESHES</dt>
              <dd>{diag.lighting.vertexColorMeshes}</dd>
            </div>
          </dl>
        </Card>
      ) : null}
      {showDev && diag?.artifactDebug ? (
        <Card title="Artifact isolation (29.4)" className="mt-2" data-testid="odessa-artifact-panel">
          <dl className="eds-type-caption grid grid-cols-2 gap-x-4 gap-y-1">
            <div>
              <dt className="opacity-70">ASSET PACKAGE</dt>
              <dd data-testid="odessa-asset-package">{diag.assetPackage ?? "—"}</dd>
            </div>
            <div>
              <dt className="opacity-70">DECAL-RANKED MESHES</dt>
              <dd data-testid="odessa-decal-count">{diag.artifactDebug.decalMeshes}</dd>
            </div>
            <div>
              <dt className="opacity-70">VERTICAL RECOVERY</dt>
              <dd data-testid="odessa-vertical-recovery">
                {diag.artifactDebug.verticalRecovery
                  ? `${diag.artifactDebug.verticalRecovery.mode} · ${diag.artifactDebug.verticalRecovery.correctedMeshes} meshes · ` +
                    `spike suspects=${diag.artifactDebug.verticalRecovery.spikeSuspects} · ` +
                    `mixed domain=${diag.artifactDebug.verticalRecovery.mixedDomainMeshes} · ` +
                    `city h=${diag.artifactDebug.verticalRecovery.cityHeight} m`
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">COMPONENT REPAIR</dt>
              <dd data-testid="odessa-component-repair">
                {diag.artifactDebug.componentRepair
                  ? `${diag.artifactDebug.componentRepair.meshes} meshes · ` +
                    `repaired=${diag.artifactDebug.componentRepair.repairedComponents} · ` +
                    `anomalies=${diag.artifactDebug.componentRepair.sourceAnomalies} · ` +
                    `guard-reverts=${diag.artifactDebug.componentRepair.revertedComponents} · ` +
                    `verts=${diag.artifactDebug.componentRepair.modifiedVertices}`
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">CAMERA ALT / BASE</dt>
              <dd>
                {diag.artifactDebug.cameraAltitude
                  ? `${diag.artifactDebug.cameraAltitude.altitudeAboveBase} m · base ${diag.artifactDebug.cameraAltitude.cityBaseY} · ` +
                    `${diag.artifactDebug.cameraAltitude.belowCityBase ? "BELOW BASE" : "above base"} · ` +
                    `${diag.artifactDebug.cameraAltitude.belowSeaLevel ? "BELOW SEA" : "above sea"} · ` +
                    `${diag.artifactDebug.cameraAltitude.insideCityBox ? "INSIDE BOX" : "outside box"}`
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="opacity-70">BISECT</dt>
              <dd>
                {diag.artifactDebug.bisect.active
                  ? `${diag.artifactDebug.bisect.showing} · ${diag.artifactDebug.bisect.currentCount}/${diag.artifactDebug.bisect.totalMeshes} · ${diag.artifactDebug.bisect.path}`
                  : "off"}
              </dd>
            </div>
            <div className="col-span-2">
              <dt className="opacity-70">LAST INSPECTION (ALT+CLICK)</dt>
              <dd data-testid="odessa-last-inspection">
                {diag.artifactDebug.lastInspection
                  ? `${diag.artifactDebug.lastInspection.object} · ${diag.artifactDebug.lastInspection.material} · ` +
                    `y=${diag.artifactDebug.lastInspection.worldPosition[1]} · h=${diag.artifactDebug.lastInspection.meshBoxHeight} · ` +
                    `rank=${diag.artifactDebug.lastInspection.decalRank ?? "—"} · d=${diag.artifactDebug.lastInspection.distance}`
                  : "— (ALT/OPTION+click a surface, e.g. the gray slab)"}
              </dd>
            </div>
          </dl>
        </Card>
      ) : null}
      {showDev && diag ? (
        <Card title="3D Debug" className="mt-2">
          <pre className="overflow-x-auto text-xs">{JSON.stringify(diag, null, 2)}</pre>
        </Card>
      ) : null}
    </div>
  );
}

export function Odessa3DQualitySelect(props: { value: QualityProfile; onChange: (v: QualityProfile) => void }) {
  return (
    <select
      className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2"
      value={props.value}
      onChange={(e) => props.onChange(e.target.value as QualityProfile)}
      aria-label="Качество 3D"
    >
      <option value="auto">AUTO</option>
      <option value="low">LOW</option>
      <option value="medium">MEDIUM</option>
      <option value="high">HIGH</option>
    </select>
  );
}
