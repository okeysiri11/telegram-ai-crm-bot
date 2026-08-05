/**
 * Enterprise Spatial Runtime public API — Sprint 29.4.
 */

export {
  SPATIAL_RUNTIME_VERSION,
  SPATIAL_PERSIST_KEY,
  SPATIAL_API_PREFIX,
  ODESSA_CITY,
} from "./spatialTypes";
export type {
  SpatialEntityKind,
  SpatialDistrictKind,
  SpatialRelationKind,
  LocationAssignmentKind,
  SpatialEventName,
  GeoLocation,
  GeoRegion,
  SpatialMetadata,
  SpatialEntity,
  District,
  Building,
  Floor,
  Room,
  Workspace,
  Zone,
  PointOfInterest,
  SpatialRelationship,
  LocationAssignment,
  NavigationNode,
  SpatialRoute,
  CitySpatialQuery,
} from "./spatialTypes";

export { spatialPermissions } from "./spatialPermissions";
export type { SpatialPermissionScope } from "./spatialPermissions";
export { spatialEvents, publishSpatialEvent } from "./spatialEvents";
export { spatialRegistry, planeToGeo, districtKindForCityDistrict } from "./spatialRegistry";
export { locationEngine } from "./locationEngine";
export { routingEngine } from "./routingEngine";
export { seedOdessaSpatial } from "./spatialSeed";
export { buildCitySpatialQuery, buildingsInDistrict, resolveSpatialBuildingId } from "./citySpatialQuery";
export { spatialRuntime } from "./spatialRuntime";
export { spatialRuntimeApi, spatialApiPrefix } from "./spatialRuntimeApi";
