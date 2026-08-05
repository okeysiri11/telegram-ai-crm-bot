/**
 * Location engine — Sprint 29.4.
 */

import type { LocationAssignment, LocationAssignmentKind, GeoLocation } from "./spatialTypes";
import { spatialRegistry } from "./spatialRegistry";
import { publishSpatialEvent } from "./spatialEvents";

const assignments = new Map<string, LocationAssignment>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function key(subjectKind: string, subjectId: string, kind: LocationAssignmentKind) {
  return `${subjectKind}:${subjectId}:${kind}`;
}

export const locationEngine = {
  clear() {
    assignments.clear();
  },

  list() {
    return [...assignments.values()];
  },

  forSubject(subjectKind: LocationAssignment["subjectKind"], subjectId: string) {
    return this.list().filter((a) => a.subjectKind === subjectKind && a.subjectId === subjectId);
  },

  getCurrent(subjectKind: LocationAssignment["subjectKind"], subjectId: string) {
    return assignments.get(key(subjectKind, subjectId, "current"));
  },

  assign(input: {
    subjectKind: LocationAssignment["subjectKind"];
    subjectId: string;
    kind: LocationAssignmentKind;
    entityId: string;
    dynamic?: GeoLocation;
    until?: string;
  }): LocationAssignment {
    const entity = spatialRegistry.get(input.entityId);
    const prev = this.getCurrent(input.subjectKind, input.subjectId);

    if (input.kind === "current" && prev && prev.entityId !== input.entityId) {
      const prevEntity = spatialRegistry.get(prev.entityId);
      if (prevEntity?.kind === "building" || prevEntity?.cityBuildingId) {
        publishSpatialEvent("LeftBuilding", {
          subjectId: input.subjectId,
          entityId: prev.entityId,
          buildingId: prevEntity.cityBuildingId || prev.entityId,
        });
      }
    }

    const assignment: LocationAssignment = {
      id: uid("loc"),
      subjectKind: input.subjectKind,
      subjectId: input.subjectId,
      kind: input.kind,
      entityId: input.entityId,
      since: new Date().toISOString(),
      until: input.until,
      dynamic: input.dynamic,
    };
    assignments.set(key(input.subjectKind, input.subjectId, input.kind), assignment);

    if (input.kind === "current") {
      publishSpatialEvent("LocationChanged", {
        subjectId: input.subjectId,
        entityId: input.entityId,
        subjectKind: input.subjectKind,
      });
      if (entity?.kind === "building" || entity?.cityBuildingId) {
        publishSpatialEvent("EnteredBuilding", {
          subjectId: input.subjectId,
          entityId: input.entityId,
          buildingId: entity.cityBuildingId || entity.id,
        });
      }
      const district = entity
        ? spatialRegistry.ancestors(entity.id).find((a) => a.kind === "district") ||
          (entity.kind === "district" ? entity : undefined)
        : undefined;
      if (district) {
        publishSpatialEvent("EnteredDistrict", {
          subjectId: input.subjectId,
          entityId: district.id,
          districtId: district.cityDistrictId || district.id,
        });
      }
    }

    if (input.kind === "assigned" && entity?.kind === "workspace") {
      publishSpatialEvent("AssignedWorkspace", {
        subjectId: input.subjectId,
        entityId: input.entityId,
      });
    }

    spatialRegistry.relate("assigned", input.subjectId, input.entityId);
    return assignment;
  },

  setDynamicPosition(
    subjectKind: LocationAssignment["subjectKind"],
    subjectId: string,
    geo: GeoLocation,
    nearEntityId?: string,
  ) {
    return this.assign({
      subjectKind,
      subjectId,
      kind: "dynamic",
      entityId: nearEntityId || "city_odessa",
      dynamic: geo,
    });
  },
};
