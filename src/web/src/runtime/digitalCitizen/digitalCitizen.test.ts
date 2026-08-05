import { beforeEach, describe, expect, it } from "vitest";
import {
  DIGITAL_CITIZEN_VERSION,
  digitalCitizenEngine,
  digitalCitizenApi,
  citizenPermissions,
  presenceEngine,
  PRESENCE_STATUSES,
  EDC_CITIZEN_OWNER,
  EDC_CITIZEN_MANAGER,
  EDC_CITIZEN_DEV,
  EDC_ORG_DEMO,
  activityEngine,
  organizationMembershipService,
} from "@/runtime/digitalCitizen";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { businessNetworkEngine } from "@/runtime/businessNetwork";

describe("Sprint 29.1 Digital Citizen Runtime", () => {
  beforeEach(() => {
    digitalCitizenEngine.__resetForTests();
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    digitalCitizenEngine.startup();
  });

  it("boots with seed citizens and version 29.1", () => {
    expect(DIGITAL_CITIZEN_VERSION).toBe("29.1");
    expect(digitalCitizenEngine.getCitizen(EDC_CITIZEN_OWNER)?.displayName).toBe("Owner Demo");
    expect(digitalCitizenEngine.stats().citizens).toBeGreaterThanOrEqual(3);
    expect(digitalCitizenEngine.listAi().length).toBeGreaterThanOrEqual(5);
  });

  it("supports multi-org membership and manager hierarchy", () => {
    const second = digitalCitizenEngine.createCitizen({
      displayName: "Partner Guest",
      identity: { email: "guest@northwind.test" },
    });
    digitalCitizenEngine.joinOrganization({
      citizenId: second.id,
      orgId: "org_northwind",
      role: "guest",
    });
    const memberships = digitalCitizenEngine.listMemberships(second.id);
    expect(memberships.length).toBeGreaterThanOrEqual(1);

    const hier = digitalCitizenEngine.managerHierarchy(EDC_CITIZEN_DEV);
    expect(hier.managers).toContain(EDC_CITIZEN_MANAGER);
    expect(hier.managers).toContain(EDC_CITIZEN_OWNER);
    expect(digitalCitizenEngine.managerHierarchy(EDC_CITIZEN_OWNER).reports).toContain(
      EDC_CITIZEN_MANAGER,
    );
  });

  it("changes roles and records employment history", () => {
    const mem = organizationMembershipService
      .listForCitizen(EDC_CITIZEN_DEV)
      .find((m) => m.active)!;
    digitalCitizenEngine.setRole(mem.id, "manager");
    expect(organizationMembershipService.get(mem.id)?.role).toBe("manager");
    expect(organizationMembershipService.employmentHistory(EDC_CITIZEN_DEV).length).toBeGreaterThan(
      1,
    );
  });

  it("enforces citizen permission scopes", () => {
    const ownerScopes = digitalCitizenEngine.permissionsFor(EDC_CITIZEN_OWNER);
    expect(ownerScopes).toContain("enterprise_admin");
    expect(citizenPermissions.canAccess("company", ownerScopes)).toBe(true);

    const guestScopes = citizenPermissions.scopesForMember(
      {
        id: "x",
        citizenId: "g",
        orgId: EDC_ORG_DEMO,
        role: "guest",
        active: true,
        joinedAt: new Date().toISOString(),
        history: [],
      },
      true,
    );
    expect(citizenPermissions.canAccess("department", guestScopes)).toBe(false);
    expect(citizenPermissions.canAccess("self", guestScopes)).toBe(true);
  });

  it("updates presence for city-compatible snapshot", () => {
    digitalCitizenEngine.setPresence(EDC_CITIZEN_DEV, "vacation", {
      locationLabel: "PTO",
    });
    expect(presenceEngine.get(EDC_CITIZEN_DEV)?.status).toBe("vacation");
    expect(PRESENCE_STATUSES).toContain("invisible");
    expect(digitalCitizenEngine.presenceSnapshot().some((p) => p.status === "vacation")).toBe(true);
  });

  it("workspace tasks projects bookmarks and documents", () => {
    const task = digitalCitizenEngine.assignTask(EDC_CITIZEN_OWNER, "Ship sprint 29.1");
    expect(task.title).toContain("29.1");
    digitalCitizenEngine.joinProject(EDC_CITIZEN_DEV, "proj_ebn", "EBN Integration", "contributor");
    digitalCitizenEngine.signDocument(EDC_CITIZEN_OWNER, "doc://acts/act-001");
    const ws = digitalCitizenEngine.workspace(EDC_CITIZEN_OWNER);
    expect(ws.tasks.some((t) => t.id === task.id)).toBe(true);
    expect(ws.documentRefs).toContain("doc://acts/act-001");
  });

  it("assigns personal AI and records activity", () => {
    const ai = digitalCitizenEngine.registerAi({
      kind: "assistant",
      name: "Temp Assistant",
      ownerCitizenId: EDC_CITIZEN_MANAGER,
    });
    digitalCitizenEngine.assignAi(ai.id, EDC_CITIZEN_MANAGER);
    expect(digitalCitizenEngine.listAi(EDC_CITIZEN_MANAGER).some((a) => a.id === ai.id)).toBe(true);
    expect(activityEngine.list(20).some((e) => e.name === "AIAssigned")).toBe(true);
  });

  it("publishes digital_citizen_update events", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "digital_citizen_update") seen.push(String(e.payload?.event || ""));
    });
    digitalCitizenEngine.updateCitizen(EDC_CITIZEN_OWNER, { bio: "Updated" });
    expect(seen).toContain("CitizenUpdated");
    unsub();
  });

  it("exposes city facade and command + API inventory", async () => {
    const facade = digitalCitizenEngine.cityFacade(EDC_CITIZEN_OWNER);
    expect(facade?.companyBusinessProfileId).toBeTruthy();
    expect(facade?.role).toBe("owner");
    expect(facade?.aiAssignmentIds.length).toBeGreaterThan(0);

    const cmd = await commandRuntime.execute("edc_open");
    expect(cmd.ok).toBe(true);
    const inv = await digitalCitizenApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
  });

  it("leaves organization and records activity", () => {
    const mem = organizationMembershipService
      .listForCitizen(EDC_CITIZEN_DEV)
      .find((m) => m.active)!;
    digitalCitizenEngine.leaveOrganization(mem.id, "transfer");
    expect(organizationMembershipService.get(mem.id)?.active).toBe(false);
    expect(activityEngine.list(20).some((e) => e.name === "CitizenLeftCompany")).toBe(true);
  });
});
