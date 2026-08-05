/**
 * Digital Citizen activity + EventBus bridge — Sprint 29.1.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import {
  DIGITAL_CITIZEN_VERSION,
  type CitizenActivityEvent,
  type CitizenActivityName,
} from "./citizenTypes";

const events: CitizenActivityEvent[] = [];

function uid() {
  return `act_${Math.random().toString(36).slice(2, 10)}`;
}

export function publishCitizenActivity(
  name: CitizenActivityName,
  citizenId: string,
  payload: Record<string, unknown> = {},
) {
  const entry: CitizenActivityEvent = {
    id: uid(),
    name,
    citizenId,
    at: new Date().toISOString(),
    payload,
  };
  events.unshift(entry);
  if (events.length > 200) events.length = 200;

  enterpriseEventBus.publish({
    type: "digital_citizen_update",
    source: "system",
    payload: {
      stream: "digital_citizen",
      event: name,
      citizenId,
      version: DIGITAL_CITIZEN_VERSION,
      ...payload,
    },
  });
  return entry;
}

export const activityEngine = {
  clear() {
    events.length = 0;
  },

  list(limit = 40, citizenId?: string) {
    const all = citizenId ? events.filter((e) => e.citizenId === citizenId) : events;
    return all.slice(0, limit);
  },

  record: publishCitizenActivity,
};

export const citizenEvents = {
  created: (citizenId: string) => publishCitizenActivity("CitizenCreated", citizenId),
  updated: (citizenId: string) => publishCitizenActivity("CitizenUpdated", citizenId),
  joinedCompany: (citizenId: string, orgId: string) =>
    publishCitizenActivity("CitizenJoinedCompany", citizenId, { orgId }),
  leftCompany: (citizenId: string, orgId: string) =>
    publishCitizenActivity("CitizenLeftCompany", citizenId, { orgId }),
  roleChanged: (citizenId: string, role: string, orgId: string) =>
    publishCitizenActivity("RoleChanged", citizenId, { role, orgId }),
  taskAssigned: (citizenId: string, taskId: string) =>
    publishCitizenActivity("TaskAssigned", citizenId, { taskId }),
  meetingJoined: (citizenId: string, meetingId: string) =>
    publishCitizenActivity("MeetingJoined", citizenId, { meetingId }),
  documentSigned: (citizenId: string, documentRef: string) =>
    publishCitizenActivity("DocumentSigned", citizenId, { documentRef }),
  projectJoined: (citizenId: string, projectId: string) =>
    publishCitizenActivity("ProjectJoined", citizenId, { projectId }),
  aiAssigned: (citizenId: string, aiId: string) =>
    publishCitizenActivity("AIAssigned", citizenId, { aiId }),
  presenceChanged: (citizenId: string, status: string) =>
    publishCitizenActivity("PresenceChanged", citizenId, { status }),
};
