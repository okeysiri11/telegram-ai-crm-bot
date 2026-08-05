/**
 * Enterprise Life Engine public API — Sprint 29.2.
 */

export {
  LIFE_ENGINE_VERSION,
  LIFE_PERSIST_KEY,
  LIFE_API_PREFIX,
} from "./lifeTypes";
export type {
  LifeEventKind,
  TimelineSubjectKind,
  LifePresence,
  MovementKind,
  ProjectMemberRole,
  LifeEvent,
  TimelineEntry,
  OccupantKind,
  BuildingOccupant,
  BuildingOccupancy,
  CityMovement,
  LifeMeeting,
  LifeVehicle,
  ProjectParticipant,
  BusinessInteraction,
  CityRuntimeSnapshot,
} from "./lifeTypes";

export { lifeEventEngine, publishLifeEvent } from "./lifeEventEngine";
export { activityTimeline } from "./activityTimeline";
export { buildingOccupancy } from "./buildingOccupancy";
export { cityMovement } from "./cityMovement";
export { livePresence, toLifePresence, toCitizenPresence } from "./livePresence";
export { businessInteractions } from "./businessInteractions";
export { projectParticipation } from "./projectParticipation";
export { lifeMeetings, lifeVehicles } from "./lifeMeetings";
export { lifeEngine } from "./lifeEngine";
export { lifeEngineApi, lifeApiPrefix } from "./lifeEngineApi";
