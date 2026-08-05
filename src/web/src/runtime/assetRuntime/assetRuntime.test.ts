import { beforeEach, describe, expect, it } from "vitest";
import {
  ASSET_RUNTIME_VERSION,
  assetRuntime,
  assetPermissions,
  assetEvents,
  assetRuntimeApi,
} from "@/runtime/assetRuntime";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER, EDC_CITIZEN_DEV } from "@/runtime/digitalCitizen";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID, EBN_PARTNER_PROFILE_ID } from "@/runtime/businessNetwork";
import { lifeEngine } from "@/runtime/lifeEngine";
import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";

describe("Sprint 29.3 Enterprise Asset Runtime", () => {
  beforeEach(() => {
    assetRuntime.__resetForTests();
    lifeEngine.__resetForTests();
    digitalCitizenEngine.__resetForTests();
    businessNetworkEngine.__resetForTests();
    commandRuntime.startup();
    assetRuntime.startup();
  });

  it("boots with seeded asset catalog and version 29.3", () => {
    expect(ASSET_RUNTIME_VERSION).toBe("29.3");
    expect(assetRuntime.get("ast_hq_hub")?.type).toBe("headquarters");
    expect(assetRuntime.stats().assets).toBeGreaterThanOrEqual(10);
    expect(assetRuntime.stats().types).toBeGreaterThanOrEqual(8);
  });

  it("supports CRUD register and lifecycle transitions", () => {
    const created = assetRuntime.create({
      type: "computer",
      profile: { name: "Spare Laptop" },
      ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
      location: { kind: "building", buildingId: "developer" },
    });
    expect(created.status).toBe("draft");
    assetRuntime.register(created.id);
    expect(assetRuntime.get(created.id)?.lifecycle.phase).toBe("registered");
    assetRuntime.setLifecycle(created.id, "in_use");
    assetRuntime.maintain(created.id, "Battery swap");
    expect(assetRuntime.get(created.id)?.status).toBe("maintenance");
    expect(assetRuntime.get(created.id)?.available).toBe(false);
    assetRuntime.archive(created.id);
    expect(assetEvents.list().some((e) => e.name === "AssetArchived")).toBe(true);
  });

  it("assigns and transfers ownership with permissions", () => {
    const assign = assetRuntime.assign("ast_van_1", { citizenId: EDC_CITIZEN_OWNER });
    expect(assign.ok).toBe(true);
    expect(assetRuntime.get("ast_van_1")?.assignedCitizenId).toBe(EDC_CITIZEN_OWNER);

    const asset = assetRuntime.get("ast_van_1")!;
    const scopes = assetPermissions.scopesForActor({
      asset,
      citizenId: EDC_CITIZEN_OWNER,
      isAdmin: true,
    });
    expect(assetPermissions.canTransfer(scopes)).toBe(true);
    expect(assetPermissions.canAccess("owner", scopes)).toBe(true);

    const guestScopes = assetPermissions.scopesForActor({
      asset,
      citizenId: "cit_stranger",
    });
    expect(assetPermissions.canTransfer(guestScopes)).toBe(false);

    const tr = assetRuntime.transfer(
      "ast_digital_pack",
      { kind: "partner", companyId: EBN_PARTNER_PROFILE_ID, partnerCompanyId: EBN_PARTNER_PROFILE_ID },
      EDC_CITIZEN_OWNER,
      "channel",
    );
    expect(tr.ok).toBe(true);
    expect(assetRuntime.get("ast_digital_pack")?.ownership.kind).toBe("partner");
  });

  it("tracks location moves and city queries", () => {
    assetRuntime.move("ast_drone_1", {
      kind: "building",
      buildingId: "mission_control",
      districtId: "enterprise",
      x: 50,
      y: 50,
    });
    expect(assetRuntime.assetsByBuilding("mission_control").some((a) => a.id === "ast_drone_1")).toBe(
      true,
    );
    const city = assetRuntime.cityQuery();
    expect(city.totals.assets).toBeGreaterThan(0);
    expect(city.byCompany[EBN_HOME_PROFILE_ID]?.length).toBeGreaterThan(0);
    expect(city.byCitizen[EDC_CITIZEN_DEV]?.length).toBeGreaterThan(0);
    expect(Object.keys(city.byDistrict).length).toBeGreaterThan(0);
  });

  it("publishes asset_runtime_update events", () => {
    const seen: string[] = [];
    const unsub = enterpriseEventBus.subscribe((e) => {
      if (e.type === "asset_runtime_update") seen.push(String(e.payload?.event || ""));
    });
    assetRuntime.create({
      type: "document",
      profile: { name: "Temp Doc" },
      ownership: { kind: "citizen", citizenId: EDC_CITIZEN_OWNER },
      location: { kind: "virtual" },
    });
    expect(seen).toContain("AssetCreated");
    unsub();
  });

  it("integrates with command runtime and API inventory", async () => {
    const cmd = await commandRuntime.execute("asset_open");
    expect(cmd.ok).toBe(true);
    const inv = await assetRuntimeApi.inventory();
    expect(inv.version || (inv as { stats?: { version: string } }).stats?.version).toBeTruthy();
  });
});
