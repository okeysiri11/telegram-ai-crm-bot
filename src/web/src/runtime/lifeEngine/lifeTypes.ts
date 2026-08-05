/**
 * Enterprise Life Engine types — Sprint 29.2.
 * Living ecosystem over Citizens · EBN · City · AI · Automation.
 */

export const LIFE_ENGINE_VERSION = "29.2";
export const LIFE_PERSIST_KEY = "ews_life_engine_v1";
export const LIFE_API_PREFIX = "/api/enterprise-life/v1";

export type LifeEventKind =
  | "citizen_enters_office"
  | "citizen_leaves_office"
  | "citizen_starts_work"
  | "citizen_finishes_work"
  | "meeting_started"
  | "meeting_ended"
  | "project_started"
  | "project_completed"
  | "document_signed"
  | "partner_visited"
  | "vehicle_departed"
  | "vehicle_arrived"
  | "ai_activated"
  | "workflow_executed"
  | "citizen_moved"
  | "meeting_created"
  | "document_shared"
  | "project_updated"
  | "vehicle_assigned"
  | "company_visited"
  | "workflow_completed"
  | "business_visit"
  | "meeting_invitation"
  | "partnership_discussion"
  | "shared_workspace"
  | "project_collaboration";

export type TimelineSubjectKind = "company" | "citizen" | "project" | "ai" | "building";

export type LifePresence =
  | "working"
  | "in_meeting"
  | "travelling"
  | "busy"
  | "available"
  | "remote"
  | "vacation"
  | "offline";

export type MovementKind =
  | "office_to_office"
  | "office_to_meeting"
  | "warehouse_to_client"
  | "construction_to_supplier"
  | "remote_worker"
  | "ai_movement"
  | "vehicle";

export type ProjectMemberRole =
  | "owner"
  | "lead"
  | "contributor"
  | "reviewer"
  | "observer"
  | "sponsor";

export type LifeEvent = {
  id: string;
  kind: LifeEventKind;
  at: string;
  citizenId?: string;
  companyId?: string;
  buildingId?: string;
  projectId?: string;
  aiId?: string;
  vehicleId?: string;
  meetingId?: string;
  documentRef?: string;
  workflowId?: string;
  fromBuildingId?: string;
  toBuildingId?: string;
  message?: string;
  payload: Record<string, unknown>;
};

export type TimelineEntry = LifeEvent & {
  subjectKind: TimelineSubjectKind;
  subjectId: string;
};

export type OccupantKind = "employee" | "visitor" | "meeting_attendee" | "ai";

export type BuildingOccupant = {
  id: string;
  buildingId: string;
  citizenId?: string;
  aiId?: string;
  kind: OccupantKind;
  since: string;
  meetingId?: string;
};

export type BuildingOccupancy = {
  buildingId: string;
  capacity: number;
  occupants: BuildingOccupant[];
  employeeCount: number;
  visitorCount: number;
  meetingCount: number;
  activityLabel: string;
};

export type CityMovement = {
  id: string;
  kind: MovementKind;
  actorCitizenId?: string;
  actorAiId?: string;
  vehicleId?: string;
  fromBuildingId?: string;
  toBuildingId?: string;
  startedAt: string;
  arrivedAt?: string;
  status: "in_transit" | "arrived" | "cancelled";
  purpose?: string;
};

export type LifeMeeting = {
  id: string;
  title: string;
  buildingId?: string;
  companyId?: string;
  projectId?: string;
  hostCitizenId: string;
  attendeeIds: string[];
  status: "scheduled" | "active" | "ended";
  startedAt?: string;
  endedAt?: string;
  createdAt: string;
};

export type LifeVehicle = {
  id: string;
  label: string;
  status: "idle" | "departed" | "en_route" | "arrived";
  assignedCitizenId?: string;
  fromBuildingId?: string;
  toBuildingId?: string;
  updatedAt: string;
};

export type ProjectParticipant = {
  id: string;
  projectId: string;
  projectName: string;
  citizenId: string;
  role: ProjectMemberRole;
  attendance: number;
  participationScore: number;
  assignments: string[];
  contributions: { id: string; at: string; detail: string }[];
  joinedAt: string;
};

export type BusinessInteraction = {
  id: string;
  kind:
    | "business_visit"
    | "meeting_invitation"
    | "document_exchange"
    | "partnership_discussion"
    | "shared_workspace"
    | "project_collaboration";
  fromCitizenId?: string;
  toCitizenId?: string;
  companyId?: string;
  partnerCompanyId?: string;
  buildingId?: string;
  projectId?: string;
  documentRef?: string;
  at: string;
  detail?: string;
};

export type CityRuntimeSnapshot = {
  version: string;
  citizens: { id: string; displayName: string; presence: LifePresence; buildingId?: string }[];
  occupancy: BuildingOccupancy[];
  meetings: LifeMeeting[];
  vehicles: LifeVehicle[];
  activities: LifeEvent[];
  ai: { id: string; name: string; kind: string; assignedCitizenId?: string; active: boolean }[];
  projects: { projectId: string; projectName: string; memberCount: number; status: string }[];
  movements: CityMovement[];
  stats: {
    events: number;
    online: number;
    activeMeetings: number;
    inTransit: number;
  };
};
