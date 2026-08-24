/**
 * Interactive City 3D — core domain types.
 * Presentation layer only; platform records stay in existing modules.
 */

import type { GeoLocation } from "@/runtime/spatialRuntime/spatialTypes";
import type { CityBuildingId } from "../cityCatalog";

export type CityViewMode = "2d" | "3d" | "hybrid";

export type CityEntityKind =
  | "building"
  | "road"
  | "route"
  | "connection"
  | "project"
  | "vehicle"
  | "marker"
  | "platform"
  | "tile"
  | "unknown";

/** Unified city entity for selection + platform navigation. */
export type CityEntity = {
  id: string;
  kind: CityEntityKind;
  label?: string;
  geo?: GeoLocation;
  /** Reference to existing platform record — never duplicate CRM/project data here. */
  platformRef?: {
    module: string;
    entityId: string;
    route?: string;
    buildingId?: CityBuildingId;
  };
  bounds?: CityBounds;
  layerId?: string;
  tileId?: string;
  metadata?: Record<string, unknown>;
};

/** Physical road vs dynamic route vs logical connection. */
export type CityRelationshipKind = "physical_road" | "route" | "connection";

export type CityRelationship = {
  id: string;
  kind: CityRelationshipKind;
  fromId: string;
  toId: string;
  label?: string;
  metadata?: Record<string, unknown>;
};

export type CityBounds = {
  minX: number;
  maxX: number;
  minY?: number;
  maxY?: number;
  minZ: number;
  maxZ: number;
};

export type AssetStatus = "idle" | "queued" | "loading" | "loaded" | "failed" | "unloaded";

export type AssetSource = "REAL_GLB" | "PROCEDURAL_FALLBACK";

export type AssetLoadPhase = "idle" | "queued" | "fetching" | "downloaded" | "parsing" | "parsed" | "loaded" | "failed";

export type AssetLifecycle =
  | "queued"
  | "fetching"
  | "waiting_parse"
  | "parsing"
  | "parsed"
  | "preparing"
  | "ready"
  | "active"
  | "hidden"
  | "failed";

export type BootState = "BOOTSTRAP" | "INTERACTIVE" | "FILLING" | "READY";

export type HeavyClass = "LIGHT" | "MEDIUM" | "HEAVY" | "EXTREME";

export type AssetTimings = {
  fetchMs?: number;
  arrayBufferMs?: number;
  parseMs?: number;
  prepMs?: number;
  attachMs?: number;
  totalBlockingMs?: number;
  triangleCount?: number;
  objectCount?: number;
};

export type AssetLoadDiagnostic = {
  id: string;
  url: string;
  phase: AssetLoadPhase;
  bytesLoaded?: number;
  bytesTotal?: number;
  elapsedMs?: number;
  fetchMs?: number;
  arrayBufferMs?: number;
  parseMs?: number;
  sizeMb?: number;
  triangleCount?: number;
  objectCount?: number;
  error?: string;
  meshCount?: number;
  httpStatus?: number;
};

export type CityAsset = {
  id: string;
  url: string;
  status: AssetStatus;
  size?: number;
  sizeMb?: number;
  source?: AssetSource;
  loadPhase?: AssetLoadPhase;
  lifecycle?: AssetLifecycle;
  /** Three.js root — kept outside React state; accessed via scene controller only. */
  object3D?: import("three").Object3D | null;
  bounds?: CityBounds;
  tileId?: string;
  layerId?: string;
  lod?: number;
  priority?: number;
  error?: string;
  procedural?: boolean;
  entityRefs?: string[];
  triangleCount?: number;
  objectCount?: number;
  heavyClass?: HeavyClass;
  timings?: AssetTimings;
};

export type OdessaManifestLayer = {
  id: string;
  label: string;
  defaultVisible?: boolean;
  dynamic?: boolean;
};

export type OdessaManifestAsset = {
  id: string;
  url: string;
  layer: string;
  priority?: number;
  lod?: number;
  bounds?: CityBounds;
  entityRef?: string;
  label?: string;
  sizeMb?: number;
  sourceType?: string;
  triangles?: number;
  objects?: number;
};

