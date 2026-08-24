/**
 * Odessa 3D scene controller — assembled city under odessaCityRoot.
 */

import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GeoTransform } from "./geoTransform";
import { ProgressiveAssetLoader } from "./assetLoader";
import { TileStreamingController } from "./tileStreaming";
import { LayerManager } from "./layerManager";
import { citySelection } from "./citySelection";
import { disposeObject3D } from "./disposeUtils";
import {
  computeGlobalCityBounds,
  fitCameraToOdessaBounds,
  focusCameraOnPoint,
  tileBoxFromObject,
  type GlobalCityBounds,
  type MaterialAudit,
} from "./cityAssembly";
import {
  clearCityEntities,
  entityFromManifestAsset,
  listCityEntities,
  registerCityEntity,
  seedPlatformBuildingEntities,
} from "./cityEntityRegistry";
import { loadOdessaManifest } from "./odessaManifest";
import { activeOdessaPackage } from "./odessaPackage";
import { clampPixelRatio, anisotropyForQuality, isLowPowerDevice, type QualitySettings } from "./qualityProfile";
import type { LoadingProgress, OdessaDevDiagnostics, OdessaManifest, OdessaPerfDiagnostics } from "./types";
import {
  AdaptivePixelRatioController,
  DemandRenderLoop,
  FrameMetricsTracker,
  HUD_THROTTLE_MS,
  STREAM_TICK_MS,
  cameraMotionKey,
  collectRendererStats,
  countVisibleSceneObjects,
} from "./odessaPerformance";
import {
  BASE_PAN_SPEED,
  CAMERA_DAMPING_FACTOR,
  CAMERA_MIN_DISTANCE_M,
  CAMERA_MIN_HEIGHT_ABOVE_BASE_M,
  CAMERA_POLAR_3D_MAX,
  CAMERA_POLAR_3D_MIN,
  CAMERA_ROTATE_SPEED,
  CAMERA_ZOOM_SPEED,
  CITY_SCREEN_SPACE_PANNING,
  CITY_ZOOM_TOWARD_POINTER,
  FOCUS_TWEEN_MS,
  HOME_TWEEN_MS,
  LOGARITHMIC_DEPTH_BUFFER,
  applyCameraGroundConstraint,
  computeCameraClipRange,
  computeAdaptiveCameraClip,
  panSpeedForDistance,
} from "./cameraNavigation";
import {
  perspectiveOverviewPose,
  polarLimitsForViewMode,
  topDownPose,
  type CameraPose,
  type CityCameraViewMode,
} from "./cameraViewMode";
import type { CityDebugSnapshot } from "./cityDebug";
import { applyWaterSurfaceGuard, isWaterLikeMesh, type WaterGuardResult } from "./waterSurfaceGuard";
import {
  DEFAULT_RENDER_ISOLATION,
  applyNeutralMaterialDiagnostic,
  collectLightingColorAudit,
  collectRenderStabilityStats,
  createNeutralDiagnosticMaterial,
  fogMixAtDepth,
  hideWaterLikeMeshes,
  safariStableRendererOptions,
  setSubtreeIsolatedHidden,
  toneMappingName,
  type RenderIsolationState,
} from "./renderStability";
import {
  ODESSA_VERTICAL_RECOVERY_FACTOR,
  ODESSA_VERTICAL_RECOVERY_MODE,
  applyOdessaVerticalScaleRecovery,
  revertOdessaVerticalScaleRecovery,
  type VerticalRecoveryMode,
} from "./verticalRecovery";
import {
  ComponentColorOverlay,
  setSceneComponentRepairEnabled,
  type ComponentRepairTag,
} from "./componentRepair";
import {
  DEFAULT_DEBUG_VIEW,
  MaterialDebugOverride,
  MeshBisector,
  SpikeHighlighter,
  cameraAltitudeReport,
  collectRuntimeSpikeReport,
  createDepthDebugMaterial,
  describeIntersection,
  setBasePlaneHidden,
  type BisectAction,
  type BisectStatus,
  type DebugViewState,
  type InspectorHit,
} from "./renderDebugTools";
import {
  InteractionRuntimeState,
  interactionPixelRatio,
  streamConcurrencyForMode,
  type RuntimePerfMode,
} from "./runtimePerfState";
import { MaterialInternCache } from "./materialIntern";
import { ProgressiveSceneActivator, type ActivatorAttachContext } from "./progressiveActivator";
import { FirstLoadProfiler } from "./firstLoadProfiler";
import { resolveBootState, type BootState } from "./assetLifecycle";
import { cacheManifestCenter, cacheMeasuredBounds, clearBoundsCache, getCachedCenter } from "./assetBoundsCache";
import { OdessaEnvironment, resolveEnvironmentQuality } from "./environment";
import { formatClassifiedMaterials } from "./environment/buildingReadability";
import { LodVisibilityManager, isSeaOrCoastProtected, lodThresholdsFor } from "./lod";
import { classifyParseBand } from "./loading/parsePolicy";
import { DevLongTaskObserver } from "./loading/longTaskObserver";
import {
  PickRegistry,
  HighlightController,
  bindPickableEntity,
  bindingCounts,
  auditSceneGraph,
  emptySceneGraphAudit,
  isClickGesture,
  exceedsDragThreshold,
  pointerToNdc,
  createRaycastMeter,
  recordRaycast,
  HOVER_RAYCAST_INTERVAL_MS,
  type InteractionSnapshot,
  type SceneGraphAudit,
} from "./interaction";
import {
  applyFocusTween,
  createFocusTween,
  focusPoseForObject,
  type CameraFocusTween,
} from "./interaction/focusCamera";
import {
  GeoReferenceRuntime,
  GeoAnchorRenderer,
  GeoDebugGrid,
  CalibrationMarkerRenderer,
  geoSelectionBridge,
  formatLatLon,
  gridSpacingForDistance,
  odessaModelFingerprint,
  ALTITUDE_POLICY,
  worldToLocalMeters,
  describeAxisMapping,
} from "./geospatial";
import type { CalibrationSlotId, GeoCoordinate, LocalWorldCoordinate } from "./geospatial";
import { formatCityGeoDebug } from "./cityDebug";

export type OdessaSceneCallbacks = {
  onProgress?: (p: LoadingProgress) => void;
  onSelect?: (entityId: string | null) => void;
  onInteraction?: (snap: InteractionSnapshot) => void;
  onInitError?: (message: string, error?: Error) => void;
  onPerfStats?: (stats: OdessaPerfDiagnostics) => void;
  onCalibrationPick?: (world: LocalWorldCoordinate) => void;
};

export class OdessaSceneController {
  private renderer: THREE.WebGLRenderer | null = null;
  private scene = new THREE.Scene();
  /** Single parent for all 45 GLB tiles — global corrections only here. */
  private odessaCityRoot = new THREE.Group();
  private tileDebugGroup = new THREE.Group();
  private pickDebugGroup = new THREE.Group();
  private camera: THREE.PerspectiveCamera | null = null;
  private controls: OrbitControls | null = null;
  private raycaster = new THREE.Raycaster();
  private pointer = new THREE.Vector2();
  private renderLoop: DemandRenderLoop | null = null;
  private resizeObserver: ResizeObserver | null = null;
  private disposed = false;
  private manifest: OdessaManifest | null = null;
  private geo: GeoTransform | null = null;
  private loader = new ProgressiveAssetLoader();
  private stream: TileStreamingController | null = null;
  private layers = new LayerManager();
  private layerGroups = new Map<string, THREE.Group>();
  private assetNodes = new Map<string, THREE.Object3D>();
  private assetVisibility = new Map<string, boolean>();
  private tileHelpers = new Map<string, THREE.Object3D>();
  private settings: QualitySettings;
  private canvas: HTMLCanvasElement | null = null;
  private callbacks: OdessaSceneCallbacks;
  private initError: string | null = null;
  private lastStreamMs = 0;
  private lastHudMs = 0;
  private lastResize = { w: 0, h: 0 };
  private globalBounds: GlobalCityBounds | null = null;
  private materialAudit: MaterialAudit | null = null;
  private showTileBounds = false;
  private lastClickMs = 0;
  private clickMoved = false;
  private pointerDown = { x: 0, y: 0 };
  private frameMetrics = new FrameMetricsTracker();
  private adaptiveDpr: AdaptivePixelRatioController;
  private appliedAnisotropy = 1;
  private renderDirty = true;
  private controlsMoving = false;
  private dampingPending = false;
  private loaderBusy = false;
  private lastCamKey = "";
  private continuousRender = false;
  private waterAudit: WaterGuardResult | null = null;
  private waterDebug = false;
  private zoomTowardPointer = CITY_ZOOM_TOWARD_POINTER;
  private interaction = new InteractionRuntimeState();
  private materialShare = new MaterialInternCache();
  private assetCenters = new Map<string, THREE.Vector3>();
  private lastPanDist = -1;
  private lastRuntimeMode: RuntimePerfMode = "IDLE";
  private lastStreamConcurrent = -1;
  private environment: OdessaEnvironment | null = null;
  private lod = new LodVisibilityManager();
  private scratchSphere = new THREE.Sphere();
  private activator = new ProgressiveSceneActivator();
  private profiler = new FirstLoadProfiler();
  private bootState: BootState = "BOOTSTRAP";
  private lastFps = 60;
  private lastActivatedId: string | null = null;
  private recordedParse = new Set<string>();
  private scratchFrustum = new THREE.Frustum();
  private scratchProj = new THREE.Matrix4();
  private firstGeometryRendered = false;
  private longTasks = new DevLongTaskObserver();
  private mountPhase: "idle" | "manifest" | "renderer" | "streaming" | "ready" | "failed" = "idle";
  private rendererReady = false;
  private pickRegistry = new PickRegistry();
  private highlighter = new HighlightController();
  private interactionEnabled = true;
  private hoveredPickId: string | null = null;
  private selectedPickId: string | null = null;
  private selectedActive = false;
  private lastHoverRaycastMs = 0;
  private pointerInside = false;
  private raycastMeter = createRaycastMeter();
  private sceneAudit: SceneGraphAudit = emptySceneGraphAudit();
  private focusTween: CameraFocusTween | null = null;
  private cameraViewMode: CityCameraViewMode = "3d";
  private homePose: CameraPose | null = null;
  private last3dPose: CameraPose | null = null;
  private showSelectionBounds = false;
  private geoRef = new GeoReferenceRuntime();
  private geoMarkers = new GeoAnchorRenderer();
  private geoGrid = new GeoDebugGrid();
  private calMarkers = new CalibrationMarkerRenderer();
  private lastClickWorld: { x: number; y: number; z: number } | null = null;
  private lastHoverWorld: { x: number; y: number; z: number } | null = null;
  private calibrationPicking = false;
  private isolation: RenderIsolationState = { ...DEFAULT_RENDER_ISOLATION };
  private neutralMat: THREE.MeshLambertMaterial | null = null;
  private debugView: DebugViewState = { ...DEFAULT_DEBUG_VIEW };
  /* STEP 29.9: the metric package renders vendor geometry directly — the
   * legacy recovery chain only ever runs for the CURRENT_BROKEN package. */
  private verticalRecoveryMode: VerticalRecoveryMode = activeOdessaPackage().runtimeGeometryRecovery
    ? ODESSA_VERTICAL_RECOVERY_MODE
    : "off";
  private savedSpikeVis: Map<THREE.Mesh, boolean> | null = null;
  private matOverride = new MaterialDebugOverride();
  private spikeHighlighter = new SpikeHighlighter();
  private componentOverlay = new ComponentColorOverlay();
  private bisector = new MeshBisector();
  private depthDebugMat: THREE.MeshDepthMaterial | null = null;
  private debugAmbient: THREE.AmbientLight | null = null;
  private meshBoundsGroup = new THREE.Group();
  private savedSceneVis: Map<THREE.Object3D, boolean> | null = null;
  private savedFog: THREE.Scene["fog"] | undefined = undefined;
  private savedBackground: THREE.Scene["background"] | undefined = undefined;
  private lastInspection: InspectorHit | null = null;
  private inspectRaycaster = new THREE.Raycaster();

