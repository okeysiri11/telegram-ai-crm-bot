/**
 * Building occupancy — Sprint 29.2.
 * Derived from real citizen presence + life movements (no scripted animation).
 */

import type { BuildingOccupancy, BuildingOccupant, OccupantKind } from "./lifeTypes";

const capacityByBuilding: Record<string, number> = {
  hub: 40,
  crm: 24,
  erp: 20,
  ai_studio: 16,
  developer: 28,
  production: 30,
  marketplace: 20,
  business_network: 18,
  digital_citizens: 22,
  mission_control: 12,
  finance: 16,
  knowledge: 20,
  default: 25,
};

const occupants = new Map<string, BuildingOccupant>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const buildingOccupancy = {
  clear() {
    occupants.clear();
  },

  capacity(buildingId: string) {
    return capacityByBuilding[buildingId] ?? capacityByBuilding.default!;
  },

  setCapacity(buildingId: string, capacity: number) {
    capacityByBuilding[buildingId] = Math.max(1, capacity);
  },

  enter(input: {
    buildingId: string;
    citizenId?: string;
    aiId?: string;
    kind: OccupantKind;
    meetingId?: string;
  }) {
    // One slot per citizen/ai per building
    for (const [id, o] of occupants) {
      if (input.citizenId && o.citizenId === input.citizenId) occupants.delete(id);
      if (input.aiId && o.aiId === input.aiId) occupants.delete(id);
    }
    const occ: BuildingOccupant = {
      id: uid("occ"),
      buildingId: input.buildingId,
      citizenId: input.citizenId,
      aiId: input.aiId,
      kind: input.kind,
      since: new Date().toISOString(),
      meetingId: input.meetingId,
    };
    occupants.set(occ.id, occ);
    return occ;
  },

  leave(citizenId?: string, aiId?: string) {
    let removed = 0;
    for (const [id, o] of occupants) {
      if ((citizenId && o.citizenId === citizenId) || (aiId && o.aiId === aiId)) {
        occupants.delete(id);
        removed += 1;
      }
    }
    return removed;
  },

  leaveBuilding(buildingId: string, citizenId: string) {
    for (const [id, o] of occupants) {
      if (o.buildingId === buildingId && o.citizenId === citizenId) {
        occupants.delete(id);
        return true;
      }
    }
    return false;
  },

  list(buildingId?: string) {
    const all = [...occupants.values()];
    return buildingId ? all.filter((o) => o.buildingId === buildingId) : all;
  },

  snapshot(buildingId: string): BuildingOccupancy {
    const list = this.list(buildingId);
    const employeeCount = list.filter((o) => o.kind === "employee").length;
    const visitorCount = list.filter((o) => o.kind === "visitor").length;
    const meetingCount = new Set(list.filter((o) => o.meetingId).map((o) => o.meetingId)).size;
    const activityLabel =
      meetingCount > 0
        ? `${meetingCount} meeting(s)`
        : list.length > 0
          ? `${list.length} present`
          : "Quiet";
    return {
      buildingId,
      capacity: this.capacity(buildingId),
      occupants: list,
      employeeCount,
      visitorCount,
      meetingCount,
      activityLabel,
    };
  },

  allSnapshots(buildingIds: string[]): BuildingOccupancy[] {
    const ids = new Set([...buildingIds, ...this.list().map((o) => o.buildingId)]);
    return [...ids].map((id) => this.snapshot(id));
  },
};
