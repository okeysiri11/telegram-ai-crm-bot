/**
 * Sprint 31.0 — Closed Beta integration tests.
 */
import { describe, expect, it } from "vitest";
import {
  CLOSED_BETA_META,
  CLOSED_BETA_SURFACES,
  assertClosedBetaSurfacesReachable,
} from "./closedBetaCatalog";
import { ENTERPRISE_RU_SIDEBAR } from "@/navigation/enterpriseRuNav";
import { homeRouteForRole, mapToRoleHomeId, postAuthDestination } from "@/navigation/roleHome";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";
import { resetFirstEntry, markFirstEntryComplete, saveFirstEntry } from "@/onboarding/firstEntryStore";

const REGISTERED = [
  "/login",
  "/onboarding/first-entry",
  "/owner",
  "/admin",
  "/dashboards/manager",
  "/dashboards/employee",
  "/dashboards/client",
  "/dashboards/dealer",
  "/crm",
  "/projects",
  "/knowledge",
  "/calendar",
  "/notifications",
  "/documents",
  "/marketplace",
  "/ai-studio",
  "/production-studio",
  "/city",
  "/platform-builder/runtime",
  "/ai-agents",
  "/orchestrator",
  "/command-center",
  "/settings",
  "/identity/profile",
  "/health",
  "/search",
  "/dashboard",
  "/desktop",
  "/analytics",
  "/erp",
  "/tasks",
  "/auth/register",
  "/enterprise-city",
  "/identity/security",
];

describe("Sprint 31.0 Closed Beta RC", () => {
  it("maps all closed beta surfaces to registered routes", () => {
    expect(CLOSED_BETA_META.sprint).toBe("32.5");
    const check = assertClosedBetaSurfacesReachable(REGISTERED);
    expect(check.missing).toEqual([]);
    expect(check.ok).toBe(true);
    expect(CLOSED_BETA_SURFACES.length).toBeGreaterThanOrEqual(20);
  });

  it("role homes cover Owner Admin Manager Employee Client Dealer", () => {
    expect(homeRouteForRole("owner")).toBe("/owner");
    expect(homeRouteForRole("administrator")).toBe("/admin");
    expect(homeRouteForRole("manager")).toBe("/dashboards/manager");
    expect(homeRouteForRole("employee")).toBe("/dashboards/employee");
    expect(homeRouteForRole("client")).toBe("/dashboards/client");
    expect(homeRouteForRole("dealer")).toBe("/dashboards/dealer");
    expect(mapToRoleHomeId("business_owner")).toBe("owner");
    expect(mapToRoleHomeId("administrator")).toBe("administrator");
  });

  it("first-entry catalog includes platform roles", () => {
    const ids = firstEntryRoleCatalog.list().map((r) => r.id);
    expect(ids).toEqual(
      expect.arrayContaining(["business_owner", "administrator", "manager", "employee", "client"]),
    );
  });

  it("postAuthDestination gates first-run then role home", () => {
    resetFirstEntry();
    expect(postAuthDestination("owner")).toBe("/onboarding/first-entry");
    saveFirstEntry({ roleId: "manager", companyName: "Beta Co" });
    markFirstEntryComplete();
    expect(postAuthDestination("manager")).toBe("/dashboards/manager");
  });

  it("sidebar has no duplicate marketing twin and finance is live", () => {
    const finance = ENTERPRISE_RU_SIDEBAR.find((i) => i.id === "finance");
    expect(finance?.route).toBe("/analytics");
    expect(ENTERPRISE_RU_SIDEBAR.some((i) => i.id === "marketing")).toBe(false);
    expect(ENTERPRISE_RU_SIDEBAR.some((i) => i.id === "ai_studio")).toBe(true);
    for (const item of ENTERPRISE_RU_SIDEBAR) {
      expect(item.route.startsWith("/")).toBe(true);
    }
  });

  it("exports manager and employee dashboards", async () => {
    const mod = await import("@/dashboard/RoleOpsDashboards");
    expect(typeof mod.ManagerDashboardPage).toBe("function");
    expect(typeof mod.EmployeeDashboardPage).toBe("function");
  }, 15_000);
});