  constructor(settings: QualitySettings, callbacks: OdessaSceneCallbacks = {}) {
    this.settings = settings;
    this.callbacks = callbacks;
    this.adaptiveDpr = new AdaptivePixelRatioController(settings.profile, settings.pixelRatioCap);
    this.loader.setMaxConcurrent(settings.maxConcurrentLoads);
    this.odessaCityRoot.name = "odessaCityRoot";
    this.tileDebugGroup.name = "tile_debug";
    this.tileDebugGroup.visible = false;
    this.pickDebugGroup.name = "pick_debug";
    this.pickDebugGroup.visible = false;
    this.highlighter.attachDebugGroup(this.pickDebugGroup);
    this.geoMarkers.setVisualOffset(ALTITUDE_POLICY.visualOffsetWorld);
    this.geoMarkers.group.visible = false;
    this.geoGrid.group.visible = false;
    this.calMarkers.group.visible = false;
  }

  runtimeStatus(): {
    phase: string;
    disposed: boolean;
    manifest: string;
    controller: string;
    webgl: string;
    canvas: string;
  } {
    const glApi = typeof WebGLRenderingContext !== "undefined";
    return {
      phase: this.mountPhase,
      disposed: this.disposed,
      manifest: this.manifest ? `ok:${this.manifest.tiles.length} tiles` : "pending",
      controller: this.disposed ? "disposed" : this.rendererReady ? "mounted" : "mounting",
      webgl: this.renderer ? "ok" : glApi ? "api-present" : "missing",
      canvas: this.canvas?.isConnected ? `${this.lastResize.w}x${this.lastResize.h}` : "detached",
    };
  }

  async mount(canvas: HTMLCanvasElement) {
    if (this.disposed) return;
    this.canvas = canvas;
    this.mountPhase = "manifest";
    try {
      if (typeof canvas.isConnected === "boolean" && !canvas.isConnected) {
        throw new Error("canvas_not_in_document");
      }
      clearCityEntities();
      seedPlatformBuildingEntities();
      /* STEP 29.9: manifest comes from the active package
       * (REBUILT_METRIC by default, CURRENT_BROKEN as dev rollback). */
      this.manifest = await loadOdessaManifest(activeOdessaPackage().manifestUrl);
      if (this.disposed) return;
      this.profiler.markManifest();
      this.geo = new GeoTransform(this.manifest.geoTransform);
      this.layers.bootstrap(this.manifest.layers);
      if (!this.odessaCityRoot.parent) this.scene.add(this.odessaCityRoot);
      this.scene.add(this.tileDebugGroup);
      this.scene.add(this.pickDebugGroup);
      this.scene.add(this.geoMarkers.group);
      this.scene.add(this.geoGrid.group);
      this.scene.add(this.calMarkers.group);
      for (const layer of this.manifest.layers) {
        const g = new THREE.Group();
        g.name = `layer_${layer.id}`;
        g.visible = this.layers.isVisible(layer.id);
        this.layerGroups.set(layer.id, g);
        this.odessaCityRoot.add(g);
      }
      for (const tile of this.manifest.tiles) {
        for (const asset of tile.assets) {
          this.loader.registerManifestAsset(tile.id, asset);
          cacheManifestCenter(asset.id, asset.bounds);
          const ent = entityFromManifestAsset(this.manifest, tile.id, asset);
          if (ent) registerCityEntity(ent);
        }
      }
      this.geoRef.resolve({
        originLat: this.manifest.geoTransform.originLat,
        originLng: this.manifest.geoTransform.originLng,
        calibrated: this.manifest.geoTransform.calibrated,
        loadPersisted: true,
        currentFingerprint: odessaModelFingerprint({
          ...this.manifest,
          packageId: activeOdessaPackage().id,
        }),
      });
      this.geoRef.setAnchorsFromEntities(listCityEntities());
      this.syncGeoOverlays();
      this.stream = new TileStreamingController(this.manifest, this.geo, this.loader);
      this.loader.onFetchCancelled = (assetId) => {
        const asset = this.loader.registry.get(assetId);
        if (asset?.tileId) this.stream?.releaseTileIfUnloaded(asset.tileId);
      };
      this.loader.subscribe((p) => {
        if (this.disposed) return;
        this.loaderBusy = p.loading > 0 || p.queued > 0 || this.loader.isParseBusy();
        this.emitHudProgress(p);
        this.requestRender();
      });
      this.emitHudProgress();
      this.mountPhase = "renderer";
      this.initRenderer(canvas);
      if (this.disposed) return;
      this.bindResizeObserver(canvas);
      this.refreshGlobalBounds();
      this.syncGeoWorldBox();
      this.fitCameraToOdessa(true);
      this.mountPhase = "streaming";
      this.stream.bootstrapPriorityTiles();
      if (import.meta.env.DEV) this.longTasks.start();
      this.startRenderLoop();
      this.requestRender();
      this.mountPhase = "ready";
    } catch (err) {
      if (this.disposed) return;
      this.mountPhase = "failed";
      const error = err instanceof Error ? err : new Error(String(err));
      this.initError = error.message;
      this.callbacks.onInitError?.(this.initError, error);
    }
  }

  private startRenderLoop() {
    this.renderLoop = new DemandRenderLoop({
      onFrame: (now) => this.onFrame(now),
      shouldContinue: () => this.shouldKeepRendering(),
    });
    this.renderLoop.requestFrame();
  }

  private shouldKeepRendering(): boolean {
    if (this.disposed) return false;
    return (
      this.renderDirty ||
      this.controlsMoving ||
      this.dampingPending ||
      this.loaderBusy ||
      this.continuousRender ||
      this.focusTween != null ||
      this.interaction.getMode() !== "IDLE" ||
      this.activator.pendingCount() > 0 ||
      this.loader.isParseBusy()
    );
  }

  requestRender() {
    this.renderDirty = true;
    this.renderLoop?.requestFrame();
  }

  private onFrame(now: number) {
    if (this.disposed) return;

    if (this.controls && this.camera) {
      const keyBefore = this.lastCamKey;
      if (this.focusTween) {
        const done = applyFocusTween(this.focusTween, now, this.camera, this.controls.target);
        this.controls.minPolarAngle = 0;
        this.controls.maxPolarAngle = Math.PI;
        this.controls.update();
        this.applyCameraSafety();
        this.renderDirty = true;
        if (done) {
          this.focusTween = null;
          this.applyPolarForViewMode();
          this.applyCameraSafety();
        }
      } else {
        this.controls.update();
        this.applyCameraSafety();
      }
      const keyAfter = cameraMotionKey(this.camera, this.controls.target);
      const moved = keyAfter !== keyBefore;
      if (moved) {
        this.lastCamKey = keyAfter;
        this.renderDirty = true;
        this.dampingPending = true;
      } else {
        this.dampingPending = false;
      }
      const mode = this.interaction.tick(now, moved);
      this.applyRuntimeMode(mode);
      if (this.environment && this.camera && this.controls) {
        this.environment.updateFrame(this.camera.position.distanceTo(this.controls.target));
      }
      if (this.camera) {
        this.geoMarkers.updateScales(this.camera);
        this.calMarkers.updateScales(this.camera);
      }
    } else {
      this.interaction.tick(now, false);
    }

    const pauseStream = this.interaction.shouldPauseStreaming();
    if (this.stream && this.camera && now - this.lastStreamMs > STREAM_TICK_MS) {
      this.lastStreamMs = now;
      this.syncAssetPriorities();
      if (!pauseStream) {
        this.stream.schedule(
          this.camera,
          {
            maxActiveTiles: Math.max(this.settings.maxActiveTiles, 12),
            loadDistanceM: this.settings.loadDistanceM,
            unloadDistanceM: this.settings.unloadDistanceM,
            heavyLoadDistanceM: this.settings.heavyLoadDistanceM,
            heavyUnloadDistanceM: this.settings.heavyUnloadDistanceM,
            targetX: this.controls?.target.x,
            targetZ: this.controls?.target.z,
            cityDiagonalM: this.globalBounds?.diagonal,
            profile: this.settings.profile,
            lodBias: this.settings.lodBias,
          },
          {
            pauseNewActivations: false,
            pauseUnload: this.interaction.shouldPauseHeavyUnload(),
          },
        );
      }
      if (!this.interaction.shouldDeferVisibilityPass()) {
        this.applyDistanceVisibility();
      }
      this.requestRender();
    }

    this.syncPipelineRuntime();
    const attached = this.activateParsedAssets(now);
    if (attached) this.requestRender();

    if (this.renderer && this.camera && this.renderDirty) {
      const frame = this.frameMetrics.tick(now);
      this.lastFps = frame.fps;
      this.adaptiveDpr.observe(frame.frameMs, now, frame.fps, this.interaction.getMode());
      const device = typeof window !== "undefined" ? window.devicePixelRatio : 1;
      const guarded = this.adaptiveDpr.currentRatio(device);
      const dpr = clampPixelRatio(
        interactionPixelRatio(guarded, this.interaction.shouldDipPixelRatio()),
        this.settings.pixelRatioCap,
      );
      if (Math.abs(this.renderer.getPixelRatio() - dpr) > 0.01) {
        this.renderer.setPixelRatio(dpr);
      }
      this.renderer.render(this.scene, this.camera);
      this.renderDirty = false;
      if (this.assetNodes.size > 0 && !this.firstGeometryRendered) {
        this.firstGeometryRendered = true;
        this.profiler.markFirstRender();
      }
      this.emitPerfStats(now, frame);
    }
  }

  private applyRuntimeMode(mode: RuntimePerfMode) {
    const cap = this.adaptiveDpr.getStreamConcurrencyCap(this.settings.maxConcurrentLoads);
    const concurrent = streamConcurrencyForMode(this.settings.maxConcurrentLoads, mode, cap);
    if (concurrent !== this.lastStreamConcurrent) {
      this.lastStreamConcurrent = concurrent;
      this.loader.setMaxConcurrent(concurrent);
    }
    const paused = this.interaction.shouldPauseStreaming();
    if (this.loader.isStreamingPaused() !== paused) {
      this.loader.setStreamingPaused(paused);
    }
    if (mode !== this.lastRuntimeMode) {
      this.lastRuntimeMode = mode;
      this.requestRender();
    }
  }

  private syncPipelineRuntime() {
    let pendingMb = 0;
    for (const asset of this.loader.registry.list()) {
      if (
        (asset.lifecycle === "parsed" || asset.lifecycle === "preparing" || asset.lifecycle === "ready") &&
        !this.assetNodes.has(asset.id)
      ) {
        pendingMb += asset.sizeMb ?? 0;
      }
    }
    this.loader.setRuntime({
      mode: this.interaction.getMode(),
      fps: this.lastFps,
      bootState: this.bootState,
      waitingActivationCount: this.activator.pendingCount(),
      waitingActivationMb: pendingMb,
    });
    this.loader.tickQueues();
  }

