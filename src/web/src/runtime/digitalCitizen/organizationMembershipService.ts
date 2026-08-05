/**
 * Organization membership — Sprint 29.1.
 */

import type {
  Department,
  EmploymentHistoryEntry,
  OrganizationMember,
  OrganizationRole,
  Position,
} from "./citizenTypes";

const members = new Map<string, OrganizationMember>();
const departments = new Map<string, Department>();
const positions = new Map<string, Position>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function hist(partial: Omit<EmploymentHistoryEntry, "id">): EmploymentHistoryEntry {
  return { id: uid("eh"), ...partial };
}

export const organizationMembershipService = {
  clear() {
    members.clear();
    departments.clear();
    positions.clear();
  },

  upsertDepartment(dept: Department) {
    departments.set(dept.id, dept);
    return dept;
  },

  upsertPosition(pos: Position) {
    positions.set(pos.id, pos);
    return pos;
  },

  listDepartments(orgId?: string) {
    const all = [...departments.values()];
    return orgId ? all.filter((d) => d.orgId === orgId) : all;
  },

  listPositions(orgId?: string) {
    const all = [...positions.values()];
    return orgId ? all.filter((p) => p.orgId === orgId) : all;
  },

  join(input: {
    citizenId: string;
    orgId: string;
    role: OrganizationRole;
    businessProfileId?: string;
    departmentId?: string;
    positionId?: string;
    managerCitizenId?: string;
    ownershipPct?: number;
  }): OrganizationMember {
    const existing = this.listForCitizen(input.citizenId).find(
      (m) => m.orgId === input.orgId && m.active,
    );
    if (existing) return existing;

    const now = new Date().toISOString();
    const member: OrganizationMember = {
      id: uid("om"),
      citizenId: input.citizenId,
      orgId: input.orgId,
      businessProfileId: input.businessProfileId,
      role: input.role,
      departmentId: input.departmentId,
      positionId: input.positionId,
      managerCitizenId: input.managerCitizenId,
      ownershipPct: input.ownershipPct,
      active: true,
      joinedAt: now,
      history: [
        hist({
          orgId: input.orgId,
          role: input.role,
          departmentId: input.departmentId,
          positionTitle: input.positionId
            ? positions.get(input.positionId)?.title
            : undefined,
          startedAt: now,
        }),
      ],
    };
    members.set(member.id, member);
    return member;
  },

  leave(memberId: string, reason?: string) {
    const cur = members.get(memberId);
    if (!cur || !cur.active) return null;
    const now = new Date().toISOString();
    const history = cur.history.map((h, i) =>
      i === 0 && !h.endedAt ? { ...h, endedAt: now, reason } : h,
    );
    const next: OrganizationMember = {
      ...cur,
      active: false,
      leftAt: now,
      history,
    };
    members.set(memberId, next);
    return next;
  },

  setRole(memberId: string, role: OrganizationRole) {
    const cur = members.get(memberId);
    if (!cur) return null;
    const now = new Date().toISOString();
    const history = [
      hist({
        orgId: cur.orgId,
        role,
        departmentId: cur.departmentId,
        startedAt: now,
      }),
      ...cur.history.map((h, i) => (i === 0 && !h.endedAt ? { ...h, endedAt: now } : h)),
    ];
    const next = { ...cur, role, history };
    members.set(memberId, next);
    return next;
  },

  setManager(memberId: string, managerCitizenId: string | undefined) {
    const cur = members.get(memberId);
    if (!cur) return null;
    const next = { ...cur, managerCitizenId };
    members.set(memberId, next);
    return next;
  },

  get(id: string) {
    return members.get(id);
  },

  list() {
    return [...members.values()];
  },

  listForCitizen(citizenId: string) {
    return this.list().filter((m) => m.citizenId === citizenId);
  },

  listForOrg(orgId: string) {
    return this.list().filter((m) => m.orgId === orgId && m.active);
  },

  /** Direct reports under a manager */
  reports(managerCitizenId: string) {
    return this.list().filter((m) => m.active && m.managerCitizenId === managerCitizenId);
  },

  employmentHistory(citizenId: string) {
    return this.listForCitizen(citizenId).flatMap((m) => m.history);
  },
};
