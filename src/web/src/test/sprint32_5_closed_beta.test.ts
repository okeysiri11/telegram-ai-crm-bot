/**
 * Sprint 32.5 — Closed Beta launch readiness (no new engines).
 */
import { describe, expect, it } from "vitest";
import { CITY_BUILDINGS } from "@/enterprise-city/cityCatalog";
import {
  CLOSED_BETA_META,
  CLOSED_BETA_SURFACES,
  CLOSED_BETA_VERSION,
} from "@/closed-beta/closedBetaCatalog";
import { deriveOwnerMetrics } from "@/enterprise-business/deriveOwnerMetrics";
import { deriveGodModeMetrics } from "@/enterprise-business/deriveGodModeMetrics";
import { OWNER_SUBSYSTEMS } from "@/platform-integration/ownerSubsystems";
import { webConfig } from "@/config/webConfig";

describe("Sprint 32.5 Closed Beta Launch Preparation", () => {
  it("web sprint and catalog version align", () => {
    expect(webConfig.sprint).toBe("33.1");
    expect(CLOSED_BETA_VERSION).toBe("32.5-closed-beta");
    expect(CLOSED_BETA_META.sprint).toBe("32.5");
  });

  it("city buildings open real modules (no # / no HR placeholder / security SoR)", () => {
    expect(CITY_BUILDINGS.every((b) => !b.route.includes("#"))).toBe(true);
    const security = CITY_BUILDINGS.find((b) => b.id === "security");
    const hr = CITY_BUILDINGS.find((b) => b.id === "hr");
    const marketing = CITY_BUILDINGS.find((b) => b.id === "marketing");
    expect(security?.route).toBe("/identity/security");
    expect(hr?.route).toBe("/identity/users");
    expect(marketing?.route).toContain("/production-studio");
    expect(hr?.route).not.toBe("/workspace/hr");
  });

  it("owner metrics avoid stub identity/live labels", () => {
    const cards = deriveOwnerMetrics();
    const ids = cards.map((c) => c.id);
    for (const id of ["users", "orgs", "security", "queues", "api", "database", "redis", "providers"]) {
      expect(ids).toContain(id);
    }
    expect(cards.some((c) => c.value === "identity" || c.value === "live")).toBe(false);
    const god = deriveGodModeMetrics();
    expect(god.some((c) => c.value === "identity" || c.value === "live")).toBe(false);
    expect(god.some((c) => c.id === "security")).toBe(true);
  });

  it("closed beta surfaces include security and first-entry journey", () => {
    const routes = CLOSED_BETA_SURFACES.map((s) => s.route);
    expect(routes).toContain("/owner");
    expect(routes).toContain("/city");
    expect(routes).toContain("/onboarding/first-entry");
    expect(routes).toContain("/identity/security");
    expect(routes).toContain("/auth/register");
    expect(OWNER_SUBSYSTEMS.some((s) => s.route === "/identity/security")).toBe(true);
  });
});
