import { beforeEach, describe, expect, it } from "vitest";
import {
  INTERACTION_RUNTIME_VERSION,
  interactionRuntime,
  interactionPermissions,
  interactionEvents,
  interactionRuntimeApi,
  interactionCache,
} from "@/runtime/interactionRuntime";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID } from "@/runtime/businessNetwork";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";

describe("Sprint 29.6 Enterprise Interaction Runtime", () => {
  beforeEach(() => {
    interactionRuntime.__resetForTests();
    cityVisualizationRuntime.__resetForTests();
    spatialRuntime.__resetForTests();
    assetRuntime.__resetForTests();
    lifeEngine.__resetForTests();
    digitalCitizenEngine.__resetForTests();
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
    interactionRuntime.startup();
  });

  it("boots catalog from real runtimes with version 29.6", () => {
    expect(INTERACTION_RUNTIME_VERSION).toBe("29.6");
    expect(interactionRuntime.session()?.active).toBe(true);
    expect(interactionRuntime.catalog().length).toBeGreaterThan(10);
    expect(interactionRuntime.catalog().some((t) => t.kind === "building")).toBe(true);
    expect(interactionRuntime.catalog().some((t) => t.kind === "citizen")).toBe(true);
    expect(interactionRuntime.catalog().some((t) => t.kind === "company")).toBe(true);
  });

  it("selects single multi area and hierarchy", () => {
    const hub = interactionRuntime.select("building", "hub");
    expect(hub?.id).toBe("hub");
    expect(interactionRuntime.selection().mode).toBe("single");

    interactionRuntime.toggleSelect("building", "developer");
    expect(interactionRuntime.selection().mode).toBe("multi");
    expect(interactionRuntime.selection().targets.length).toBeGreaterThanOrEqual(1);

    const area = interactionRuntime.selectArea({ minX: 0, minY: 0, maxX: 100, maxY: 100 });
    expect(area.mode).toBe("area");
    expect(area.targets.length).toBeGreaterThan(0);

    const hier = interactionRuntime.selectHierarchy("district", "enterprise");
    expect(hier?.mode).toBe("hierarchy");
    expect(hier!.targets.length).toBeGreaterThan(0);
  });

  it("searches navigates and discovers businesses", () => {
    const hits = interactionRuntime.search("Demo");
    expect(hits.some((h) => h.target.kind === "company" || h.score > 0)).toBe(true);
    const nearby = interactionRuntime.nearby("hub");
    expect(nearby.length).toBeGreaterThan(0);
    const biz = interactionRuntime.businessDiscovery();
    expect(biz.some((h) => h.target.id === EBN_HOME_PROFILE_ID)).toBe(true);
    const jump = interactionRuntime.quickJump("building", "developer");
    expect(jump?.path).toBeTruthy();
    expect(interactionRuntime.navigationHistory().length).toBeGreaterThan(0);
  });

  it("executes real context actions and permissions", () => {
    interactionRuntime.select("building", "hub");
    const meeting = interactionRuntime.execute("create_meeting", undefined, {
      title: "Interaction Sync",
      hostCitizenId: EDC_CITIZEN_OWNER,
    });
    expect(meeting.ok).toBe(true);

    const task = interactionRuntime.execute("assign_task", undefined, {
      citizenId: EDC_CITIZEN_OWNER,
      title: "Review interactions",
    });
    expect(task.ok).toBe(true);

    const guest = interactionPermissions.scopesForActor({ citizenId: "cit_stranger" });
    expect(interactionPermissions.canExecuteAction("invite_partner", guest)).toBe(false);
    const admin = interactionPermissions.scopesForActor({ isAdmin: true, citizenId: EDC_CITIZEN_OWNER });
    expect(interactionPermissions.canExecuteAction("start_workflow", admin)).toBe(true);

    const opened = interactionRuntime.open("company", EBN_HOME_PROFILE_ID);
    expect(opened.ok).toBe(true);
  });

  it("publishes interaction events and caches state", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "interaction_runtime_update") seen.push(String(e.payload?.event || ""));
    });
    interactionRuntime.select("citizen", EDC_CITIZEN_OWNER);
    interactionRuntime.execute("navigate", undefined, { path: "/life-engine" });
    expect(seen).toContain("ObjectSelected");
    expect(seen).toContain("ActionExecuted");
    expect(interactionCache.stats().revision).toBeGreaterThan(0);
    unsub();
  });

  it("integrates command runtime and API inventory", async () => {
    const cmd = await commandRuntime.execute("interaction_open");
    expect(cmd.ok).toBe(true);
    const inv = await interactionRuntimeApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
  });
});
