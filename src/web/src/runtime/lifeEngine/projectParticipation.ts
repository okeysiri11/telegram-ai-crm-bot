/**
 * Project participation — Sprint 29.2.
 */

import type { ProjectMemberRole, ProjectParticipant } from "./lifeTypes";
import { publishLifeEvent } from "./lifeEventEngine";

const byKey = new Map<string, ProjectParticipant>();

function key(projectId: string, citizenId: string) {
  return `${projectId}::${citizenId}`;
}

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const projectParticipation = {
  clear() {
    byKey.clear();
  },

  list(projectId?: string) {
    const all = [...byKey.values()];
    return projectId ? all.filter((p) => p.projectId === projectId) : all;
  },

  get(projectId: string, citizenId: string) {
    return byKey.get(key(projectId, citizenId));
  },

  join(input: {
    projectId: string;
    projectName: string;
    citizenId: string;
    role: ProjectMemberRole;
  }): ProjectParticipant {
    const existing = this.get(input.projectId, input.citizenId);
    if (existing) return existing;
    const member: ProjectParticipant = {
      id: uid("pp"),
      projectId: input.projectId,
      projectName: input.projectName,
      citizenId: input.citizenId,
      role: input.role,
      attendance: 0,
      participationScore: 0,
      assignments: [],
      contributions: [],
      joinedAt: new Date().toISOString(),
    };
    byKey.set(key(input.projectId, input.citizenId), member);
    publishLifeEvent("project_updated", {
      projectId: input.projectId,
      citizenId: input.citizenId,
      payload: { action: "joined", role: input.role, projectName: input.projectName },
    });
    return member;
  },

  setRole(projectId: string, citizenId: string, role: ProjectMemberRole) {
    const cur = this.get(projectId, citizenId);
    if (!cur) return null;
    const next = { ...cur, role };
    byKey.set(key(projectId, citizenId), next);
    publishLifeEvent("project_updated", {
      projectId,
      citizenId,
      payload: { action: "role_changed", role },
    });
    return next;
  },

  assign(projectId: string, citizenId: string, assignment: string) {
    const cur = this.get(projectId, citizenId);
    if (!cur) return null;
    const next = {
      ...cur,
      assignments: [assignment, ...cur.assignments].slice(0, 40),
      participationScore: cur.participationScore + 1,
    };
    byKey.set(key(projectId, citizenId), next);
    publishLifeEvent("project_updated", {
      projectId,
      citizenId,
      payload: { action: "assigned", assignment },
    });
    return next;
  },

  recordAttendance(projectId: string, citizenId: string) {
    const cur = this.get(projectId, citizenId);
    if (!cur) return null;
    const next = {
      ...cur,
      attendance: cur.attendance + 1,
      participationScore: cur.participationScore + 2,
    };
    byKey.set(key(projectId, citizenId), next);
    return next;
  },

  contribute(projectId: string, citizenId: string, detail: string) {
    const cur = this.get(projectId, citizenId);
    if (!cur) return null;
    const contribution = { id: uid("pc"), at: new Date().toISOString(), detail };
    const next = {
      ...cur,
      contributions: [contribution, ...cur.contributions].slice(0, 80),
      participationScore: cur.participationScore + 3,
    };
    byKey.set(key(projectId, citizenId), next);
    publishLifeEvent("project_collaboration" as const, {
      projectId,
      citizenId,
      message: detail,
      payload: { contributionId: contribution.id },
    });
    return next;
  },

  startProject(projectId: string, projectName: string, ownerCitizenId: string) {
    this.join({ projectId, projectName, citizenId: ownerCitizenId, role: "owner" });
    publishLifeEvent("project_started", {
      projectId,
      citizenId: ownerCitizenId,
      payload: { projectName },
    });
  },

  completeProject(projectId: string, citizenId?: string) {
    publishLifeEvent("project_completed", {
      projectId,
      citizenId,
      payload: { memberCount: this.list(projectId).length },
    });
  },
};
