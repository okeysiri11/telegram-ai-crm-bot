/**
 * Life event engine + EventBus bridge — Sprint 29.2.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { LIFE_ENGINE_VERSION, type LifeEvent, type LifeEventKind } from "./lifeTypes";

const events: LifeEvent[] = [];
const listeners = new Set<(e: LifeEvent) => void>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

/** Map life kinds to EventBus payload event names */
const BUS_EVENT_NAME: Partial<Record<LifeEventKind, string>> = {
  citizen_moved: "CitizenMoved",
  meeting_created: "MeetingCreated",
  meeting_started: "MeetingCreated",
  meeting_ended: "MeetingFinished",
  document_shared: "DocumentShared",
  document_signed: "DocumentShared",
  project_updated: "ProjectUpdated",
  project_started: "ProjectUpdated",
  project_completed: "ProjectUpdated",
  vehicle_assigned: "VehicleAssigned",
  vehicle_departed: "VehicleAssigned",
  vehicle_arrived: "VehicleAssigned",
  company_visited: "CompanyVisited",
  partner_visited: "CompanyVisited",
  business_visit: "CompanyVisited",
  workflow_completed: "WorkflowCompleted",
  workflow_executed: "WorkflowCompleted",
};

export function publishLifeEvent(
  kind: LifeEventKind,
  partial: Omit<Partial<LifeEvent>, "id" | "kind" | "at" | "payload"> & {
    payload?: Record<string, unknown>;
    message?: string;
  } = {},
): LifeEvent {
  const event: LifeEvent = {
    id: uid("life"),
    kind,
    at: new Date().toISOString(),
    citizenId: partial.citizenId,
    companyId: partial.companyId,
    buildingId: partial.buildingId,
    projectId: partial.projectId,
    aiId: partial.aiId,
    vehicleId: partial.vehicleId,
    meetingId: partial.meetingId,
    documentRef: partial.documentRef,
    workflowId: partial.workflowId,
    fromBuildingId: partial.fromBuildingId,
    toBuildingId: partial.toBuildingId,
    message: partial.message,
    payload: partial.payload || {},
  };
  events.unshift(event);
  if (events.length > 400) events.length = 400;

  const busName = BUS_EVENT_NAME[kind] || kind;
  enterpriseEventBus.publish({
    type: "life_engine_update",
    source: "system",
    payload: {
      stream: "life_engine",
      event: busName,
      kind,
      version: LIFE_ENGINE_VERSION,
      citizenId: event.citizenId,
      buildingId: event.buildingId,
      projectId: event.projectId,
      companyId: event.companyId,
      ...event.payload,
    },
  });
  // Keep City live
  enterpriseEventBus.publish({
    type: "city_update",
    source: "system",
    payload: { stream: "life_engine", kind, buildingId: event.buildingId },
  });

  listeners.forEach((l) => l(event));
  return event;
}

export const lifeEventEngine = {
  clear() {
    events.length = 0;
  },

  subscribe(listener: (e: LifeEvent) => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  list(limit = 60) {
    return events.slice(0, limit);
  },

  byCitizen(citizenId: string, limit = 40) {
    return events.filter((e) => e.citizenId === citizenId).slice(0, limit);
  },

  byBuilding(buildingId: string, limit = 40) {
    return events.filter(
      (e) => e.buildingId === buildingId || e.toBuildingId === buildingId || e.fromBuildingId === buildingId,
    ).slice(0, limit);
  },

  byProject(projectId: string, limit = 40) {
    return events.filter((e) => e.projectId === projectId).slice(0, limit);
  },

  byCompany(companyId: string, limit = 40) {
    return events.filter((e) => e.companyId === companyId).slice(0, limit);
  },

  byAi(aiId: string, limit = 40) {
    return events.filter((e) => e.aiId === aiId).slice(0, limit);
  },

  record: publishLifeEvent,
};
