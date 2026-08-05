/**
 * Unified activity timeline — Sprint 29.2.
 */

import type { LifeEvent, TimelineEntry, TimelineSubjectKind } from "./lifeTypes";
import { lifeEventEngine } from "./lifeEventEngine";

function toEntries(event: LifeEvent): TimelineEntry[] {
  const out: TimelineEntry[] = [];
  const push = (subjectKind: TimelineSubjectKind, subjectId: string) => {
    out.push({ ...event, subjectKind, subjectId });
  };
  if (event.citizenId) push("citizen", event.citizenId);
  if (event.companyId) push("company", event.companyId);
  if (event.projectId) push("project", event.projectId);
  if (event.aiId) push("ai", event.aiId);
  const building = event.buildingId || event.toBuildingId;
  if (building) push("building", building);
  if (!out.length) push("company", "platform");
  return out;
}

export const activityTimeline = {
  forSubject(subjectKind: TimelineSubjectKind, subjectId: string, limit = 40): TimelineEntry[] {
    return lifeEventEngine
      .list(200)
      .flatMap(toEntries)
      .filter((e) => e.subjectKind === subjectKind && e.subjectId === subjectId)
      .slice(0, limit);
  },

  company(companyId: string, limit = 40) {
    return this.forSubject("company", companyId, limit);
  },

  citizen(citizenId: string, limit = 40) {
    return this.forSubject("citizen", citizenId, limit);
  },

  project(projectId: string, limit = 40) {
    return this.forSubject("project", projectId, limit);
  },

  ai(aiId: string, limit = 40) {
    return this.forSubject("ai", aiId, limit);
  },

  building(buildingId: string, limit = 40) {
    return this.forSubject("building", buildingId, limit);
  },

  unified(limit = 80): TimelineEntry[] {
    return lifeEventEngine.list(limit).flatMap(toEntries).slice(0, limit);
  },
};
