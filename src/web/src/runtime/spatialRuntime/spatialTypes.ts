/**
 * Enterprise Spatial Runtime types — Sprint 29.4.
 * Odessa Digital Twin foundation (runtime only — no map rendering).
 */

export const SPATIAL_RUNTIME_VERSION = "29.4";
export const SPATIAL_PERSIST_KEY = "ews_spatial_runtime_v1";
export const SPATIAL_API_PREFIX = "/api/enterprise-spatial/v1";

/** WGS84-ish coords for Odessa Digital Twin reference */
export const ODESSA_CITY = {
  id: "city_odessa",
  name: "Odessa",
  nameUk: "Одеса",
  country: "UA",
  region: "Odesa Oblast",
  /** Approximate city center */
  lat: 46.4825,
  lng: 30.7233,
  timezone: "Europe/Kyiv",
} as const;

export type SpatialEntityKind =
  | "country"
  | "region"
  | "city"
  | "district"
  | "street"
  | "building"
  | "floor"
  | "room"
  | "workspace"
  | "zone"
  | "poi"
  | "virtual_space";

export type SpatialDistrictKind =
  | "business"
  | "industrial"
  | "logistics"
  | "financial"
  | "medical"
  | "education"
  | "construction"
  | "marketplace"
  | "residential"
  | "custom";

export type SpatialRelationKind =
  | "contains"
  | "adjacent"
  | "connected"
  | "near"
  | "inside"
  | "outside"
  | "assigned"
  | "visited";

export type LocationAssignmentKind =
  | "current"
  | "assigned"
  | "home_office"
  | "company_office"
  | "remote_workplace"
  | "warehouse"
  | "construction_site"
  | "meeting_room"
  | "dynamic";

export type SpatialEventName =
  | "LocationChanged"
  | "EnteredBuilding"
  | "LeftBuilding"
  | "EnteredDistrict"
  | "AssignedWorkspace"
  | "MovedAsset"
  | "BuildingRegistered";

export type GeoLocation = {
  lat: number;
  lng: number;
  /** City plane 0–100 (Enterprise City map space) */
  x?: number;
  y?: number;
  altitudeM?: number;
  label?: string;
};

export type GeoRegion = {
  id: string;
  name: string;
  /** Bounding box in city plane */
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  center: GeoLocation;
};

export type SpatialMetadata = Record<string, unknown>;

export type SpatialEntity = {
  id: string;
  kind: SpatialEntityKind;
  name: string;
  parentId?: string;
  geo?: GeoLocation;
  region?: GeoRegion;
  districtKind?: SpatialDistrictKind;
  /** Link to existing City catalog building id */
  cityBuildingId?: string;
  /** Link to CityDistrictId */
  cityDistrictId?: string;
  companyId?: string;
  capacity?: number;
  metadata: SpatialMetadata;
  createdAt: string;
  updatedAt: string;
};

export type SpatialRelationship = {
  id: string;
  kind: SpatialRelationKind;
  fromId: string;
  toId: string;
  weight?: number;
  createdAt: string;
};

export type LocationAssignment = {
  id: string;
  subjectKind: "citizen" | "asset" | "company" | "meeting" | "project";
  subjectId: string;
  kind: LocationAssignmentKind;
  entityId: string;
  since: string;
  until?: string;
  dynamic?: GeoLocation;
};

export type NavigationNode = {
  id: string;
  entityId: string;
  geo: GeoLocation;
  edges: { toNodeId: string; distanceM: number; travelSec: number }[];
};

export type SpatialRoute = {
  id: string;
  fromEntityId: string;
  toEntityId: string;
  nodeIds: string[];
  path: GeoLocation[];
  distanceM: number;
  travelTimeSec: number;
  /** Future: traffic / vehicle mode */
  mode: "walk" | "vehicle" | "transit" | "virtual";
};

export type District = SpatialEntity & { kind: "district" };
export type Building = SpatialEntity & { kind: "building" };
export type Floor = SpatialEntity & { kind: "floor" };
export type Room = SpatialEntity & { kind: "room" };
export type Workspace = SpatialEntity & { kind: "workspace" };
export type Zone = SpatialEntity & { kind: "zone" };
export type PointOfInterest = SpatialEntity & { kind: "poi" };

export type CitySpatialQuery = {
  buildingsByDistrict: Record<string, SpatialEntity[]>;
  companiesByBuilding: Record<string, string[]>;
  citizensByLocation: Record<string, string[]>;
  assetsByBuilding: Record<string, string[]>;
  projectsByArea: Record<string, string[]>;
  meetingsByOffice: Record<string, string[]>;
  districts: SpatialEntity[];
  stats: {
    entities: number;
    buildings: number;
    districts: number;
    routesCached: number;
    assignments: number;
  };
};