  private syncAssetPriorities() {
    if (!this.stream || !this.camera) return;
    const cam = this.camera;
    const targetX = this.controls?.target.x ?? cam.position.x;
    const targetZ = this.controls?.target.z ?? cam.position.z;
    const thresholds = lodThresholdsFor(this.settings.profile, this.globalBounds?.diagonal, this.settings.lodBias);
    const states = this.stream.evaluate(cam, {
      targetX,
      targetZ,
      cityDiagonalM: this.globalBounds?.diagonal,
      profile: this.settings.profile,
      lodBias: this.settings.lodBias,
    });
    for (const st of states) {
      const tile = this.stream.tileById(st.tileId);
      if (!tile) continue;
      const cx = tile.centerScene?.x ?? 0;
      const cz = tile.centerScene?.z ?? 0;
      const toTarget = Math.hypot(cx - targetX, cz - targetZ);
      const nearTarget = toTarget < thresholds.targetProtectM;
      const seaTile = isSeaOrCoastProtected(tile.id, st.layerId);
      const parseBand = classifyParseBand({
        distanceM: st.distanceM,
        inFrustum: st.inFrustum,
        nearTarget,
        nearM: thresholds.nearM,
        midM: thresholds.midM,
        farM: thresholds.farM,
      });
      for (const asset of tile.assets) {
        this.loader.updatePriority(asset.id, {
          score: st.score,
          parseBand,
          nearTarget,
          inFrustum: st.inFrustum,
          seaProtected: seaTile || isSeaOrCoastProtected(asset.id, asset.layer, asset.url),
        });
      }
    }
  }

  private emitPerfStats(now: number, frame: { fps: number; frameMs: number }) {
    if (!this.callbacks.onPerfStats || !this.renderer || !this.controls) return;
    if (now - this.lastHudMs < HUD_THROTTLE_MS) return;
    this.lastHudMs = now;
    const stats = collectRendererStats(this.renderer);
    const c = this.loader.registry.counts();
    const visibleGlbs = [...this.assetNodes.values()].filter((n) => n.visible).length;
    const vis = this.activator.visualPrepStats();
    this.callbacks.onPerfStats({
      fps: +frame.fps.toFixed(1),
      frameMs: +frame.frameMs.toFixed(1),
      drawCalls: stats.drawCalls,
      triangles: stats.triangles,
      points: stats.points,
      lines: stats.lines,
      geometries: stats.geometries,
      textures: stats.textures,
      visibleObjects: countVisibleSceneObjects(this.scene),
      loadedGlbs: c.realGlb,
      visibleGlbs,
      queuedAssets: c.queued,
      activeTiles: this.stream?.activeTileIds().length ?? 0,
      cameraDistance: +this.camera!.position.distanceTo(this.controls!.target).toFixed(1),
      pixelRatio: this.renderer.getPixelRatio(),
      adaptiveTier: this.adaptiveDpr.getTierLabel(),
      continuousRender: this.shouldKeepRendering(),
      runtimeMode: this.interaction.getMode(),
      streamingPaused: this.loader.isStreamingPaused(),
      bootState: this.bootState,
      parsedCount: this.loader.progress().parsedCount,
      downloadedCount: this.loader.progress().downloadedCount,
      firstLoad: this.firstLoadSnapshot(),
      environment: this.environment
        ? {
            ...this.environment.diagnostics(),
            classifiedMaterials: formatClassifiedMaterials(vis),
            normalizedMaterials: vis.normalizedMaterials,
            texturedMaterialsSkipped: vis.texturedMaterialsSkipped,
            buildingVariationCount: vis.buildingVariationCount,
          }
        : undefined,
      lod: this.lod.diagnostics(),
      pipeline: this.loader.pipelineSnapshot(this.activator.pendingCount()),
      quality: {
        mode: this.settings.profile,
        pixelRatio: this.renderer.getPixelRatio(),
        antialias: this.settings.antialias,
        anisotropy: this.appliedAnisotropy,
        fps: +frame.fps.toFixed(1),
        interactionState: this.interaction.getMode(),
        visibleAssets: visibleGlbs,
        hiddenAssets: Math.max(0, this.assetNodes.size - visibleGlbs),
        lodTransitionsPerSec: this.lod.diagnostics().transitionsPerSec,
        triangles: stats.triangles,
        drawCalls: stats.drawCalls,
      },
    });
  }

  private firstLoadSnapshot(): OdessaPerfDiagnostics["firstLoad"] {
    const snap = this.profiler.snapshot();
    return {
      timeToManifest: snap.timeToManifest,
      timeToFirstParse: snap.timeToFirstParse,
      timeToFirstGeometry: snap.timeToFirstGeometry,
      timeToFirstRender: snap.timeToFirstRender,
      timeToInteractive: snap.timeToInteractive,
      timeTo50PercentActive: snap.timeTo50PercentActive,
      timeToReady: snap.timeToReady,
      totalParseMs: snap.totalParseMs,
      averageParseMs: snap.averageParseMs,
      longTaskCount: snap.longTaskCount,
      longTasks50: snap.longTasks50,
      longTasks100: snap.longTasks100,
      longTasks250: snap.longTasks250,
      longTasks500: snap.longTasks500,
      worst10: snap.worst10.map((r) => ({
        id: r.id,
        parseMs: r.parseMs,
        sizeMb: r.sizeMb,
        triangleCount: r.triangleCount,
      })),
    };
  }

