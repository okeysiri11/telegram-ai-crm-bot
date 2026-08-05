/**
 * Enterprise City Visualization Runtime types — Sprint 29.5.
 * Runtime bridge for future 2D/3D Digital Twin clients — no graphics.
 */

export const CITY_VIS_VERSION = "29.5";
export const CITY_VIS_PERSIST_KEY = "ews_city_visualization_v1";
export const CITY_VIS_API_PREFIX = "/api/enterprise-city-viz/v1";

export type VisualizationLayerId =
  | "districts"
  | "buildings"
  | "citizens"
  | "companies"
  | "assets"
  | "activities"
  | "traffic"
  | "overlays";

export type LodTier = "far" | "medium" | "near" | "detail";

export type BuildingOpenState = "open" | "closed" | "restricted" | "unknown";

export type BuildingVisualStatus =
  | "idle"
  | "active"
  | "busy"
  | "alert"
  | "offline"
  | "maintenance";

export type CityVisEventName =
  | "BuildingUpdated"
  | "CitizenMoved"
  | "MeetingStarted"
  | "MeetingFinished"
  | "AssetMoved"
  | "CompanyUpdated"
  | "DistrictUpdated"
  | "WorkflowExecuted"
  | "SceneRebuilt"
  | "VisibilityChanged";

export type VisualizationLayer = {
  id: VisualizationLayerId;
  label: string;
  enabled: boolean;
  order: number;
  lodMin: LodTier;
};

export type BuildingVisualState = {
  buildingId: string;
  spatialEntityId?: string;
  districtId?: string;
  status: BuildingVisualStatus;
  occupancy: number;
  businessActivity: number;
  openState: BuildingOpenState;
  meetingCount: number;
  meetingIds: string[];
  projectIds: string[];
  companyIds: string[];
  assetCount: number;
  processLabel?: string;
  /** Future branding hooks for twin clients */
  branding?: {
    logoRef?: string;
    accentHint?: string;
    labelOverride?: string;
  };
  updatedAt: string;
};

export type DistrictVisualState = {
  districtId: string;
  spatialEntityId?: string;
  districtKind?: string;
  activity: number;
  population: number;
  businessDensity: number;
  constructionActivity: number;
  trafficDensity: number;
  economicActivity: number;
  runtimeStatus: BuildingVisualStatus;
  buildingIds: string[];
  updatedAt: string;
};

export type CitizenVisualState = {
  citizenId: string;
  displayName: string;
  buildingId?: string;
  workspaceId?: string;
  companyId?: string;
  presence: string;
  role?: string;
  activity?: string;
  remote: boolean;
  avatarRef?: string;
  updatedAt: string;
};

export type AssetVisualState = {
  assetId: string;
  name: string;
  type: string;
  category?: string;
  buildingId?: string;
  districtId?: string;
  status: string;
  available: boolean;
  isVehicle: boolean;
  isEquipment: boolean;
  isWarehouse: boolean;
  isHeadquarters: boolean;
  isConstruction: boolean;
  isDrone: boolean;
  updatedAt: string;
};

export type CompanyVisualState = {
  companyId: string;
  name: string;
  buildingIds: string[];
  category?: string;
  relationshipCount: number;
  updatedAt: string;
};

export type ActivityVisualState = {
  id: string;
  kind: "meeting" | "workflow" | "movement" | "project" | "automation";
  label: string;
  buildingId?: string;
  districtId?: string;
  subjectIds: string[];
  status: string;
  at: string;
};

export type CityScene = {
  id: string;
  cityId: string;
  cityName: string;
  version: string;
  generatedAt: string;
  layers: VisualizationLayer[];
  buildings: BuildingVisualState[];
  districts: DistrictVisualState[];
  citizens: CitizenVisualState[];
  companies: CompanyVisualState[];
  assets: AssetVisualState[];
  activities: ActivityVisualState[];
};

export type VisualizationState = {
  sceneId: string;
  revision: number;
  lastEvent?: CityVisEventName;
  dirtyLayers: VisualizationLayerId[];
  visibleBuildingIds: string[];
  visibleCitizenIds: string[];
  visibleCompanyIds: string[];
  visibleAssetIds: string[];
  visibleActivityIds: string[];
  visibleDistrictIds: string[];
  lod: LodTier;
  viewportHint?: { minX: number; minY: number; maxX: number; maxY: number };
};

export type VisibleCityQuery = {
  buildings: BuildingVisualState[];
  citizens: CitizenVisualState[];
  companies: CompanyVisualState[];
  assets: AssetVisualState[];
  activities: ActivityVisualState[];
  districts: DistrictVisualState[];
  revision: number;
  lod: LodTier;
};

export type LodDescriptor = {
  tier: LodTier;
  includeCitizens: boolean;
  includeAssets: boolean;
  includeActivities: boolean;
  includeBranding: boolean;
  maxEntities: number;
};

export type IncrementalUpdate = {
  revision: number;
  event?: CityVisEventName;
  upsertBuildings: BuildingVisualState[];
  upsertDistricts: DistrictVisualState[];
  upsertCitizens: CitizenVisualState[];
  upsertAssets: AssetVisualState[];
  upsertActivities: ActivityVisualState[];
  removeIds: string[];
  at: string;
};

export type RendererBridgePayload = {
  scene: CityScene;
  state: VisualizationState;
  query: VisibleCityQuery;
  incremental?: IncrementalUpdate;
};
