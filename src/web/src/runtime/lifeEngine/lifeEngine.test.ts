import { beforeEach, describe, expect, it } from "vitest";
import {
  LIFE_ENGINE_VERSION,
  lifeEngine,
  lifeEventEngine,
  activityTimeline,
  buildingOccupancy,
  lifeEngineApi,
} from "@/runtime/lifeEngine";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER, EDC_CITIZEN_DEV } from "@/runtime/digitalCitizen";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { workflowRuntime } from "@/runtime/workflowRuntime";

describe("Sprint 29.2 Enterprise Life Engine", () => {
  beforeEach(() => {
    lifeEngine.__resetForTests();
    digitalCitizenEngine.__resetForTests();
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    lifeEngine.startup();
  });

  it("boots with version 29.2 and seeds live occupancy", () => {
    expect(LIFE_ENGINE_VERSION).toBe("29.2");
    expect(lifeEngine.stats().version).toBe("29.2");
    const city = lifeEngine.cityRuntime();
    expect(city.citizens.length).toBeGreaterThanOrEqual(3);
    expect(city.occupancy.some((o) => o.occupants.length > 0)).toBe(true);
  });

  it("records life events and unified timelines", () => {
    lifeEngine.enterOffice(EDC_CITIZEN_OWNER, "crm");
    lifeEngine.startWork(EDC_CITIZEN_DEV, "developer");
    const events = lifeEventEngine.list(20);
    expect(events.some((e) => e.kind === "citizen_enters_office")).toBe(true);
    expect(activityTimeline.citizen(EDC_CITIZEN_OWNER).length).toBeGreaterThan(0);
    expect(activityTimeline.building("crm").length).toBeGreaterThan(0);
    expect(activityTimeline.unified(10).length).toBeGreaterThan(0);
  });

  it("tracks building occupancy from real presence", () => {
    lifeEngine.enterOffice(EDC_CITIZEN_OWNER, "hub");
    const occ = buildingOccupancy.snapshot("hub");
    expect(occ.employeeCount).toBeGreaterThanOrEqual(1);
    expect(occ.capacity).toBeGreaterThan(0);
    lifeEngine.leaveOffice(EDC_CITIZEN_OWNER, "hub");
    expect(buildingOccupancy.snapshot("hub").occupants.every((o) => o.citizenId !== EDC_CITIZEN_OWNER)).toBe(
      true,
    );
  });

  it("moves citizens between buildings", () => {
    lifeEngine.enterOffice(EDC_CITIZEN_DEV, "ai_studio");
    const mov = lifeEngine.move({
      kind: "office_to_office",
      citizenId: EDC_CITIZEN_DEV,
      fromBuildingId: "ai_studio",
      toBuildingId: "developer",
      purpose: "standup",
    });
    expect(mov.status).toBe("in_transit");
    const arrived = lifeEngine.arrive(mov.id);
    expect(arrived?.status).toBe("arrived");
    expect(buildingOccupancy.list("developer").some((o) => o.citizenId === EDC_CITIZEN_DEV)).toBe(true);
  });

  it("runs meetings and updates presence", () => {
    const m = lifeEngine.createMeeting({
      title: "Design review",
      hostCitizenId: EDC_CITIZEN_OWNER,
      attendeeIds: [EDC_CITIZEN_DEV],
      buildingId: "mission_control",
    });
    lifeEngine.startMeeting(m.id);
    expect(lifeEngine.meetings.active().length).toBeGreaterThanOrEqual(1);
    expect(digitalCitizenEngine.getCitizen(EDC_CITIZEN_OWNER)?.presence.status).toBe("meeting");
    lifeEngine.endMeeting(m.id);
    expect(lifeEventEngine.list(30).some((e) => e.kind === "meeting_ended")).toBe(true);
  });

  it("supports project participation and business interactions", () => {
    lifeEngine.projects.contribute("proj_platform", EDC_CITIZEN_DEV, "Shipped occupancy bridge");
    const p = lifeEngine.projects.get("proj_platform", EDC_CITIZEN_DEV);
    expect(p?.contributions.length).toBeGreaterThan(0);
    expect(p!.participationScore).toBeGreaterThan(0);

    lifeEngine.businessVisit(EDC_CITIZEN_OWNER, "biz_demo_corp", "marketplace", "biz_northwind");
    expect(lifeEngine.interactions.list().some((i) => i.kind === "business_visit")).toBe(true);
    lifeEngine.exchangeDocument(EDC_CITIZEN_OWNER, "doc://life/msa");
    expect(lifeEventEngine.list(40).some((e) => e.kind === "document_signed")).toBe(true);
  });

  it("maps live presence statuses", () => {
    lifeEngine.setLifePresence(EDC_CITIZEN_OWNER, "remote", "hub");
    expect(digitalCitizenEngine.getCitizen(EDC_CITIZEN_OWNER)?.presence.status).toBe("working");
    lifeEngine.setLifePresence(EDC_CITIZEN_OWNER, "travelling");
    expect(lifeEngine.cityRuntime().citizens.find((c) => c.id === EDC_CITIZEN_OWNER)?.presence).toBe(
      "travelling",
    );
  });

  it("bridges workflow completion into life events", async () => {
    await workflowRuntime.start("demo_parallel_ops", { via: "life_test" });
    await new Promise((r) => setTimeout(r, 30));
    const kinds = lifeEventEngine.list(50).map((e) => e.kind);
    expect(kinds.some((k) => k === "workflow_executed" || k === "workflow_completed")).toBe(true);
  });

  it("publishes life_engine_update on EventBus", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "life_engine_update") seen.push(String(e.payload?.kind || ""));
    });
    lifeEngine.enterOffice(EDC_CITIZEN_OWNER, "finance");
    expect(seen).toContain("citizen_enters_office");
    unsub();
  });

  it("exposes city runtime API and command", async () => {
    const city = lifeEngine.cityRuntime();
    expect(city.meetings).toBeTruthy();
    expect(city.vehicles.length).toBeGreaterThanOrEqual(1);
    expect(city.ai.length).toBeGreaterThan(0);
    const cmd = await commandRuntime.execute("life_open");
    expect(cmd.ok).toBe(true);
    const inv = await lifeEngineApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
  });
});
