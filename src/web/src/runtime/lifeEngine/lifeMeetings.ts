/**
 * Meetings + vehicles — Sprint 29.2 life runtime entities.
 */

import type { LifeMeeting, LifeVehicle } from "./lifeTypes";
import { publishLifeEvent } from "./lifeEventEngine";
import { buildingOccupancy } from "./buildingOccupancy";

const meetings = new Map<string, LifeMeeting>();
const vehicles = new Map<string, LifeVehicle>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const lifeMeetings = {
  clear() {
    meetings.clear();
  },

  list() {
    return [...meetings.values()].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  },

  get(id: string) {
    return meetings.get(id);
  },

  create(input: {
    title: string;
    hostCitizenId: string;
    attendeeIds?: string[];
    buildingId?: string;
    companyId?: string;
    projectId?: string;
  }): LifeMeeting {
    const meeting: LifeMeeting = {
      id: uid("mtg"),
      title: input.title,
      hostCitizenId: input.hostCitizenId,
      attendeeIds: [...new Set([input.hostCitizenId, ...(input.attendeeIds || [])])],
      buildingId: input.buildingId,
      companyId: input.companyId,
      projectId: input.projectId,
      status: "scheduled",
      createdAt: new Date().toISOString(),
    };
    meetings.set(meeting.id, meeting);
    publishLifeEvent("meeting_created", {
      meetingId: meeting.id,
      citizenId: input.hostCitizenId,
      buildingId: input.buildingId,
      companyId: input.companyId,
      projectId: input.projectId,
      message: input.title,
    });
    return meeting;
  },

  start(meetingId: string) {
    const cur = meetings.get(meetingId);
    if (!cur) return null;
    const next: LifeMeeting = {
      ...cur,
      status: "active",
      startedAt: new Date().toISOString(),
    };
    meetings.set(meetingId, next);
    if (cur.buildingId) {
      for (const citizenId of cur.attendeeIds) {
        buildingOccupancy.enter({
          buildingId: cur.buildingId,
          citizenId,
          kind: "meeting_attendee",
          meetingId,
        });
      }
    }
    publishLifeEvent("meeting_started", {
      meetingId,
      citizenId: cur.hostCitizenId,
      buildingId: cur.buildingId,
      projectId: cur.projectId,
      companyId: cur.companyId,
      message: cur.title,
    });
    return next;
  },

  end(meetingId: string) {
    const cur = meetings.get(meetingId);
    if (!cur) return null;
    const next: LifeMeeting = {
      ...cur,
      status: "ended",
      endedAt: new Date().toISOString(),
    };
    meetings.set(meetingId, next);
    publishLifeEvent("meeting_ended", {
      meetingId,
      citizenId: cur.hostCitizenId,
      buildingId: cur.buildingId,
      projectId: cur.projectId,
      message: cur.title,
    });
    return next;
  },

  active() {
    return this.list().filter((m) => m.status === "active");
  },
};

export const lifeVehicles = {
  clear() {
    vehicles.clear();
  },

  list() {
    return [...vehicles.values()];
  },

  get(id: string) {
    return vehicles.get(id);
  },

  register(label: string, id?: string): LifeVehicle {
    const v: LifeVehicle = {
      id: id || uid("veh"),
      label,
      status: "idle",
      updatedAt: new Date().toISOString(),
    };
    vehicles.set(v.id, v);
    return v;
  },

  assign(vehicleId: string, citizenId: string, fromBuildingId?: string, toBuildingId?: string) {
    const cur = vehicles.get(vehicleId);
    if (!cur) return null;
    const next: LifeVehicle = {
      ...cur,
      assignedCitizenId: citizenId,
      fromBuildingId,
      toBuildingId,
      status: "departed",
      updatedAt: new Date().toISOString(),
    };
    vehicles.set(vehicleId, next);
    publishLifeEvent("vehicle_assigned", {
      vehicleId,
      citizenId,
      fromBuildingId,
      toBuildingId,
    });
    return next;
  },

  setStatus(vehicleId: string, status: LifeVehicle["status"], buildingId?: string) {
    const cur = vehicles.get(vehicleId);
    if (!cur) return null;
    const next = { ...cur, status, updatedAt: new Date().toISOString(), toBuildingId: buildingId || cur.toBuildingId };
    vehicles.set(vehicleId, next);
    return next;
  },
};