export type OdessaManifestTile = {
  id: string;
  label?: string;
  center: { lat: number; lng: number };
  centerScene?: { x: number; z: number };
  radiusM?: number;
  assets: OdessaManifestAsset[];
};

export type GeoTransformCalibration = {
  originLat: number;
  originLng: number;
  scaleMetersPerDegreeLat?: number;
  scaleMetersPerDegreeLng?: number;
  rotationY?: number;
  elevationOffset?: number;
  /** When false, scene uses approximate WGS84 scaling — fine-tune with survey/GPS later. */
  calibrated?: boolean;
};

export type OdessaManifest = {
  version: string;
  cityId: string;
  name: string;
  center: { lat: number; lng: number; alt?: number };
  geoTransform: GeoTransformCalibration;
  cityBounds?: CityBounds;
  priorityTiles?: string[];
  tiles: OdessaManifestTile[];
  layers: OdessaManifestLayer[];
  packageFormat?: string;
  stats?: Record<string, number>;
};

export type QualityProfile = "auto" | "low" | "medium" | "high";

export type LoadingProgress = {
  total: number;
  loaded: number;
  failed: number;
  queued: number;
  loading: number;
  percent: number;
  loadingAssetId?: string | null;
  loadedMb?: number;
  totalMb?: number;
  realGlbLoaded?: number;
  sourceMode?: AssetSource | "MIXED";
  loadDiagnostics?: AssetLoadDiagnostic[];
  firstError?: string | null;
  parsedCount?: number;
  activeCount?: number;
  downloadedCount?: number;
  bootState?: BootState;
  currentAssetId?: string | null;
  waitingParse?: number;
};

