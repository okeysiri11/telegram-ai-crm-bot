/**
 * Digital Citizen public API — Sprint 29.1.
 */

export {
  DIGITAL_CITIZEN_VERSION,
  EDC_PERSIST_KEY,
  EDC_API_PREFIX,
} from "./citizenTypes";
export type {
  CitizenStatus,
  CitizenVerification,
  PresenceStatus,
  OrganizationRole,
  CitizenPermissionScope,
  PersonalAiKind,
  CitizenActivityName,
  CitizenIdentity,
  CitizenPreferences,
  CitizenPresence,
  CitizenProfile,
  Citizen,
  Department,
  Position,
  EmploymentHistoryEntry,
  OrganizationMember,
  PersonalTask,
  PersonalCalendarEvent,
  AssignedProject,
  WorkspaceBookmark,
  CitizenWorkspace,
  PersonalAiAgent,
  CitizenActivityEvent,
  CityCitizenFacade,
} from "./citizenTypes";

export { citizenPermissions } from "./citizenPermissions";
export { activityEngine, citizenEvents, publishCitizenActivity } from "./citizenEvents";
export { citizenProfileService } from "./citizenProfileService";
export { organizationMembershipService } from "./organizationMembershipService";
export { citizenWorkspaceService } from "./citizenWorkspaceService";
export { personalAiRegistry } from "./personalAiRegistry";
export { presenceEngine, PRESENCE_STATUSES } from "./presenceEngine";
export { cityCitizenBridge, toCityCitizenFacade } from "./cityCitizenBridge";
export { digitalCitizenEngine } from "./digitalCitizenEngine";
export { digitalCitizenApi, edcApiPrefix } from "./digitalCitizenApi";
export {
  seedDigitalCitizens,
  EDC_ORG_DEMO,
  EDC_CITIZEN_OWNER,
  EDC_CITIZEN_MANAGER,
  EDC_CITIZEN_DEV,
} from "./citizenSeed";
