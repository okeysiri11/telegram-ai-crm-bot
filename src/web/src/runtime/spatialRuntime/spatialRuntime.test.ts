import { beforeEach, describe, expect, it } from "vitest";
import {
  SPATIAL_RUNTIME_VERSION,
  ODESSA_CITY,
  spatialRuntime,
  spatialPermissions,
  spatialEvents,
  spatialRuntimeApi,
  spatialRegistry,
  routingEngine,
  resolveSpatialBuildingId,
} from "@/runtime/spatialRuntime";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";

describe("Sprint 29.4 Enterprise Spatial Runtime", () => {
  beforeEach(() => {
    spatialRuntime.__resetForTests();
    assetRuntime.__resetForTests();
    lifeEngine.__resetForTests();
    digitalCitizenEngine.__resetForTests();
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    spatialRuntime.startup();
  });

  it("boots Odessa twin with hierarchy and version 29.4", () => {
    expect(SPATIAL_RUNTIME_VERSION).toBe("29.4");
    expect(spatialRuntime.get(ODESSA_CITY.id)?.kind).toBe("city");
    expect(spatialRuntime.list("country").length).toBeGreaterThanOrEqual(1);
    expect(spatialRuntime.list("building").length).toBeGreaterThanOrEqual(8);
    expect(spatialRuntime.list("district").length).toBeGreaterThanOrEqual(10);
    expect(spatialRuntime.stats().city).toBe("Odessa");
  });

  it("supports spatial hierarchy ancestors contains and district kinds", () => {
    const hub = resolveSpatialBuildingId("hub");
    const chain = spatialRuntime.ancestors(hub);
    expect(chain.some((e) => e.kind === "district")).toBe(true);
    expect(chain.some((e) => e.kind === "city")).toBe(true);
    expect(spatialRuntime.districts("business").length).toBeGreaterThanOrEqual(1);
    expect(spatialRuntime.districts("logistics").length).toBeGreaterThanOrEqual(1);
    expect(spatialRuntime.districts("medical").length).toBeGreaterThanOrEqual(1);
    expect(spatialRuntime.districts("residential").length).toBeGreaterThanOrEqual(1);
    expect(spatialRuntime.buildingsByDistrict("enterprise").length).toBeGreaterThan(0);
    expect(spatialRegistry.relations(hub, "contains").length + spatialRegistry.relations(undefined, "contains").length).toBeGreaterThan(0);
  });

  it("assigns locations and emits spatial events", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "spatial_runtime_update") seen.push(String(e.payload?.event || ""));
    });
    const entityId = resolveSpatialBuildingId("developer");
    spatialRuntime.assignLocation({
      subjectKind: "citizen",
      subjectId: EDC_CITIZEN_OWNER,
      kind: "current",
      entityId,
    });
    expect(spatialRuntime.currentLocation("citizen", EDC_CITIZEN_OWNER)?.entityId).toBe(entityId);
    spatialRuntime.assignLocation({
      subjectKind: "citizen",
      subjectId: EDC_CITIZEN_OWNER,
      kind: "home_office",
      entityId: "spv_remote",
    });
    spatialRuntime.assignLocation({
      subjectKind: "citizen",
      subjectId: EDC_CITIZEN_OWNER,
      kind: "meeting_room",
      entityId: resolveSpatialBuildingId("mission_control"),
    });
    expect(spatialRuntime.locationsFor("citizen", EDC_CITIZEN_OWNER).length).toBeGreaterThanOrEqual(2);
    expect(seen).toContain("LocationChanged");
    expect(seen).toContain("EnteredBuilding");
    expect(spatialEvents.list().some((e) => e.name === "BuildingRegistered")).toBe(true);
    unsub();
  });

  it("routes between buildings with distance and travel time", () => {
    const from = resolveSpatialBuildingId("hub");
    const to = resolveSpatialBuildingId("developer");
    const route = spatialRuntime.route(from, to);
    expect(route).toBeTruthy();
    expect(route!.distanceM).toBeGreaterThan(0);
    expect(route!.travelTimeSec).toBeGreaterThan(0);
    expect(route!.path.length).toBeGreaterThanOrEqual(2);
    expect(spatialRuntime.distance(from, to)).toBe(route!.distanceM);
    expect(routingEngine.listNodes().length).toBeGreaterThan(0);
  });

  it("enforces spatial permissions", () => {
    const admin = spatialPermissions.scopesForActor({ isAdmin: true, citizenId: EDC_CITIZEN_OWNER });
    expect(spatialPermissions.canAssignLocation(admin)).toBe(true);
    const guest = spatialPermissions.scopesForActor({ citizenId: "cit_stranger" });
    expect(spatialPermissions.canViewPrivateLocation(guest)).toBe(false);
    expect(spatialPermissions.canAccess("public", guest)).toBe(true);
  });

  it("integrates city query with life assets citizens and ebn", () => {
    const city = spatialRuntime.cityQuery();
    expect(city.stats.buildings).toBeGreaterThan(0);
    expect(Object.keys(city.buildingsByDistrict).length).toBeGreaterThan(0);
    expect(Object.keys(city.citizensByLocation).length).toBeGreaterThan(0);
    expect(Object.keys(city.assetsByBuilding).length).toBeGreaterThan(0);
    expect(city.companiesByBuilding.hub?.length).toBeGreaterThan(0);
    spatialRuntime.moveAsset("ast_drone_1", {
      kind: "building",
      buildingId: "mission_control",
      districtId: "enterprise",
    });
    expect(spatialEvents.list().some((e) => e.name === "MovedAsset")).toBe(true);
  });

  it("integrates command runtime and API inventory", async () => {
    const cmd = await commandRuntime.execute("spatial_open");
    expect(cmd.ok).toBe(true);
    const inv = await spatialRuntimeApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
  });
});