export type OdessaDevDiagnostics = {
  /** STEP 29.9: active asset package (REBUILT_METRIC | CURRENT_BROKEN). */
  assetPackage?: string;
  loadedAssets: number;
  queuedAssets: number;
  failedAssets: number;
  realGlbLoaded?: number;
  triangleCount?: number;
  meshCount?: number;
  camera: { x: number; y: number; z: number };
  lookAt?: { x: number; y: number; z: number };
  selectedEntityId?: string | null;
  activeLayers: string[];
  quality: QualityProfile;
  tilesActive: string[];
  cityBounds?: { min: { x: number; y: number; z: number }; max: { x: number; y: number; z: number }; center: { x: number; y: number; z: number }; size: { x: number; y: number; z: number } };
  axisExtents?: { x: number; y: number; z: number };
  sourceMode?: AssetSource | "MIXED";
  loadingAssetId?: string | null;
  visibleTiles?: number;
  cameraDistance?: number;
  cityDiagonal?: number;
  materialAudit?: {
    meshCount: number;
    materialCount: number;
    textureCount: number;
    missingTextureSlots: number;
    vertexColorMeshes: number;
  };
  odessaReady?: boolean;
  runtimeMode?: "IDLE" | "INTERACTING" | "SETTLING";
  bootState?: BootState;
  waterAudit?: {
    meshCount: number;
    kept: number;
    duplicatesHidden: number;
    debug: boolean;
    logarithmicDepthBuffer: boolean;
    surfaces?: Array<{
      name: string;
      category: string;
      minY: number;
      maxY: number;
      materialType: string;
      transparent: boolean;
      depthWrite: boolean;
      side: number;
      renderOrder: number;
      hiddenAsDuplicate: boolean;
    }>;
  };
  panSpeed?: number;
  cameraNear?: number;
  cameraFar?: number;
  renderStability?: {
    cityRootInstances: number;
    meshCount: number;
    visibleMeshes: number;
    transparentMaterials: number;
    depthWriteFalseCount: number;
    cameraNear: number;
    cameraFar: number;
    farNearRatio: number;
    rendererPixelRatio: number;
    drawCalls: number;
    triangles: number;
    isolation?: {
      baseModelOnly: boolean;
      disableWater: boolean;
      disableOverlays: boolean;
      neutralMaterial: boolean;
    };
  };
  artifactDebug?: {
    debugView: {
      sourceCityOnly: boolean;
      environmentOff: boolean;
      lightsNeutral: boolean;
      wireframe: boolean;
      depthDebug: boolean;
      sideMode: "original" | "front" | "double";
      transparentOff: boolean;
      showMeshBounds: boolean;
      hideBasePlane: boolean;
      tightClip: boolean;
      spikesOnly: boolean;
      hideSpikes?: boolean;
      colorSpikesRed?: boolean;
      /** STEP 29.8 component-repair dev modes. */
      componentColors?: boolean;
      componentRepairOff?: boolean;
    };
    bisect: {
      active: boolean;
      totalMeshes: number;
      currentCount: number;
      showing: "ALL" | "A" | "B";
      depth: number;
      path: string;
      currentNames: string[];
    };
    cameraAltitude: {
      cameraY: number;
      cityBaseY: number;
      altitudeAboveBase: number;
      insideCityBox: boolean;
      belowCityBase: boolean;
      belowSeaLevel: boolean;
    } | null;
    decalMeshes: number;
    verticalRecovery?: {
      mode: "off" | "selective" | "legacy";
      factor: number;
      correctedMeshes: number;
      spikeSuspects: number;
      /** STEP 29.7: meshes left as authored because their vertex buffers bake
       * meter-domain miniature features (vertical recovery would needle them). */
      mixedDomainMeshes: number;
      cityHeight: number;
    };
    /** STEP 29.8: vertex-level component repair of mixed-domain merged meshes. */
    componentRepair?: {
      meshes: number;
      totalComponents: number;
      repairedComponents: number;
      sourceAnomalies: number;
      revertedComponents: number;
      modifiedVertices: number;
    };
    lastInspection: {
      object: string;
      parent: string;
      material: string;
      geometry: string;
      distance: number;
      worldPosition: [number, number, number];
      faceIndex: number;
      boundingBox: { min: [number, number, number]; max: [number, number, number] } | null;
      meshBoxHeight: number | null;
      meshFootprint: number | null;
      decalRank: number | null;
      verticalRecovery: { factor: number; preHeight: number; postHeight: number; reason: string } | null;
      spikeSuspect: boolean;
    } | null;
  };
  lighting?: {
    outputColorSpace: string;
    toneMapping: string;
    toneMappingExposure: number;
    sunIntensity: number;
    hemiIntensity: number;
    fogEnabled: boolean;
    fogDensity: number;
    fogColor: string;
    fogMixAtCameraPct: number;
    fogMixAtDiagonalPct: number;
    emissiveActiveMaterials: number;
    metalTexturedMaterials: number;
    srgbDataMapViolations: number;
    vertexColorMeshes: number;
    transparentTexturedMaterials: number;
  };
  zoomTowardPointer?: boolean;
  screenSpacePanning?: boolean;
  interaction?: {
    pickables: number;
    hovered: string | null;
    selected: string | null;
    selectedActive: boolean;
    raycastsPerSec: number;
    lastRaycastMs: number;
    candidates: number;
    hits: number;
    boundEntities: number;
    unboundEntities: number;
    ambiguousEntities?: number;
    registrySize: number;
    materialClones: number;
    interactionEnabled: boolean;
    showSelectionBounds?: boolean;
  };
  sceneAudit?: {
    object3dCount: number;
    meshCount: number;
    namedMeshCount: number;
    unnamedMeshCount: number;
    materialsReused: number;
    uniqueMaterials: number;
    meshesWithUserData: number;
    meshesWithAssetId: number;
  };
  georeference?: {
    status: string;
    source: string;
    confidence: string;
    originLat: number | null;
    originLon: number | null;
    worldOrigin: { x: number; y: number; z: number } | null;
    metersPerWorldUnit: number | null;
    rotation: number | null;
    axisMapping: string;
    controlPoints: number;
    meanError: number | null;
    maxError: number | null;
    quality?: string;
    modelGeoBounds: { north: number; south: number; east: number; west: number } | null;
    anchors: number;
    inBounds: number;
    outOfBounds: number;
    selectedWorld: { x: number; y: number; z: number } | null;
    selectedGeo: { lat: number; lon: number } | null;
    cameraGeo: { lat: number; lon: number } | null;
    cameraWorld?: { x: number; y: number; z: number } | null;
    cameraTargetWorld?: { x: number; y: number; z: number } | null;
    cameraTargetGeo?: { lat: number; lon: number } | null;
    overlays?: boolean;
    reasons?: string[];
    modelFingerprint?: string | null;
    modelMismatch?: boolean;
  };
};

