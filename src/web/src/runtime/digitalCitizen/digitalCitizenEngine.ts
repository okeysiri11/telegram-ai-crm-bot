/**
 * Digital Citizen Engine — Sprint 29.1.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { DIGITAL_CITIZEN_VERSION } from "./citizenTypes";
import type {
  OrganizationRole,
  PresenceStatus,
  PersonalAiKind,
  CitizenPermissionScope,
} from "./citizenTypes";
import { citizenProfileService } from "./citizenProfileService";
import { organizationMembershipService } from "./organizationMembershipService";
import { citizenWorkspaceService } from "./citizenWorkspaceService";
import { personalAiRegistry } from "./personalAiRegistry";
import { presenceEngine } from "./presenceEngine";
import { activityEngine, citizenEvents } from "./citizenEvents";
import { cityCitizenBridge } from "./cityCitizenBridge";
import { citizenPermissions } from "./citizenPermissions";
import {
  seedDigitalCitizens,
  EDC_CITIZEN_OWNER,
  EDC_ORG_DEMO,
} from "./citizenSeed";

let booted = false;

function registerCommands() {
  commandRuntime.register({
    id: "edc_open",
    action: "open_digital_citizens",
    label: "Open Digital Citizens",
    kind: "navigate",
    keywords: ["citizen", "people", "hr", "digital"],
    route: "/digital-citizens",
    permission: "*",
  });
  commandRuntime.register({
    id: "edc_set_presence",
    action: "set_citizen_presence",
    label: "Set Citizen Presence",
    kind: "system",
    keywords: ["presence", "status", "online"],
    permission: "*",
    handler: async (_ctx, args) => {
      const id = String(args.citizenId || EDC_CITIZEN_OWNER);
      const status = String(args.status || "online") as PresenceStatus;
      const res = digitalCitizenEngine.setPresence(id, status);
      return { ok: Boolean(res), message: status };
    },
  });
}

export const digitalCitizenEngine = {
  version: DIGITAL_CITIZEN_VERSION,

  startup() {
    if (booted) return this.stats();
    commandRuntime.startup();
    businessNetworkEngine.startup();
    seedDigitalCitizens();
    registerCommands();
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "digital_citizen", ready: true, version: DIGITAL_CITIZEN_VERSION },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  createCitizen(input: Parameters<typeof citizenProfileService.create>[0]) {
    this.startup();
    const c = citizenProfileService.create(input);
    citizenWorkspaceService.ensure(c.id);
    citizenEvents.created(c.id);
    return c;
  },

  updateCitizen(id: string, patch: Parameters<typeof citizenProfileService.update>[1]) {
    this.startup();
    const c = citizenProfileService.update(id, patch);
    if (c) citizenEvents.updated(id);
    return c;
  },

  getCitizen(id: string) {
    this.startup();
    return citizenProfileService.get(id);
  },

  listCitizens() {
    this.startup();
    return citizenProfileService.list();
  },

  joinOrganization(input: Parameters<typeof organizationMembershipService.join>[0]) {
    this.startup();
    const m = organizationMembershipService.join(input);
    citizenProfileService.update(input.citizenId, { primaryOrgId: input.orgId });
    citizenEvents.joinedCompany(input.citizenId, input.orgId);
    return m;
  },

  leaveOrganization(memberId: string, reason?: string) {
    this.startup();
    const m = organizationMembershipService.leave(memberId, reason);
    if (m) citizenEvents.leftCompany(m.citizenId, m.orgId);
    return m;
  },

  setRole(memberId: string, role: OrganizationRole) {
    this.startup();
    const m = organizationMembershipService.setRole(memberId, role);
    if (m) citizenEvents.roleChanged(m.citizenId, role, m.orgId);
    return m;
  },

  listMemberships(citizenId?: string) {
    this.startup();
    return citizenId
      ? organizationMembershipService.listForCitizen(citizenId)
      : organizationMembershipService.list();
  },

  managerHierarchy(citizenId: string) {
    this.startup();
    const chain: string[] = [];
    let current = organizationMembershipService
      .listForCitizen(citizenId)
      .find((m) => m.active);
    const guard = new Set<string>();
    while (current?.managerCitizenId && !guard.has(current.managerCitizenId)) {
      chain.push(current.managerCitizenId);
      guard.add(current.managerCitizenId);
      current = organizationMembershipService
        .listForCitizen(current.managerCitizenId)
        .find((m) => m.active);
    }
    return {
      citizenId,
      managers: chain,
      reports: organizationMembershipService.reports(citizenId).map((m) => m.citizenId),
    };
  },

  workspace(citizenId: string) {
    this.startup();
    return citizenWorkspaceService.get(citizenId);
  },

  assignTask(citizenId: string, title: string, dueAt?: string, projectId?: string) {
    this.startup();
    const task = citizenWorkspaceService.addTask(citizenId, title, dueAt, projectId);
    citizenEvents.taskAssigned(citizenId, task.id);
    return task;
  },

  joinProject(citizenId: string, projectId: string, projectName: string, role?: string) {
    this.startup();
    const p = citizenWorkspaceService.assignProject(citizenId, { projectId, projectName, role });
    citizenEvents.projectJoined(citizenId, projectId);
    return p;
  },

  signDocument(citizenId: string, documentRef: string) {
    this.startup();
    citizenWorkspaceService.addDocument(citizenId, documentRef);
    citizenEvents.documentSigned(citizenId, documentRef);
    return true;
  },

  joinMeeting(citizenId: string, title: string) {
    this.startup();
    const ev = citizenWorkspaceService.addCalendarEvent(citizenId, {
      title,
      startsAt: new Date().toISOString(),
      endsAt: new Date(Date.now() + 3600_000).toISOString(),
      meeting: true,
    });
    this.setPresence(citizenId, "meeting");
    citizenEvents.meetingJoined(citizenId, ev.id);
    return ev;
  },

  registerAi(input: {
    kind: PersonalAiKind;
    name: string;
    ownerCitizenId?: string;
    orgId?: string;
  }) {
    this.startup();
    return personalAiRegistry.register(input);
  },

  assignAi(aiId: string, citizenId: string) {
    this.startup();
    const a = personalAiRegistry.assign(aiId, citizenId);
    if (a) citizenEvents.aiAssigned(citizenId, aiId);
    return a;
  },

  listAi(citizenId?: string) {
    this.startup();
    return citizenId ? personalAiRegistry.forCitizen(citizenId) : personalAiRegistry.list();
  },

  setPresence(citizenId: string, status: PresenceStatus, extra?: Parameters<typeof presenceEngine.set>[2]) {
    this.startup();
    const c = presenceEngine.set(citizenId, status, extra);
    if (c) citizenEvents.presenceChanged(citizenId, status);
    return c;
  },

  presenceSnapshot() {
    this.startup();
    return presenceEngine.snapshot();
  },

  activity(limit = 40, citizenId?: string) {
    this.startup();
    return activityEngine.list(limit, citizenId);
  },

  cityFacade(citizenId: string) {
    this.startup();
    return cityCitizenBridge.load(
      citizenId,
      citizenProfileService.list(),
      organizationMembershipService.list(),
      personalAiRegistry.list(),
    );
  },

  permissionsFor(citizenId: string, orgId = EDC_ORG_DEMO): CitizenPermissionScope[] {
    this.startup();
    const member =
      organizationMembershipService.listForCitizen(citizenId).find((m) => m.orgId === orgId && m.active) ||
      null;
    return citizenPermissions.scopesForMember(member, true);
  },

  permissions: citizenPermissions,

  stats() {
    return {
      version: DIGITAL_CITIZEN_VERSION,
      citizens: citizenProfileService.list().length,
      memberships: organizationMembershipService.list().filter((m) => m.active).length,
      departments: organizationMembershipService.listDepartments().length,
      aiAgents: personalAiRegistry.list().length,
      online: presenceEngine.onlineCount(),
      activities: activityEngine.list(200).length,
    };
  },

  inspectorSnapshot() {
    this.startup();
    return {
      version: DIGITAL_CITIZEN_VERSION,
      citizens: citizenProfileService.list(),
      memberships: organizationMembershipService.list(),
      departments: organizationMembershipService.listDepartments(),
      positions: organizationMembershipService.listPositions(),
      workspaces: citizenProfileService.list().map((c) => citizenWorkspaceService.get(c.id)),
      ai: personalAiRegistry.list(),
      presence: presenceEngine.snapshot(),
      activity: activityEngine.list(40),
      city: { owner: this.cityFacade(EDC_CITIZEN_OWNER) },
      stats: this.stats(),
    };
  },

  __resetForTests() {
    citizenProfileService.clear();
    organizationMembershipService.clear();
    citizenWorkspaceService.clear();
    personalAiRegistry.clear();
    activityEngine.clear();
    booted = false;
  },
};