  private applyDistanceVisibility() {
    if (!this.camera || !this.stream) return;
    const cam = this.camera;
    const target = this.controls?.target;
    cam.updateMatrixWorld();
    this.scratchProj.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse);
    this.scratchFrustum.setFromProjectionMatrix(this.scratchProj);
    const assets = [...this.assetNodes.entries()].map(([id, node]) => {
      const asset = this.loader.registry.get(id);
      return {
        id,
        url: asset?.url,
        layerId: asset?.layerId,
        tileId: asset?.tileId,
        bounds: asset?.bounds,
        sizeMb: asset?.sizeMb,
        triangleCount: asset?.triangleCount,
        currentlyVisible: this.assetVisibility.get(id) ?? node.visible,
      };
    });
    const decisions = this.lod.evaluate(assets, {
      camX: cam.position.x,
      camZ: cam.position.z,
      targetX: target?.x ?? cam.position.x,
      targetZ: target?.z ?? cam.position.z,
      inFrustum: (x, y, z, radius) => {
        this.scratchSphere.center.set(x, y, z);
        this.scratchSphere.radius = radius;
        return this.scratchFrustum.intersectsSphere(this.scratchSphere);
      },
      fovYDeg: cam instanceof THREE.PerspectiveCamera ? cam.fov : 50,
      viewportHeight: this.lastResize.h || 520,
      profile: this.settings.profile,
      cityDiagonalM: this.globalBounds?.diagonal ?? 1400,
      lodBias: this.settings.lodBias,
      priorityIds: new Set(this.manifest?.priorityTiles || []),
    });
    for (const d of decisions) {
      const node = this.assetNodes.get(d.id);
      if (!node) continue;
      const prev = this.assetVisibility.get(d.id) ?? true;
      if (d.visible === prev) continue;
      node.visible = d.visible;
      this.assetVisibility.set(d.id, d.visible);
      const asset = this.loader.registry.get(d.id);
      if (asset && (asset.lifecycle === "active" || asset.lifecycle === "hidden")) {
        this.loader.registry.update(d.id, { lifecycle: d.visible ? "active" : "hidden" });
      }
      this.requestRender();
    }
  }

  private initRenderer(canvas: HTMLCanvasElement) {
    if (this.disposed || this.rendererReady || this.renderer) return;
    const parent = canvas.parentElement;
    const w = Math.max(1, parent?.clientWidth || canvas.clientWidth || 800);
    const h = Math.max(1, parent?.clientHeight || canvas.clientHeight || 520);

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      ...safariStableRendererOptions(this.settings.antialias),
      logarithmicDepthBuffer: LOGARITHMIC_DEPTH_BUFFER,
    });
    this.rendererReady = true;
    const gpuMax =
      typeof this.renderer.capabilities.getMaxAnisotropy === "function"
        ? this.renderer.capabilities.getMaxAnisotropy()
        : 1;
    this.appliedAnisotropy = anisotropyForQuality(this.settings.profile, gpuMax, isLowPowerDevice());
    const dpr = clampPixelRatio(
      this.adaptiveDpr.currentRatio(typeof window !== "undefined" ? window.devicePixelRatio : 1),
      this.settings.pixelRatioCap,
    );
    this.renderer.setPixelRatio(dpr);
    this.renderer.setSize(w, h, false);

    const clip = computeCameraClipRange({ size: { x: 1000, y: 50, z: 1000 }, diagonal: 1400 }, this.settings.cameraFarCap);
    this.camera = new THREE.PerspectiveCamera(50, w / h, clip.near, clip.far);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = CAMERA_DAMPING_FACTOR;
    this.controls.rotateSpeed = CAMERA_ROTATE_SPEED;
    this.controls.panSpeed = BASE_PAN_SPEED;
    this.controls.zoomSpeed = CAMERA_ZOOM_SPEED;
    this.controls.minPolarAngle = CAMERA_POLAR_3D_MIN;
    this.controls.maxPolarAngle = CAMERA_POLAR_3D_MAX;
    this.controls.screenSpacePanning = CITY_SCREEN_SPACE_PANNING;
    this.controls.zoomToCursor = this.zoomTowardPointer;
    this.controls.mouseButtons = {
      LEFT: THREE.MOUSE.PAN,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.ROTATE,
    };
    this.controls.touches = {
      ONE: THREE.TOUCH.PAN,
      TWO: THREE.TOUCH.DOLLY_ROTATE,
    };
    this.controls.addEventListener("change", this.onControlsChange);
    this.controls.addEventListener("start", this.onControlsStart);
    this.controls.addEventListener("end", this.onControlsEnd);
    this.controls.update();

    this.environment = new OdessaEnvironment({
      quality: resolveEnvironmentQuality(this.settings.profile),
      enableLocalShadows: this.settings.enableLocalShadows,
    });
    this.environment.mount(this.scene, this.renderer);

    canvas.addEventListener("pointerdown", this.syncOrbitModifier, true);
    canvas.addEventListener("pointerdown", this.onPointerDown);
    canvas.addEventListener("pointermove", this.onPointerMove);
    canvas.addEventListener("pointerup", this.onPointerUp);
    canvas.addEventListener("pointerup", this.restoreOrbitButtons, true);
    canvas.addEventListener("pointerleave", this.onPointerLeave);
    canvas.addEventListener("pointerenter", this.onPointerEnter);
    canvas.addEventListener("dblclick", this.onDoubleClick);
    canvas.addEventListener("contextmenu", this.onContextMenu);

    this.lastResize = { w, h };
  }

  private onControlsChange = () => {
    this.applyCameraSafety();
    this.updatePanSensitivity();
    this.requestRender();
  };

  private applyCameraSafety() {
    if (!this.camera || !this.controls) return;
    const baseY = this.globalBounds?.box.min.y ?? 0;
    applyCameraGroundConstraint(this.camera, this.controls.target, baseY, CAMERA_MIN_HEIGHT_ABOVE_BASE_M);
  }

  private applyPolarForViewMode() {
    if (!this.controls) return;
    const limits = polarLimitsForViewMode(this.cameraViewMode);
    this.controls.minPolarAngle = limits.minPolarAngle;
    this.controls.maxPolarAngle = limits.maxPolarAngle;
  }

  private beginCameraTween(to: CameraPose, durationMs: number) {
    if (!this.camera || !this.controls) return;
    this.focusTween = createFocusTween(
      performance.now(),
      this.camera.position,
      to.position,
      this.controls.target,
      to.target,
      durationMs,
    );
    this.updatePanSensitivity(true);
    this.requestRender();
  }

  private onControlsStart = () => {
    this.controlsMoving = true;
    this.interaction.start(performance.now());
    this.updatePanSensitivity(true);
    this.requestRender();
  };

  private onControlsEnd = () => {
    this.controlsMoving = false;
    this.interaction.end(performance.now());
    this.updatePanSensitivity(true);
    this.syncAdaptiveClip();
    this.requestRender();
  };

  private updatePanSensitivity(force = false) {
    if (!this.controls || !this.camera) return;
    const dist = this.camera.position.distanceTo(this.controls.target);
    if (!force && this.lastPanDist >= 0 && Math.abs(dist - this.lastPanDist) < 4) return;
    this.lastPanDist = dist;
    const diag = this.globalBounds?.diagonal ?? 1200;
    this.controls.panSpeed = panSpeedForDistance({
      distance: dist,
      cityDiagonal: diag,
      viewportHeight: this.lastResize.h || 520,
      basePanSpeed: BASE_PAN_SPEED,
    });
  }

  private bindResizeObserver(canvas: HTMLCanvasElement) {
    const parent = canvas.parentElement;
    if (!parent || typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", this.onWindowResize);
      return;
    }
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(parent);
  }

  private onWindowResize = () => {
    this.resize();
  };

  private onContextMenu = (e: Event) => {
    e.preventDefault();
  };

  private syncOrbitModifier = (e: PointerEvent) => {
    if (!this.controls) return;
    const rotate = e.altKey || e.ctrlKey || e.metaKey || e.shiftKey;
    this.controls.mouseButtons.LEFT = rotate ? THREE.MOUSE.ROTATE : THREE.MOUSE.PAN;
  };

  private restoreOrbitButtons = () => {
    if (!this.controls) return;
    this.controls.mouseButtons.LEFT = THREE.MOUSE.PAN;
  };

  private onPointerDown = (e: PointerEvent) => {
    this.pointerInside = true;
    this.pointerDown = { x: e.clientX, y: e.clientY };
    this.clickMoved = false;
    if (this.focusTween) this.focusTween = null;
  };

  private onPointerEnter = () => {
    this.pointerInside = true;
  };

  private onPointerLeave = () => {
    this.pointerInside = false;
    this.setHoveredPickId(null);
  };

  private onPointerMove = (e: PointerEvent) => {
    if (exceedsDragThreshold(this.pointerDown, { x: e.clientX, y: e.clientY })) {
      this.clickMoved = true;
    }
    this.maybeHoverRaycast(e.clientX, e.clientY, performance.now());
  };

  private onPointerUp = (e: PointerEvent) => {
    if (e.button !== 0) return;
    if (e.altKey) {
      this.inspectAtScreen(e.clientX, e.clientY);
      return;
    }
    this.handleClick(e.clientX, e.clientY);
  };

  private onDoubleClick = (e: MouseEvent) => {
    if (this.calibrationPicking) return;
    if (!this.interactionEnabled) return;
    const hit = this.raycastPick(e.clientX, e.clientY);
    if (!hit) return;
    this.selectPickId(hit.entity.pickId);
    this.focusPickId(hit.entity.pickId);
  };

  resize() {
    if (!this.renderer || !this.camera || !this.canvas?.parentElement) return;
    const w = this.canvas.parentElement.clientWidth;
    const h = this.canvas.parentElement.clientHeight;
    if (w === this.lastResize.w && h === this.lastResize.h) return;
    this.lastResize = { w, h };
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
    this.requestRender();
  }

  resetCamera() {
    if (!this.camera || !this.controls) {
      this.fitCameraToOdessa(true);
      return;
    }
    this.cameraViewMode = "3d";
    this.applyPolarForViewMode();
    const bounds = this.globalBounds ?? this.refreshGlobalBounds();
    const pose = this.homePose ?? perspectiveOverviewPose(bounds, this.camera, this.camera.aspect);
    this.beginCameraTween(pose, HOME_TWEEN_MS);
  }

  getCameraViewMode(): CityCameraViewMode {
    return this.cameraViewMode;
  }

  setCameraViewMode(mode: CityCameraViewMode) {
    if (!this.camera || !this.controls) return;
    if (mode === this.cameraViewMode) return;
    const bounds = this.globalBounds ?? this.refreshGlobalBounds();
    if (mode === "2d") {
      this.last3dPose = {
        position: this.camera.position.clone(),
        target: this.controls.target.clone(),
      };
      this.cameraViewMode = "2d";
      this.applyPolarForViewMode();
      this.beginCameraTween(topDownPose(bounds), HOME_TWEEN_MS);
      return;
    }
    this.cameraViewMode = "3d";
    this.applyPolarForViewMode();
    const pose =
      this.last3dPose ?? this.homePose ?? perspectiveOverviewPose(bounds, this.camera, this.camera.aspect);
    this.beginCameraTween(pose, HOME_TWEEN_MS);
  }

  cityDebugSnapshot(fps = this.lastFps): CityDebugSnapshot {
    const cam = this.camera?.position;
    const tgt = this.controls?.target;
    const hovered = this.hoveredPickId ? this.pickRegistry.get(this.hoveredPickId) : undefined;
    const selected = this.selectedPickId ? this.pickRegistry.get(this.selectedPickId) : undefined;
    const solve = this.geoRef.solveResult();
    const cal = this.geoRef.calibration();
    const camWorld = cam ? { x: cam.x, y: cam.y, z: cam.z } : null;
    const camGeo = camWorld && this.geoRef.overlaysOn() ? this.geoRef.toGeo(camWorld) : null;
    const selWorld = selected?.position ?? this.lastClickWorld;
    const selGeo = selWorld && this.geoRef.overlaysOn() ? this.geoRef.toGeo(selWorld) : null;
    const enu = camWorld && cal ? worldToLocalMeters(camWorld, cal) : null;
    return {
      fps,
      camera: { x: cam?.x ?? 0, y: cam?.y ?? 0, z: cam?.z ?? 0 },
      target: { x: tgt?.x ?? 0, y: tgt?.y ?? 0, z: tgt?.z ?? 0 },
      hovered: hovered?.displayName ?? hovered?.meshName ?? this.hoveredPickId,
      selected: selected?.displayName ?? selected?.meshName ?? this.selectedPickId,
      hoveredCoords: hovered?.position ?? null,
      selectedCoords: selected?.position ?? null,
      viewMode: this.cameraViewMode,
      geo: {
        status: solve.status,
        controlPoints: solve.controlPointCount,
        yaw: solve.rotation,
        scale: solve.scale,
        axis: cal ? describeAxisMapping(cal.axisMapping) : "—",
        meanError: solve.meanErrorMeters,
        maxError: solve.maxErrorMeters,
        cameraLat: camGeo?.lat ?? null,
        cameraLon: camGeo?.lon ?? null,
        cameraAlt: camGeo?.altitude ?? null,
        cameraEnu: enu,
        selectedLat: selGeo?.lat ?? null,
        selectedLon: selGeo?.lon ?? null,
      },
    };
  }

  copyGeoDebug(): string {
    return formatCityGeoDebug(this.cityDebugSnapshot());
  }

  focusGeo(geo: GeoCoordinate) {
    if (!this.camera || !this.controls) return;
    const world = this.geoRef.toWorld(geo);
    if (!world) return;
    const bounds = this.globalBounds ?? this.refreshGlobalBounds();
    const pose = focusCameraOnPoint(
      new THREE.Vector3(world.x, world.y, world.z),
      this.camera,
      this.controls.target,
      0.08,
      bounds.diagonal,
    );
    this.beginCameraTween({ position: pose.position, target: pose.target }, FOCUS_TWEEN_MS);
  }

  consumePendingGeoFocus() {
    const geo = geoSelectionBridge.consumeShow3d();
    if (geo) this.focusGeo(geo);
  }

  fitCameraToOdessa(_saveDefault = false) {
    if (!this.camera || !this.controls) return;
    const bounds = this.refreshGlobalBounds();
    const fit = fitCameraToOdessaBounds(bounds, this.camera, this.camera.aspect);
    const clip = computeCameraClipRange(bounds, this.settings.cameraFarCap);
    this.camera.position.copy(fit.position);
    this.controls.target.copy(fit.target);
    this.camera.near = clip.near;
    this.camera.far = clip.far;
    this.controls.minDistance = CAMERA_MIN_DISTANCE_M;
    this.controls.maxDistance = fit.maxDistance;
    this.applyPolarForViewMode();
    this.applyCameraSafety();
    this.camera.updateProjectionMatrix();
    this.environment?.setCityScale(bounds.diagonal, clip.far);
    this.updatePanSensitivity(true);
    this.controls.update();
    this.lastCamKey = cameraMotionKey(this.camera, this.controls.target);
    this.homePose = { position: fit.position.clone(), target: fit.target.clone() };
  }

  setShowTileBounds(on: boolean) {
    this.showTileBounds = on;
    this.tileDebugGroup.visible = on;
    if (on) this.syncTileDebugHelpers();
    this.requestRender();
  }

  getShowTileBounds() {
    return this.showTileBounds;
  }

  setWaterDebug(on: boolean) {
    this.waterDebug = on;
    this.refreshWaterGuard();
    this.requestRender();
  }

  getWaterDebug() {
    return this.waterDebug;
  }

  getRenderIsolation(): RenderIsolationState {
    return { ...this.isolation };
  }

  /** Dev diagnostic — proves whether washout is the coastal haze. Preset untouched. */
  setFogEnabled(on: boolean) {
    this.environment?.setFogEnabled(on);
    this.requestRender();
  }

  getFogEnabled(): boolean {
    return this.environment?.isFogEnabled() ?? true;
  }

  setRenderIsolation(patch: Partial<RenderIsolationState>) {
    this.isolation = { ...this.isolation, ...patch };
    if (this.isolation.baseModelOnly) {
      this.isolation.disableWater = true;
      this.isolation.disableOverlays = true;
    }
    this.applyIsolation();
    this.requestRender();
  }

  private syncAdaptiveClip() {
    if (!this.camera || !this.controls) return;
    const bounds = this.globalBounds ?? this.refreshGlobalBounds();
    const dist = this.camera.position.distanceTo(this.controls.target);
    const clip = computeAdaptiveCameraClip(bounds, dist, this.settings.cameraFarCap);
    if (Math.abs(this.camera.near - clip.near) < 0.25 && Math.abs(this.camera.far - clip.far) < 80) return;
    this.camera.near = clip.near;
    this.camera.far = clip.far;
    this.camera.updateProjectionMatrix();
  }

  private applyIsolation() {
    const iso = this.isolation;
    const hideOverlays = iso.baseModelOnly || iso.disableOverlays;
    const hideWater = iso.baseModelOnly || iso.disableWater;
    setSubtreeIsolatedHidden(this.tileDebugGroup, hideOverlays);
    setSubtreeIsolatedHidden(this.pickDebugGroup, hideOverlays);
    setSubtreeIsolatedHidden(this.geoMarkers.group, hideOverlays);
    setSubtreeIsolatedHidden(this.geoGrid.group, hideOverlays);
    setSubtreeIsolatedHidden(this.calMarkers.group, hideOverlays);
    hideWaterLikeMeshes(this.odessaCityRoot, hideWater, isWaterLikeMesh);
    if (iso.neutralMaterial) {
      if (!this.neutralMat) this.neutralMat = createNeutralDiagnosticMaterial();
      applyNeutralMaterialDiagnostic(this.odessaCityRoot, true, this.neutralMat);
    } else {
      applyNeutralMaterialDiagnostic(this.odessaCityRoot, false, this.neutralMat ?? createNeutralDiagnosticMaterial());
    }
  }

  /* ---------------- STEP 29.4 artifact isolation (dev only) ---------------- */

  getDebugView(): DebugViewState {
    return { ...this.debugView };
  }

  setDebugView(patch: Partial<DebugViewState>) {
    this.debugView = { ...this.debugView, ...patch };
    this.applyDebugView();
    this.requestRender();
  }

  private applyDebugView() {
    const dv = this.debugView;

    /* SOURCE CITY ONLY — every scene child except the GLB root is hidden. */
    if (dv.sourceCityOnly) {
      if (!this.savedSceneVis) {
        this.savedSceneVis = new Map();
        for (const child of this.scene.children) this.savedSceneVis.set(child, child.visible);
      }
      for (const child of this.scene.children) {
        child.visible =
          child === this.odessaCityRoot || child === this.debugAmbient || child === this.meshBoundsGroup;
      }
    } else if (this.savedSceneVis) {
      for (const [obj, v] of this.savedSceneVis) obj.visible = v;
      this.savedSceneVis = null;
    }

    const envRoot = this.scene.getObjectByName("odessaEnvironment");
    const envHidden = dv.environmentOff || dv.lightsNeutral || dv.sourceCityOnly;
    if (envRoot && !dv.sourceCityOnly) envRoot.visible = !envHidden;

    if (dv.environmentOff || dv.sourceCityOnly) {
      if (this.savedFog === undefined) {
        this.savedFog = this.scene.fog;
        this.savedBackground = this.scene.background;
      }
      this.scene.fog = null;
      this.scene.background = new THREE.Color(0x14181d);
    } else if (this.savedFog !== undefined) {
      this.scene.fog = this.savedFog;
      this.scene.background = this.savedBackground ?? null;
      this.savedFog = undefined;
      this.savedBackground = undefined;
    }

    const wantAmbient = dv.lightsNeutral || dv.sourceCityOnly || dv.environmentOff;
    if (wantAmbient && !this.debugAmbient) {
      this.debugAmbient = new THREE.AmbientLight(0xffffff, 1.15);
      this.debugAmbient.name = "odessaDebugAmbient";
      this.scene.add(this.debugAmbient);
    }
    if (this.debugAmbient) this.debugAmbient.visible = wantAmbient;

    if (dv.depthDebug) {
      if (!this.depthDebugMat) this.depthDebugMat = createDepthDebugMaterial();
      this.scene.overrideMaterial = this.depthDebugMat;
    } else if (this.scene.overrideMaterial === this.depthDebugMat) {
      this.scene.overrideMaterial = null;
    }

    this.matOverride.apply(this.odessaCityRoot, dv);
    setBasePlaneHidden(this.odessaCityRoot, dv.hideBasePlane);

    /* STEP 29.6/29.7 — spike-suspect visibility: SHOW ONLY or HIDE. */
    if (dv.spikesOnly || dv.hideSpikes) {
      if (!this.savedSpikeVis) {
        this.savedSpikeVis = new Map();
        this.odessaCityRoot.traverse((obj) => {
          const mesh = obj as THREE.Mesh;
          if (mesh.isMesh) this.savedSpikeVis!.set(mesh, mesh.visible);
        });
      }
      this.odessaCityRoot.traverse((obj) => {
        const mesh = obj as THREE.Mesh;
        if (!mesh.isMesh) return;
        const suspect = !!mesh.userData.odessaSpikeSuspect;
        mesh.visible = dv.spikesOnly ? suspect : this.savedSpikeVis!.get(mesh) !== false && !suspect;
      });
    } else if (this.savedSpikeVis) {
      for (const [mesh, v] of this.savedSpikeVis) mesh.visible = v;
      this.savedSpikeVis = null;
    }

    /* STEP 29.7 — COLOR SPIKE SUSPECTS RED. */
    this.spikeHighlighter.apply(this.odessaCityRoot, dv.colorSpikesRed);

    /* STEP 29.8 — ORIGINAL / REPAIRED A/B, then the component color overlay
     * (overlay reads the current per-vertex classes; both idempotent). */
    if (this.verticalRecoveryMode !== "off") {
      if (dv.componentRepairOff) this.componentOverlay.restore();
      setSceneComponentRepairEnabled(this.odessaCityRoot, !dv.componentRepairOff);
    }
    this.componentOverlay.apply(this.odessaCityRoot, dv.componentColors && !dv.componentRepairOff);

    if (dv.showMeshBounds) {
      if (!this.meshBoundsGroup.parent) {
        this.meshBoundsGroup.name = "odessaMeshBoundsDebug";
        this.scene.add(this.meshBoundsGroup);
      }
      this.meshBoundsGroup.clear();
      for (const node of this.assetNodes.values()) {
        const box = new THREE.Box3().setFromObject(node);
        if (!box.isEmpty()) this.meshBoundsGroup.add(new THREE.Box3Helper(box, new THREE.Color(0xffaa00)));
      }
      this.meshBoundsGroup.visible = true;
    } else {
      this.meshBoundsGroup.clear();
      this.meshBoundsGroup.visible = false;
    }

    if (dv.tightClip && this.camera && this.controls) {
      const bounds = this.globalBounds ?? this.refreshGlobalBounds();
      const dist = this.camera.position.distanceTo(this.controls.target);
      this.camera.near = Math.max(this.camera.near, dist / 60);
      this.camera.far = Math.min(this.camera.far, dist + bounds.diagonal * 1.2);
      this.camera.updateProjectionMatrix();
    } else if (!dv.tightClip) {
      this.syncAdaptiveClip();
    }
  }

  /** STEP 29.6 dev three-way comparison: OFF / SELECTIVE / 29.5 LEGACY.
   * Reverts every applied correction (original node TRS is untouched) and
   * re-applies the requested mode to the loaded city. Dev panel only. */
  setVerticalRecoveryMode(mode: VerticalRecoveryMode) {
    /* Metric package: geometry is already correct — recovery stays off. */
    if (!activeOdessaPackage().runtimeGeometryRecovery) return;
    if (mode === this.verticalRecoveryMode) return;
    this.verticalRecoveryMode = mode;
    this.componentOverlay.restore();
    revertOdessaVerticalScaleRecovery(this.odessaCityRoot);
    if (mode !== "off") applyOdessaVerticalScaleRecovery(this.odessaCityRoot, mode);
    setSceneComponentRepairEnabled(this.odessaCityRoot, mode !== "off" && !this.debugView.componentRepairOff);
    this.applyDebugView();
    this.refreshGlobalBounds();
    this.syncAdaptiveClip();
    this.requestRender();
  }

  getVerticalRecoveryMode(): VerticalRecoveryMode {
    return this.verticalRecoveryMode;
  }

  /** STEP 29.7 Phase 3 — EXPORT SPIKE REPORT JSON over the ACTUAL rendered
   * scene (final matrixWorld). `full` includes every mesh, not only suspects. */
  exportSpikeReport(full = false): string {
    const rows = collectRuntimeSpikeReport(this.odessaCityRoot, full);
    const spikes = rows.filter((r) => r.runtimeSpike != null && r.visible);
    const report = {
      generatedAt: new Date().toISOString(),
      recoveryMode: this.verticalRecoveryMode,
      totalRows: rows.length,
      runtimeSpikeSuspects: spikes.length,
      spikeSuspectFlags: rows.filter((r) => r.spikeSuspect).length,
      mixedDomainMeshes: rows.filter((r) => r.mixedDomain).length,
      rows,
    };
    console.info(`[Odessa3D] runtime spike report: ${spikes.length} live spikes / ${rows.length} rows`);
    return JSON.stringify(report, null, 1);
  }

  /** Phase 4 — deterministic binary mesh isolation over the source city. */
  bisect(action: BisectAction | "ACTIVATE" | "DEACTIVATE"): BisectStatus {
    if (action === "ACTIVATE") this.bisector.activate(this.odessaCityRoot);
    else if (action === "DEACTIVATE") this.bisector.deactivate();
    else this.bisector.step(action);
    this.requestRender();
    return this.bisector.status();
  }

  getBisectStatus(): BisectStatus {
    return this.bisector.status();
  }

  /** Phase 3 — ALT/OPTION+click inspector. */
  inspectAtScreen(clientX: number, clientY: number): InspectorHit | null {
    if (!this.camera || !this.canvas) return null;
    const rect = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(
      ((clientX - rect.left) / Math.max(1, rect.width)) * 2 - 1,
      -((clientY - rect.top) / Math.max(1, rect.height)) * 2 + 1,
    );
    this.inspectRaycaster.setFromCamera(ndc, this.camera);
    const hits = this.inspectRaycaster.intersectObject(this.odessaCityRoot, true);
    const hit = hits.find((h) => (h.object as THREE.Mesh).isMesh && h.object.visible);
    if (!hit) return null;
    const info = describeIntersection(hit);
    this.lastInspection = info;
    console.info(
      "[Odessa3D inspector]\n" +
        `OBJECT: ${info.object}\nPARENT: ${info.parent}\nMATERIAL: ${info.material}\n` +
        `GEOMETRY: ${info.geometry}\nWORLD POSITION: ${info.worldPosition.join(", ")}\n` +
        `FACE: ${info.faceIndex}\nBOUNDING BOX: ${JSON.stringify(info.boundingBox)}\n` +
        `DISTANCE: ${info.distance}\nBOX HEIGHT: ${info.meshBoxHeight}\nFOOTPRINT: ${info.meshFootprint}\n` +
        `DECAL RANK: ${info.decalRank}\n` +
        `VERTICAL RECOVERY: ${info.verticalRecovery ? JSON.stringify(info.verticalRecovery) : "not applied"}\n` +
        `SPIKE SUSPECT: ${info.spikeSuspect}\nMIXED DOMAIN: ${info.mixedDomain}\n` +
        `RAW GEOMETRY HEIGHT: ${info.transformChain.rawGeometryHeight}\n` +
        `OBJECT SCALE: ${info.transformChain.objectScale.join(", ")}\n` +
        `ANCESTOR SCALES: ${info.transformChain.ancestors.map((a) => `${a.name}[${a.scale.join(",")}]`).join(" → ") || "(none)"}\n` +
        `MATRIX WORLD: [${info.transformChain.matrixWorld.join(", ")}]\n` +
        `DETERMINANT: ${info.transformChain.determinant}\n` +
        `EXPECTED WORLD HEIGHT: ${info.transformChain.expectedWorldHeight ?? "n/a"}\n` +
        `ACTUAL WORLD HEIGHT: ${info.transformChain.actualWorldHeight ?? "n/a"}\n` +
        `CODE PATH: ${info.transformChain.codePath}\n` +
        `COMPONENT CLASS: ${info.componentRepair.hitClass ?? "n/a"}\n` +
        `COMPONENT REPAIR (mesh): ${info.componentRepair.meshTag ? JSON.stringify(info.componentRepair.meshTag) : "not a repair mesh"}\n` +
        `COMPONENT DETAIL: ${info.componentRepair.component ? JSON.stringify(info.componentRepair.component) : "n/a"}`,
    );
    this.requestRender();
    return info;
  }

  getLastInspection(): InspectorHit | null {
    return this.lastInspection;
  }

  setZoomTowardPointer(on: boolean) {
    this.zoomTowardPointer = on;
    if (this.controls) this.controls.zoomToCursor = on;
  }

  getZoomTowardPointer() {
    return this.zoomTowardPointer;
  }

  setLayerVisible(layerId: string, visible: boolean) {
    this.layers.setVisible(layerId, visible);
    const g = this.layerGroups.get(layerId);
    if (g) g.visible = visible;
    this.requestRender();
  }

  toggleLayer(layerId: string) {
    const on = this.layers.toggle(layerId);
    const g = this.layerGroups.get(layerId);
    if (g) g.visible = on;
    this.requestRender();
    return on;
  }

  layerList() {
    return this.layers.list();
  }

  handleClick(clientX: number, clientY: number) {
    if (this.calibrationPicking) {
      if (!isClickGesture(this.pointerDown, { x: clientX, y: clientY }, this.clickMoved)) return;
      const now = performance.now();
      if (now - this.lastClickMs < 350) return;
      this.lastClickMs = now;
      const world = this.raycastWorldHit(clientX, clientY);
      if (!world) return;
      this.lastClickWorld = world;
      this.callbacks.onCalibrationPick?.(world);
      return;
    }
    if (!this.interactionEnabled) return;
    if (!isClickGesture(this.pointerDown, { x: clientX, y: clientY }, this.clickMoved)) return;
    const now = performance.now();
    if (now - this.lastClickMs < 350) return;
    this.lastClickMs = now;

    const hit = this.raycastPick(clientX, clientY);
    if (!hit) {
      this.lastClickWorld = null;
      this.clearSelection();
      return;
    }
    this.lastClickWorld = { x: hit.hit.point.x, y: hit.hit.point.y, z: hit.hit.point.z };
    this.selectPickId(hit.entity.pickId);
  }

  setInteractionEnabled(on: boolean) {
    this.interactionEnabled = on;
    if (!on) this.setHoveredPickId(null);
    this.emitInteraction();
  }

  isInteractionEnabled(): boolean {
    return this.interactionEnabled;
  }

  setShowGeoGrid(on: boolean) {
    this.geoGrid.setEnabled(on);
    const cal = this.geoRef.calibration();
    if (on && cal && this.camera && this.controls) {
      const dist = this.camera.position.distanceTo(this.controls.target);
      const spacing = gridSpacingForDistance(dist, cal.metersPerWorldUnit);
      this.geoGrid.rebuild(cal, spacing);
    } else {
      this.geoGrid.rebuild(null);
    }
    this.requestRender();
  }

  copyClickCoordinates(): string | null {
    const geo = this.lastClickWorld ? this.geoRef.toGeo(this.lastClickWorld) : null;
    return geo ? formatLatLon(geo) : null;
  }

  modelFingerprint(): string | null {
    return this.manifest
      ? odessaModelFingerprint({ ...this.manifest, packageId: activeOdessaPackage().id })
      : null;
  }

  georeferenceStatus() {
    return this.geoRef.status();
  }

  reloadGeoreference() {
    if (!this.manifest) return;
    this.geoRef.resolve({
      originLat: this.manifest.geoTransform.originLat,
      originLng: this.manifest.geoTransform.originLng,
      calibrated: this.manifest.geoTransform.calibrated,
      loadPersisted: true,
      currentFingerprint: odessaModelFingerprint(this.manifest),
    });
    this.syncGeoWorldBox();
    this.syncGeoOverlays();
    this.emitInteraction();
  }

  setCalibrationPicking(on: boolean) {
    this.calibrationPicking = on;
    if (on) this.setHoveredPickId(null);
  }

  isCalibrationPicking(): boolean {
    return this.calibrationPicking;
  }

  setCalibrationMarkers(
    points: Array<{ id: CalibrationSlotId | "CHECK"; world: LocalWorldCoordinate }>,
    visible: boolean,
  ) {
    this.calMarkers.sync(points, visible);
    this.requestRender();
  }

  modelRootTransform() {
    const r = this.odessaCityRoot;
    return {
      position: { x: r.position.x, y: r.position.y, z: r.position.z },
      rotation: { x: r.rotation.x, y: r.rotation.y, z: r.rotation.z },
      scale: { x: r.scale.x, y: r.scale.y, z: r.scale.z },
    };
  }

  calibrationCameraPreset(
    kind: "top" | "tilt45" | "A" | "B" | "C",
    points: Partial<Record<CalibrationSlotId, LocalWorldCoordinate | null>>,
  ) {
    if (!this.camera || !this.controls) return;
    const bounds = this.globalBounds ?? this.refreshGlobalBounds();
    const center = bounds.center;
    let position: THREE.Vector3;
    let target: THREE.Vector3;
    if (kind === "top") {
      target = center.clone();
      position = new THREE.Vector3(center.x, center.y + Math.max(bounds.diagonal * 0.85, 200), center.z + 1);
    } else if (kind === "tilt45") {
      const dist = Math.max(bounds.diagonal * 0.55, 180);
      const elev = dist * Math.sin(Math.PI / 4);
      const horiz = dist * Math.cos(Math.PI / 4);
      target = center.clone();
      position = new THREE.Vector3(center.x + horiz * 0.7, center.y + elev, center.z + horiz * 0.7);
    } else {
      const p = points[kind];
      if (!p) return;
      const focused = focusCameraOnPoint(
        new THREE.Vector3(p.x, p.y, p.z),
        this.camera,
        this.controls.target,
        0.08,
        bounds.diagonal,
      );
      position = focused.position;
      target = focused.target;
    }
    const clip = computeCameraClipRange(bounds, this.settings.cameraFarCap);
    this.camera.near = clip.near;
    this.camera.far = clip.far;
    this.camera.updateProjectionMatrix();
    this.focusTween = createFocusTween(
      performance.now(),
      this.camera.position,
      position,
      this.controls.target,
      target,
    );
    this.updatePanSensitivity(true);
    this.requestRender();
  }

  private raycastWorldHit(clientX: number, clientY: number): LocalWorldCoordinate | null {
    if (!this.camera || !this.canvas) return null;
    if (!pointerToNdc(clientX, clientY, this.canvas, this.pointer)) return null;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObject(this.odessaCityRoot, true);
    for (const hit of hits) {
      let node: THREE.Object3D | null = hit.object;
      let helper = false;
      while (node) {
        if (node.userData?.odessaHighlightHelper) {
          helper = true;
          break;
        }
        node = node.parent;
      }
      if (helper) continue;
      const pt = hit.point;
      return { x: pt.x, y: pt.y, z: pt.z };
    }
    return null;
  }

  private syncGeoWorldBox() {
    const bounds = this.globalBounds ?? this.refreshGlobalBounds();
    this.geoRef.setWorldBox({
      min: { x: bounds.box.min.x, y: bounds.box.min.y, z: bounds.box.min.z },
      max: { x: bounds.box.max.x, y: bounds.box.max.y, z: bounds.box.max.z },
    });
  }

  private syncGeoOverlays() {
    const enabled = this.geoRef.overlaysOn();
    this.geoMarkers.sync(this.geoRef.cached(), {
      enabled,
      selectedEntityId: citySelection.getSelectedId(),
      classify: (id) => {
        const row = this.geoRef.cached().find((r) => r.anchor.id === id);
        return row ? this.geoRef.classifyAnchor(row.anchor.coordinate) : null;
      },
    });
    if (this.geoGrid.isEnabled()) {
      const cal = this.geoRef.calibration();
      this.geoGrid.rebuild(enabled ? cal : null);
    }
    this.requestRender();
  }

  setShowSelectionBounds(on: boolean) {
    this.showSelectionBounds = on;
    this.pickDebugGroup.visible = on;
    this.highlighter.setShowBounds(on);
    if (on && this.selectedPickId) {
      const obj = this.pickRegistry.getObject(this.selectedPickId);
      this.highlighter.setSelected(obj && (obj as THREE.Mesh).isMesh ? (obj as THREE.Mesh) : null);
    }
    this.requestRender();
  }

  clearSelection() {
    this.selectedPickId = null;
    this.selectedActive = false;
    this.lastClickWorld = null;
    this.highlighter.setSelected(null);
    citySelection.select(null);
    geoSelectionBridge.clear();
    this.callbacks.onSelect?.(null);
    this.emitInteraction();
    this.requestRender();
  }

  focusSelected() {
    if (this.selectedPickId) this.focusPickId(this.selectedPickId);
  }

  interactionSnapshot(): InteractionSnapshot {
    const pickable = this.selectedPickId ? this.pickRegistry.get(this.selectedPickId) ?? null : null;
    const asset = pickable ? this.loader.registry.get(pickable.assetId) : undefined;
    const binding = pickable
      ? bindPickableEntity(pickable, {
          entityRefs: asset?.entityRefs,
          manifestEntityRef: asset?.entityRefs?.[0],
        })
      : null;
    return {
      hoveredPickId: this.hoveredPickId,
      selectedPickId: this.selectedPickId,
      selectedActive: this.selectedActive && !!this.pickRegistry.getObject(this.selectedPickId ?? ""),
      pickable,
      binding,
      interactionEnabled: this.interactionEnabled,
      clickWorld: this.lastClickWorld,
      clickGeo: this.geoRef.overlaysOn() && this.lastClickWorld ? this.geoRef.toGeo(this.lastClickWorld) : null,
      objectGeo:
        this.geoRef.overlaysOn() && pickable?.position ? this.geoRef.toGeo(pickable.position) : null,
      georeferenceReady: this.geoRef.overlaysOn(),
    };
  }

  private selectPickId(pickId: string) {
    const entity = this.pickRegistry.get(pickId);
    const obj = this.pickRegistry.getObject(pickId);
    if (!entity || !obj) return;
    this.selectedPickId = pickId;
    this.selectedActive = true;
    this.highlighter.applyIds(
      (id) => this.pickRegistry.getObject(id),
      this.hoveredPickId,
      this.selectedPickId,
    );
    const asset = this.loader.registry.get(entity.assetId);
    const binding = bindPickableEntity(entity, {
      entityRefs: asset?.entityRefs,
      manifestEntityRef: asset?.entityRefs?.[0],
    });
    if (binding.status === "BOUND" && binding.enterpriseEntityId) {
      citySelection.select(binding.enterpriseEntityId);
      this.callbacks.onSelect?.(binding.enterpriseEntityId);
      geoSelectionBridge.setFrom3d(
        binding.enterpriseEntityId,
        this.lastClickWorld ? this.geoRef.toGeo(this.lastClickWorld) : null,
      );
    } else {
      citySelection.select(null);
      this.callbacks.onSelect?.(null);
      geoSelectionBridge.setFrom3d(null, this.lastClickWorld ? this.geoRef.toGeo(this.lastClickWorld) : null);
    }
    this.emitInteraction();
    this.requestRender();
  }

  private setHoveredPickId(pickId: string | null) {
    if (this.hoveredPickId === pickId) return;
    this.hoveredPickId = pickId;
    this.highlighter.applyIds(
      (id) => this.pickRegistry.getObject(id),
      this.hoveredPickId,
      this.selectedPickId,
    );
    this.requestRender();
  }

  hoverWorld(): { x: number; y: number; z: number } | null {
    return this.lastHoverWorld;
  }

  private maybeHoverRaycast(clientX: number, clientY: number, now: number) {
    if (this.calibrationPicking) {
      if (now - this.lastHoverRaycastMs < HOVER_RAYCAST_INTERVAL_MS) return;
      this.lastHoverRaycastMs = now;
      this.lastHoverWorld = this.raycastWorldHit(clientX, clientY);
      return;
    }
    if (!this.interactionEnabled || !this.pointerInside) return;
    if (this.interaction.getMode() === "INTERACTING") return;
    if (now - this.lastHoverRaycastMs < HOVER_RAYCAST_INTERVAL_MS) return;
    this.lastHoverRaycastMs = now;
    const hit = this.raycastPick(clientX, clientY);
    this.setHoveredPickId(hit?.entity.pickId ?? null);
  }

  private focusPickId(pickId: string) {
    if (!this.camera || !this.controls) return;
    const obj = this.pickRegistry.getObject(pickId);
    if (!obj) return;
    const bounds = this.globalBounds ?? this.refreshGlobalBounds();
    const pose = focusPoseForObject(obj, this.camera, bounds);
    const clip = computeCameraClipRange(bounds, this.settings.cameraFarCap);
    this.camera.near = clip.near;
    this.camera.far = clip.far;
    this.camera.updateProjectionMatrix();
    this.focusTween = createFocusTween(
      performance.now(),
      this.camera.position,
      pose.position,
      this.controls.target,
      pose.target,
      FOCUS_TWEEN_MS,
    );
    this.updatePanSensitivity(true);
    this.requestRender();
  }

  private emitInteraction() {
    this.callbacks.onInteraction?.(this.interactionSnapshot());
  }

  private refreshSceneAudit() {
    this.sceneAudit = auditSceneGraph(this.odessaCityRoot);
  }

  private restoreSelectionAfterRegister(assetId: string) {
    if (this.selectedPickId) {
      const ent = this.pickRegistry.get(this.selectedPickId);
      if (ent?.assetId === assetId && this.pickRegistry.getObject(this.selectedPickId)) {
        this.selectedActive = true;
        this.highlighter.applyIds(
          (id) => this.pickRegistry.getObject(id),
          this.hoveredPickId,
          this.selectedPickId,
        );
        this.emitInteraction();
        this.requestRender();
        return;
      }
      if (ent?.assetId === assetId) {
        this.selectedActive = false;
        this.emitInteraction();
      }
    }
  }

  private raycastPick(clientX: number, clientY: number): { entity: NonNullable<ReturnType<PickRegistry["get"]>>; hit: THREE.Intersection } | null {
    if (!this.camera || !this.canvas) return null;
    if (!pointerToNdc(clientX, clientY, this.canvas, this.pointer)) return null;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const candidates = this.pickRegistry.candidatesForRay(this.raycaster.ray);
    const t0 = performance.now();
    const hits = candidates.length ? this.raycaster.intersectObjects(candidates, false) : [];
    recordRaycast(this.raycastMeter, t0, performance.now() - t0, hits.length, candidates.length);
    const top = hits[0];
    if (!top) return null;
    const entity = this.pickRegistry.resolveFromObject(top.object);
    if (!entity) return null;
    return { entity, hit: top };
  }

  refreshGlobalBounds(): GlobalCityBounds {
    this.globalBounds = computeGlobalCityBounds(this.assetNodes.values(), this.manifest?.cityBounds);
    return this.globalBounds;
  }

  diagnostics(): OdessaDevDiagnostics {
    const c = this.loader.registry.counts();
    const p = this.loader.progress();
    const bounds = this.refreshGlobalBounds();
    const center = bounds.center;
    const size = bounds.size;
    let triangleCount = 0;
    let meshCount = 0;
    for (const obj of this.assetNodes.values()) {
      if (!obj.visible) continue;
      obj.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          meshCount += 1;
          const mesh = child as THREE.Mesh;
          const geo = mesh.geometry;
          if (geo?.index) triangleCount += geo.index.count / 3;
          else if (geo?.attributes.position) triangleCount += geo.attributes.position.count / 3;
        }
      });
    }
    const camDist =
      this.camera && this.controls ? this.camera.position.distanceTo(this.controls.target) : 0;

    return {
      assetPackage: activeOdessaPackage().id,
      loadedAssets: c.loaded,
      queuedAssets: c.queued,
      failedAssets: c.failed,
      realGlbLoaded: c.realGlb,
      visibleTiles: [...this.assetNodes.values()].filter((n) => n.visible).length,
      triangleCount: Math.round(triangleCount),
      meshCount,
      camera: this.camera
        ? {
            x: +this.camera.position.x.toFixed(1),
            y: +this.camera.position.y.toFixed(1),
            z: +this.camera.position.z.toFixed(1),
          }
        : { x: 0, y: 0, z: 0 },
      lookAt: this.controls
        ? {
            x: +this.controls.target.x.toFixed(1),
            y: +this.controls.target.y.toFixed(1),
            z: +this.controls.target.z.toFixed(1),
          }
        : undefined,
      cameraDistance: +camDist.toFixed(1),
      selectedEntityId: citySelection.getSelectedId(),
      activeLayers: this.layers.activeLayerIds(),
      quality: this.settings.profile,
      tilesActive: this.stream?.activeTileIds() ?? [],
      cityBounds: {
        min: {
          x: +bounds.box.min.x.toFixed(1),
          y: +bounds.box.min.y.toFixed(1),
          z: +bounds.box.min.z.toFixed(1),
        },
        max: {
          x: +bounds.box.max.x.toFixed(1),
          y: +bounds.box.max.y.toFixed(1),
          z: +bounds.box.max.z.toFixed(1),
        },
        center: { x: +center.x.toFixed(1), y: +center.y.toFixed(1), z: +center.z.toFixed(1) },
        size: { x: +size.x.toFixed(1), y: +size.y.toFixed(1), z: +size.z.toFixed(1) },
      },
      cityDiagonal: +bounds.diagonal.toFixed(1),
      axisExtents: { x: +size.x.toFixed(1), y: +size.y.toFixed(1), z: +size.z.toFixed(1) },
      sourceMode: p.sourceMode,
      loadingAssetId: p.loadingAssetId,
      materialAudit: this.materialAudit ?? undefined,
      odessaReady: this.bootState === "READY",
      bootState: this.bootState,
      panSpeed: this.controls ? +this.controls.panSpeed.toFixed(3) : BASE_PAN_SPEED,
      cameraNear: this.camera ? +this.camera.near.toFixed(3) : undefined,
      cameraFar: this.camera ? +this.camera.far.toFixed(1) : undefined,
      zoomTowardPointer: this.zoomTowardPointer,
      screenSpacePanning: CITY_SCREEN_SPACE_PANNING,
      runtimeMode: this.interaction.getMode(),
      interaction: this.interactionDiagnostics(),
      sceneAudit: {
        object3dCount: this.sceneAudit.object3dCount,
        meshCount: this.sceneAudit.meshCount,
        namedMeshCount: this.sceneAudit.namedMeshCount,
        unnamedMeshCount: this.sceneAudit.unnamedMeshCount,
        materialsReused: this.sceneAudit.materialsReused,
        uniqueMaterials: this.sceneAudit.uniqueMaterials,
        meshesWithUserData: this.sceneAudit.meshesWithUserData,
        meshesWithAssetId: this.sceneAudit.meshesWithAssetId,
      },
      georeference: this.geoRef.diagnostics({
        selectedWorld: this.lastClickWorld,
        cameraWorld: this.camera
          ? { x: this.camera.position.x, y: this.camera.position.y, z: this.camera.position.z }
          : null,
        cameraTargetWorld: this.controls
          ? { x: this.controls.target.x, y: this.controls.target.y, z: this.controls.target.z }
          : null,
      }),
      renderStability: (() => {
        const stats = collectRenderStabilityStats({
          scene: this.scene,
          cityRoot: this.odessaCityRoot,
          camera: this.camera,
          renderer: this.renderer,
        });
        return { ...stats, isolation: { ...this.isolation } };
      })(),
      lighting: (() => {
        const env = this.environment?.diagnostics();
        const audit = collectLightingColorAudit(this.odessaCityRoot);
        const fogDensity = env?.fogDensity ?? 0;
        return {
          outputColorSpace: this.renderer ? String(this.renderer.outputColorSpace) : "none",
          toneMapping: this.renderer ? toneMappingName(this.renderer.toneMapping) : "none",
          toneMappingExposure: this.renderer ? +this.renderer.toneMappingExposure.toFixed(3) : 0,
          sunIntensity: env?.sunIntensity ?? 0,
          hemiIntensity: env?.hemiIntensity ?? 0,
          fogEnabled: env?.fogEnabled ?? true,
          fogDensity: +fogDensity.toFixed(6),
          fogColor: env?.fogColor ?? "none",
          fogMixAtCameraPct: +(fogMixAtDepth(fogDensity, camDist) * 100).toFixed(1),
          fogMixAtDiagonalPct: +(fogMixAtDepth(fogDensity, bounds.diagonal) * 100).toFixed(1),
          emissiveActiveMaterials: audit.emissiveActiveMaterials,
          metalTexturedMaterials: audit.metalTexturedMaterials,
          srgbDataMapViolations: audit.srgbDataMapViolations,
          vertexColorMeshes: audit.vertexColorMeshes,
          transparentTexturedMaterials: audit.transparentTexturedMaterials,
        };
      })(),
      artifactDebug: (() => {
        let decalMeshes = 0;
        let verticalRecovered = 0;
        let spikeSuspects = 0;
        let mixedDomain = 0;
        const compRepair = {
          meshes: 0,
          totalComponents: 0,
          repairedComponents: 0,
          sourceAnomalies: 0,
          revertedComponents: 0,
          modifiedVertices: 0,
        };
        this.odessaCityRoot.traverse((obj) => {
          if (!(obj as THREE.Mesh).isMesh) return;
          if (obj.userData.odessaDecalApplied != null) decalMeshes += 1;
          if (obj.userData.odessaVerticalRecovery) verticalRecovered += 1;
          if (obj.userData.odessaSpikeSuspect) spikeSuspects += 1;
          if (obj.userData.odessaMixedDomain) mixedDomain += 1;
          const tag = obj.userData.odessaComponentRepair as ComponentRepairTag | undefined;
          if (tag?.applied) {
            compRepair.meshes += 1;
            compRepair.totalComponents += tag.totalComponents;
            compRepair.repairedComponents += tag.repairedComponents;
            compRepair.sourceAnomalies += tag.miniatureComponents;
            compRepair.revertedComponents += tag.revertedComponents;
            compRepair.modifiedVertices += tag.modifiedVertices;
          }
        });
        return {
          debugView: { ...this.debugView },
          bisect: this.bisector.status(),
          cameraAltitude: this.camera ? cameraAltitudeReport(this.camera, bounds.box) : null,
          decalMeshes,
          verticalRecovery: {
            mode: this.verticalRecoveryMode,
            factor: ODESSA_VERTICAL_RECOVERY_FACTOR,
            correctedMeshes: verticalRecovered,
            spikeSuspects,
            mixedDomainMeshes: mixedDomain,
            cityHeight: +(bounds.box.max.y - bounds.box.min.y).toFixed(1),
          },
          componentRepair: compRepair,
          lastInspection: this.lastInspection,
        };
      })(),
      waterAudit: this.waterAudit
        ? {
            meshCount: this.waterAudit.meshCount,
            kept: this.waterAudit.kept,
            duplicatesHidden: this.waterAudit.duplicatesHidden,
            debug: this.waterDebug,
            logarithmicDepthBuffer: LOGARITHMIC_DEPTH_BUFFER,
            surfaces: this.waterAudit.records.map((r) => ({
              name: r.name,
              category: r.category,
              minY: +r.minY.toFixed(4),
              maxY: +r.maxY.toFixed(4),
              materialType: r.materialType,
              transparent: r.transparent,
              depthWrite: r.depthWrite,
              side: r.side,
              renderOrder: r.renderOrder,
              hiddenAsDuplicate: r.hiddenAsDuplicate,
            })),
          }
        : undefined,
    };
  }

  private interactionDiagnostics() {
    const counts = bindingCounts(this.pickRegistry.list());
    return {
      pickables: this.pickRegistry.size(),
      hovered: this.hoveredPickId,
      selected: this.selectedPickId,
      selectedActive: this.selectedActive && !!this.pickRegistry.getObject(this.selectedPickId ?? ""),
      raycastsPerSec: this.raycastMeter.perSec,
      lastRaycastMs: +this.raycastMeter.lastMs.toFixed(2),
      candidates: this.raycastMeter.lastCandidates,
      hits: this.raycastMeter.lastHits,
      boundEntities: counts.bound,
      unboundEntities: counts.unbound,
      ambiguousEntities: counts.ambiguous,
      registrySize: this.pickRegistry.size(),
      materialClones: this.highlighter.materialCloneCount(),
      interactionEnabled: this.interactionEnabled,
      showSelectionBounds: this.showSelectionBounds,
    };
  }

  getInitError() {
    return this.initError;
  }

  getRenderLoopActive() {
    return this.renderLoop?.isRunning ?? false;
  }

  private syncTileDebugHelpers() {
    for (const [id, node] of this.assetNodes.entries()) {
      if (this.tileHelpers.has(id)) continue;
      const box = tileBoxFromObject(node);
      const helper = new THREE.Box3Helper(box, new THREE.Color(0x00ff88));
      helper.name = `debug_${id}`;
      this.tileDebugGroup.add(helper);
      this.tileHelpers.set(id, helper);
    }
    for (const [id, helper] of [...this.tileHelpers.entries()]) {
      if (!this.assetNodes.has(id)) {
        this.tileDebugGroup.remove(helper);
        this.tileHelpers.delete(id);
      }
    }
  }

  private emitHudProgress(base?: LoadingProgress) {
    const p = base ?? this.loader.progress();
    this.callbacks.onProgress?.({
      ...p,
      activeCount: this.assetNodes.size,
      bootState: this.bootState,
      currentAssetId: p.loadingAssetId ?? this.lastActivatedId,
    });
  }

  private updateBootState() {
    const c = this.loader.registry.counts();
    const active = this.activator.activatedCount();
    const next = resolveBootState({ total: c.total, failed: c.failed, active });
    const prev = this.bootState;
    this.bootState = next;
    if (c.total > 0 && active >= Math.ceil(c.total * 0.5)) this.profiler.markHalf();
    if (next === "READY" && prev !== "READY") {
      this.profiler.markReady();
      if (import.meta.env.DEV) {
        console.info("[Odessa3D] first-load KPIs", this.profiler.snapshot());
      }
    }
  }

  private ingestParsedAssets() {
    for (const asset of this.loader.registry.list()) {
      if (asset.status !== "loaded" || !asset.object3D || asset.source !== "REAL_GLB") continue;
      if (asset.lifecycle === "active" || asset.lifecycle === "hidden") continue;
      if (this.assetNodes.has(asset.id) || this.activator.has(asset.id)) continue;
      const layerId = asset.layerId || "city";
      if (!this.layers.isVisible(layerId)) continue;
      if (!this.activator.ingest(asset)) continue;
      const t = asset.timings;
      if (t?.parseMs != null && !this.recordedParse.has(asset.id)) {
        this.recordedParse.add(asset.id);
        this.profiler.recordParse({
          id: asset.id,
          url: asset.url,
          sizeMb: asset.sizeMb ?? 0,
          fetchMs: t.fetchMs ?? 0,
          parseMs: t.parseMs,
          triangleCount: asset.triangleCount ?? 0,
          objectCount: asset.objectCount ?? 0,
          heavyClass: asset.heavyClass ?? "MEDIUM",
        });
      }
    }
  }

  private activateParsedAssets(now: number): boolean {
    this.ingestParsedAssets();
    let changed = this.reapUnloadedAssets();

    if (this.camera && this.controls && this.activator.pendingCount() > 0) {
      this.camera.updateMatrixWorld();
      this.scratchProj.multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse);
      this.scratchFrustum.setFromProjectionMatrix(this.scratchProj);
      const priority = new Set(this.manifest?.priorityTiles || []);
      const n = this.activator.tick(
        {
          now,
          mode: this.interaction.getMode(),
          fps: this.lastFps,
          camera: this.camera,
          target: this.controls.target,
          frustum: this.scratchFrustum,
          priorityIds: priority,
          enableShadows: this.settings.enableShadows,
          maxAnisotropy: this.appliedAnisotropy,
          environmentQuality: resolveEnvironmentQuality(this.settings.profile),
          fovYDeg: this.camera instanceof THREE.PerspectiveCamera ? this.camera.fov : 50,
          viewportHeight: this.lastResize.h || 520,
          nowMs: now,
        },
        (info) => this.attachActivated(info),
      );
      if (n > 0) {
        this.refreshWaterGuard();
        this.updateBootState();
        this.emitHudProgress();
        changed = true;
      }
    } else if (this.activator.pendingCount() === 0 && this.assetNodes.size > 0) {
      this.updateBootState();
    }
    return changed;
  }

  private attachActivated(info: ActivatorAttachContext) {
    const { asset, root } = info;
    const layerId = asset.layerId || "city";
    const group = this.layerGroups.get(layerId);
    if (!group) return;
    const t0 = performance.now();
    this.materialShare.applyToRoot(root);
    const cached = getCachedCenter(asset.id);
    if (cached) {
      this.assetCenters.set(asset.id, new THREE.Vector3(cached.x, cached.y, cached.z));
    } else {
      const box = new THREE.Box3().setFromObject(root);
      const center = box.getCenter(new THREE.Vector3());
      this.assetCenters.set(asset.id, center);
      cacheMeasuredBounds(asset.id, {
        minX: box.min.x,
        maxX: box.max.x,
        minY: box.min.y,
        maxY: box.max.y,
        minZ: box.min.z,
        maxZ: box.max.z,
      });
    }
    this.loader.registry.update(asset.id, {
      lifecycle: "active",
      triangleCount: info.triangleCount,
      objectCount: info.objectCount,
      heavyClass: info.heavyClass,
      timings: { ...asset.timings, prepMs: info.prepMs, attachMs: performance.now() - t0 },
    });
    group.add(root);
    this.assetNodes.set(asset.id, root);
    this.assetVisibility.set(asset.id, true);
    this.lastActivatedId = asset.id;
    this.pickRegistry.registerAsset({
      assetId: asset.id,
      root,
      layerId,
      entityRefs: asset.entityRefs,
      manifestEntityRef: asset.entityRefs?.[0],
    });
    this.restoreSelectionAfterRegister(asset.id);
    this.refreshSceneAudit();
    this.profiler.recordPrep(asset.id, info.prepMs);
    this.profiler.recordAttach(asset.id, performance.now() - t0);
    this.loader.recordPrep(asset.id, info.prepMs);
    this.loader.recordAttach(asset.id, performance.now() - t0);
    if (this.showTileBounds) this.syncTileDebugHelpers();
    this.applyIsolation();
  }

  private reapUnloadedAssets(): boolean {
    let changed = false;
    for (const [assetId, node] of [...this.assetNodes.entries()]) {
      const asset = this.loader.registry.get(assetId);
      if (asset && asset.status === "unloaded") {
        this.activator.discard(assetId);
        const pickables = this.pickRegistry.list().filter((p) => p.assetId === assetId);
        this.highlighter.releaseAsset(assetId, pickables);
        if (this.selectedPickId && pickables.some((p) => p.pickId === this.selectedPickId)) {
          this.selectedActive = false;
          this.highlighter.setSelected(null);
          this.emitInteraction();
        }
        if (this.hoveredPickId && pickables.some((p) => p.pickId === this.hoveredPickId)) {
          this.hoveredPickId = null;
        }
        this.pickRegistry.unregisterAsset(assetId);
        node.parent?.remove(node);
        disposeObject3D(node);
        this.assetNodes.delete(assetId);
        this.assetVisibility.delete(assetId);
        this.assetCenters.delete(assetId);
        this.refreshSceneAudit();
        changed = true;
      }
    }
    for (const asset of this.loader.registry.list()) {
      if (asset.status === "unloaded" && this.activator.has(asset.id)) {
        this.activator.discard(asset.id);
        changed = true;
      }
    }
    return changed;
  }

  private refreshWaterGuard() {
    if (this.assetNodes.size === 0) {
      this.waterAudit = null;
      this.environment?.syncSeaFromRoots([]);
      return;
    }
    this.waterAudit = applyWaterSurfaceGuard(this.assetNodes.values(), { debug: this.waterDebug });
    this.environment?.syncSeaFromRoots(this.assetNodes.values());
  }

  dispose() {
    this.disposed = true;
    this.mountPhase = "idle";
    this.renderLoop?.dispose();
    this.renderLoop = null;
    this.resizeObserver?.disconnect();
    this.resizeObserver = null;
    window.removeEventListener("resize", this.onWindowResize);
    this.controls?.removeEventListener("change", this.onControlsChange);
    this.controls?.removeEventListener("start", this.onControlsStart);
    this.controls?.removeEventListener("end", this.onControlsEnd);
    this.canvas?.removeEventListener("pointerdown", this.syncOrbitModifier, true);
    this.canvas?.removeEventListener("pointerdown", this.onPointerDown);
    this.canvas?.removeEventListener("pointermove", this.onPointerMove);
    this.canvas?.removeEventListener("pointerup", this.onPointerUp);
    this.canvas?.removeEventListener("pointerup", this.restoreOrbitButtons, true);
    this.canvas?.removeEventListener("pointerleave", this.onPointerLeave);
    this.canvas?.removeEventListener("pointerenter", this.onPointerEnter);
    this.canvas?.removeEventListener("dblclick", this.onDoubleClick);
    this.canvas?.removeEventListener("contextmenu", this.onContextMenu);
    this.highlighter.clearAll();
    this.pickRegistry.clear();
    this.geoMarkers.dispose();
    this.geoGrid.dispose();
    this.calMarkers.dispose();
    this.hoveredPickId = null;
    this.selectedPickId = null;
    this.selectedActive = false;
    this.lastClickWorld = null;
    this.focusTween = null;
    this.loader.cancelAll();
    this.activator.disposeAll();
    this.longTasks.dispose();
    clearBoundsCache();
    this.neutralMat?.dispose();
    this.neutralMat = null;
    this.matOverride.restore();
    this.spikeHighlighter.dispose();
    this.componentOverlay.dispose();
    this.bisector.deactivate();
    if (this.savedSpikeVis) {
      for (const [mesh, v] of this.savedSpikeVis) mesh.visible = v;
      this.savedSpikeVis = null;
    }
    this.scene.overrideMaterial = null;
    this.depthDebugMat?.dispose();
    this.depthDebugMat = null;
    this.debugAmbient?.removeFromParent();
    this.debugAmbient = null;
    this.meshBoundsGroup.clear();
    this.meshBoundsGroup.removeFromParent();
    this.environment?.dispose();
    this.environment = null;
    this.lod.dispose();
    this.materialShare.dispose();
    for (const node of this.assetNodes.values()) disposeObject3D(node);
    this.controls?.dispose();
    try {
      this.renderer?.forceContextLoss();
    } catch {
      /* Safari may not implement lose_context */
    }
    this.renderer?.dispose();
    this.scene.clear();
    this.assetNodes.clear();
    this.assetVisibility.clear();
    this.assetCenters.clear();
    this.tileHelpers.clear();
    this.layerGroups.clear();
    this.renderer = null;
    this.rendererReady = false;
    this.camera = null;
    this.controls = null;
    this.canvas = null;
  }
}