export type OdessaPerfDiagnostics = {
  fps: number;
  frameMs: number;
  drawCalls: number;
  triangles: number;
  points: number;
  lines: number;
  geometries?: number;
  textures?: number;
  visibleObjects: number;
  loadedGlbs: number;
  visibleGlbs?: number;
  queuedAssets?: number;
  activeTiles?: number;
  cameraDistance: number;
  pixelRatio: number;
  adaptiveTier: string;
  continuousRender: boolean;
  runtimeMode?: "IDLE" | "INTERACTING" | "SETTLING";
  streamingPaused?: boolean;
  bootState?: BootState;
  parsedCount?: number;
  downloadedCount?: number;
  firstLoad?: {
    timeToManifest: number | null;
    timeToFirstParse: number | null;
    timeToFirstGeometry: number | null;
    timeToFirstRender: number | null;
    timeToInteractive: number | null;
    timeTo50PercentActive: number | null;
    timeToReady: number | null;
    totalParseMs: number;
    averageParseMs: number;
    longTaskCount: number;
    longTasks50?: number;
    longTasks100?: number;
    longTasks250?: number;
    longTasks500?: number;
    worst10: Array<{ id: string; parseMs: number; sizeMb: number; triangleCount: number }>;
  };
  environment?: {
    preset: string;
    sunElevation: number;
    sunAzimuth: number;
    sunIntensity?: number;
    hemiIntensity?: number;
    fogEnabled?: boolean;
    fogDensity: number;
    fogColor?: string;
    exposure: number;
    waterMode: string;
    skyEnabled: boolean;
    environmentQuality: string;
    classifiedMaterials?: string;
    normalizedMaterials?: number;
    texturedMaterialsSkipped?: number;
    buildingVariationCount?: number;
  };
  lod?: {
    near: number;
    mid: number;
    far: number;
    cull: number;
    visible: number;
    hidden: number;
    protectedSea: number;
    protectedTarget: number;
    activeTriangles: number;
    hiddenTriangles: number;
    priorityMs: number;
    boundsMs: number;
    transitionsPerSec?: number;
  };
  quality?: {
    mode: string;
    pixelRatio: number;
    antialias: boolean;
    anisotropy: number;
    fps: number;
    interactionState: "IDLE" | "INTERACTING" | "SETTLING";
    visibleAssets: number;
    hiddenAssets: number;
    lodTransitionsPerSec: number;
    triangles: number;
    drawCalls: number;
  };
  pipeline?: {
    fetching: number;
    waitingParse: number;
    parsing: number;
    parsed: number;
    waitingActivation: number;
    active: number;
    hidden: number;
    failed: number;
    fetchingMb: number;
    waitingParseMb: number;
    parsingMb: number;
    currentParseId: string | null;
    currentParseSizeMb: number;
    currentParseElapsedMs: number;
    lastParseMs: number;
    averageParseMs: number;
    worstParseMs: number;
    longTasks50: number;
    longTasks100: number;
    longTasks250: number;
    longTasks500: number;
    fetchQueue: number;
    parseQueue: number;
    activationQueue: number;
    fetchConcurrent: number;
    parseConcurrent: number;
    backpressure: boolean;
    worstOffenders: Array<{ id: string; parseMs: number; sizeMb: number; triangleCount: number }>;
  };
};
