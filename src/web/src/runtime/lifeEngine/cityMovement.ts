/**
 * City movement model — Sprint 29.2.
 * Runtime only (no rendering).
 */

import type { CityMovement, MovementKind } from "./lifeTypes";
import { publishLifeEvent } from "./lifeEventEngine";
import { buildingOccupancy } from "./buildingOccupancy";

const movements = new Map<string, CityMovement>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const cityMovement = {
  clear() {
    movements.clear();
  },

  list() {
    return [...movements.values()].sort((a, b) => b.startedAt.localeCompare(a.startedAt));
  },

  get(id: string) {
    return movements.get(id);
  },

  start(input: {
    kind: MovementKind;
    actorCitizenId?: string;
    actorAiId?: string;
    vehicleId?: string;
    fromBuildingId?: string;
    toBuildingId?: string;
    purpose?: string;
  }): CityMovement {
    if (input.actorCitizenId && input.fromBuildingId) {
      buildingOccupancy.leaveBuilding(input.fromBuildingId, input.actorCitizenId);
    }
    const move: CityMovement = {
      id: uid("mov"),
      kind: input.kind,
      actorCitizenId: input.actorCitizenId,
      actorAiId: input.actorAiId,
      vehicleId: input.vehicleId,
      fromBuildingId: input.fromBuildingId,
      toBuildingId: input.toBuildingId,
      startedAt: new Date().toISOString(),
      status: "in_transit",
      purpose: input.purpose,
    };
    movements.set(move.id, move);

    publishLifeEvent("citizen_moved", {
      citizenId: input.actorCitizenId,
      aiId: input.actorAiId,
      vehicleId: input.vehicleId,
      fromBuildingId: input.fromBuildingId,
      toBuildingId: input.toBuildingId,
      buildingId: input.fromBuildingId,
      message: input.purpose,
      payload: { movementId: move.id, kind: input.kind },
    });

    if (input.vehicleId) {
      publishLifeEvent("vehicle_departed", {
        vehicleId: input.vehicleId,
        citizenId: input.actorCitizenId,
        fromBuildingId: input.fromBuildingId,
        toBuildingId: input.toBuildingId,
        payload: { movementId: move.id },
      });
    }

    return move;
  },

  arrive(movementId: string) {
    const cur = movements.get(movementId);
    if (!cur || cur.status !== "in_transit") return null;
    const next: CityMovement = {
      ...cur,
      status: "arrived",
      arrivedAt: new Date().toISOString(),
    };
    movements.set(movementId, next);

    if (cur.actorCitizenId && cur.toBuildingId) {
      buildingOccupancy.enter({
        buildingId: cur.toBuildingId,
        citizenId: cur.actorCitizenId,
        kind: "employee",
      });
    }
    if (cur.actorAiId && cur.toBuildingId) {
      buildingOccupancy.enter({
        buildingId: cur.toBuildingId,
        aiId: cur.actorAiId,
        kind: "ai",
      });
    }

    publishLifeEvent("citizen_moved", {
      citizenId: cur.actorCitizenId,
      aiId: cur.actorAiId,
      vehicleId: cur.vehicleId,
      fromBuildingId: cur.fromBuildingId,
      toBuildingId: cur.toBuildingId,
      buildingId: cur.toBuildingId,
      payload: { movementId, phase: "arrived" },
    });

    if (cur.vehicleId) {
      publishLifeEvent("vehicle_arrived", {
        vehicleId: cur.vehicleId,
        citizenId: cur.actorCitizenId,
        buildingId: cur.toBuildingId,
        payload: { movementId },
      });
    }

    return next;
  },

  inTransit() {
    return this.list().filter((m) => m.status === "in_transit");
  },
};
