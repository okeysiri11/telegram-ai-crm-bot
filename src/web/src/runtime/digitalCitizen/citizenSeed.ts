/**
 * Digital Citizen seed — Sprint 29.1.
 * Links people to EBN Demo Corp business profile.
 */

import { EBN_HOME_PROFILE_ID } from "@/runtime/businessNetwork";
import { citizenProfileService } from "./citizenProfileService";
import { organizationMembershipService } from "./organizationMembershipService";
import { citizenWorkspaceService } from "./citizenWorkspaceService";
import { personalAiRegistry } from "./personalAiRegistry";
import { presenceEngine } from "./presenceEngine";

export const EDC_ORG_DEMO = "org_demo_corp";
export const EDC_CITIZEN_OWNER = "cit_owner_demo";
export const EDC_CITIZEN_MANAGER = "cit_mgr_ops";
export const EDC_CITIZEN_DEV = "cit_dev_alex";

export function seedDigitalCitizens() {
  if (citizenProfileService.get(EDC_CITIZEN_OWNER)) return;

  organizationMembershipService.upsertDepartment({
    id: "dept_exec",
    orgId: EDC_ORG_DEMO,
    name: "Executive",
  });
  organizationMembershipService.upsertDepartment({
    id: "dept_eng",
    orgId: EDC_ORG_DEMO,
    name: "Engineering",
    parentDepartmentId: "dept_exec",
  });
  organizationMembershipService.upsertPosition({
    id: "pos_ceo",
    orgId: EDC_ORG_DEMO,
    title: "Chief Executive Officer",
    departmentId: "dept_exec",
    level: 1,
  });
  organizationMembershipService.upsertPosition({
    id: "pos_eng_mgr",
    orgId: EDC_ORG_DEMO,
    title: "Engineering Manager",
    departmentId: "dept_eng",
    level: 2,
  });
  organizationMembershipService.upsertPosition({
    id: "pos_dev",
    orgId: EDC_ORG_DEMO,
    title: "Software Engineer",
    departmentId: "dept_eng",
    level: 3,
  });

  citizenProfileService.create({
    id: EDC_CITIZEN_OWNER,
    displayName: "Owner Demo",
    firstName: "Owner",
    lastName: "Demo",
    title: "CEO",
    status: "active",
    verification: "verified",
    identity: { email: "owner@demo.corp", userId: "owner_demo" },
    primaryOrgId: EDC_ORG_DEMO,
    preferences: { locale: "en", timezone: "Europe/Kyiv", notifyEmail: true, notifyPush: true },
    presence: { status: "online", since: new Date().toISOString(), cityBuildingId: "hub", officeId: "hq_floor_1" },
    metadata: { seed: true },
  });

  citizenProfileService.create({
    id: EDC_CITIZEN_MANAGER,
    displayName: "Ops Manager",
    firstName: "Ops",
    lastName: "Manager",
    title: "Engineering Manager",
    status: "active",
    verification: "verified",
    identity: { email: "ops@demo.corp" },
    primaryOrgId: EDC_ORG_DEMO,
    presence: {
      status: "working",
      since: new Date().toISOString(),
      cityBuildingId: "developer",
      officeId: "eng_wing",
    },
  });

  citizenProfileService.create({
    id: EDC_CITIZEN_DEV,
    displayName: "Alex Developer",
    firstName: "Alex",
    lastName: "Developer",
    title: "Software Engineer",
    status: "active",
    verification: "pending",
    identity: { email: "alex@demo.corp" },
    primaryOrgId: EDC_ORG_DEMO,
    presence: {
      status: "busy",
      since: new Date().toISOString(),
      cityBuildingId: "ai_studio",
      locationLabel: "AI Studio desk",
    },
  });

  organizationMembershipService.join({
    citizenId: EDC_CITIZEN_OWNER,
    orgId: EDC_ORG_DEMO,
    role: "owner",
    businessProfileId: EBN_HOME_PROFILE_ID,
    departmentId: "dept_exec",
    positionId: "pos_ceo",
    ownershipPct: 100,
  });

  organizationMembershipService.join({
    citizenId: EDC_CITIZEN_MANAGER,
    orgId: EDC_ORG_DEMO,
    role: "manager",
    businessProfileId: EBN_HOME_PROFILE_ID,
    departmentId: "dept_eng",
    positionId: "pos_eng_mgr",
    managerCitizenId: EDC_CITIZEN_OWNER,
  });

  organizationMembershipService.join({
    citizenId: EDC_CITIZEN_DEV,
    orgId: EDC_ORG_DEMO,
    role: "member",
    businessProfileId: EBN_HOME_PROFILE_ID,
    departmentId: "dept_eng",
    positionId: "pos_dev",
    managerCitizenId: EDC_CITIZEN_MANAGER,
  });

  const execAi = personalAiRegistry.register({
    kind: "executive",
    name: "Executive AI",
    description: "CEO briefing assistant",
    ownerCitizenId: EDC_CITIZEN_OWNER,
    orgId: EDC_ORG_DEMO,
  });
  personalAiRegistry.assign(execAi.id, EDC_CITIZEN_OWNER);

  const devAi = personalAiRegistry.register({
    kind: "developer",
    name: "Developer AI",
    ownerCitizenId: EDC_CITIZEN_DEV,
    orgId: EDC_ORG_DEMO,
  });
  personalAiRegistry.assign(devAi.id, EDC_CITIZEN_DEV);

  personalAiRegistry.register({
    kind: "sales",
    name: "Sales AI",
    orgId: EDC_ORG_DEMO,
  });
  personalAiRegistry.register({
    kind: "finance",
    name: "Finance AI",
    orgId: EDC_ORG_DEMO,
  });
  personalAiRegistry.register({
    kind: "legal",
    name: "Legal AI",
    orgId: EDC_ORG_DEMO,
  });
  personalAiRegistry.register({
    kind: "personal",
    name: "Personal AI",
    ownerCitizenId: EDC_CITIZEN_MANAGER,
  });

  citizenWorkspaceService.addTask(EDC_CITIZEN_OWNER, "Review morning brief", undefined, "proj_platform");
  citizenWorkspaceService.assignProject(EDC_CITIZEN_OWNER, {
    projectId: "proj_platform",
    projectName: "ADOS Platform",
    role: "sponsor",
  });
  citizenWorkspaceService.addBookmark(EDC_CITIZEN_OWNER, "Dashboard", "/dashboard", true);
  citizenWorkspaceService.addBookmark(EDC_CITIZEN_OWNER, "Business Network", "/business-network", true);
  citizenWorkspaceService.addDocument(EDC_CITIZEN_OWNER, "doc://contracts/msa-2026-northwind");
  citizenWorkspaceService.addCalendarEvent(EDC_CITIZEN_OWNER, {
    title: "Executive standup",
    startsAt: new Date().toISOString(),
    endsAt: new Date(Date.now() + 30 * 60_000).toISOString(),
    meeting: true,
  });

  presenceEngine.set(EDC_CITIZEN_OWNER, "online", {
    cityBuildingId: "hub",
    officeId: "hq_floor_1",
    locationLabel: "Hub Plaza",
  });
}
