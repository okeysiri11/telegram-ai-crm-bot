/**
 * Sprint 42.1 — multi-role parallel workspaces tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  MULTI_ROLE_DEMO_USERS,
  demoUserByEmail,
  getWorkspaceSlot,
  wsKey,
  WORKSPACE_PORT_SLOTS,
  snapshotRoleSession,
  restoreRoleSession,
  switchRoleSession,
  markClientOnboardingComplete,
  resetClientOnboarding,
  isClientOnboardingComplete,
  CLIENT_ONBOARDING_STEPS,
  seedClientDemoData,
  readClientDemoSeed,
} from "@/multi-role";
import { homeRouteForRole, mapToRoleHomeId, postAuthDestination } from "@/navigation/roleHome";
import { isRouteAllowedForViewMode } from "@/ux-revolution";
import { messages } from "@/i18n/messages";

describe("Sprint 42.1 multi-role workspaces", () => {
  beforeEach(() => {
    localStorage.clear();
    resetClientOnboarding();
  });

  it("seeds required demo users", () => {
    const emails = [
      "owner@ados.demo",
      "admin@ados.demo",
      "travel@globefly.demo",
      "crypto@ados.demo",
      "build@ados.demo",
      "drone@ados.demo",
      "auto@ados.demo",
      "legal@ados.demo",
      "agro@ados.demo",
      "seller@ados.demo",
    ];
    expect(MULTI_ROLE_DEMO_USERS.length).toBeGreaterThanOrEqual(10);
    for (const e of emails) {
      expect(demoUserByEmail(e), e).toBeTruthy();
      expect(demoUserByEmail(e)!.password).toBe("demo");
    }
  });

  it("maps parallel ports to workspace slots", () => {
    expect(WORKSPACE_PORT_SLOTS["3000"]).toBe("owner");
    expect(WORKSPACE_PORT_SLOTS["3001"]).toBe("travel");
    expect(WORKSPACE_PORT_SLOTS["3002"]).toBe("crypto");
    expect(WORKSPACE_PORT_SLOTS["3003"]).toBe("build");
    expect(wsKey("ewp_session_v1")).toContain("ewp_session_v1");
    expect(getWorkspaceSlot()).toBeTruthy();
  });

  it("role-based homes", () => {
    expect(homeRouteForRole("owner")).toBe("/owner");
    expect(homeRouteForRole("administrator")).toBe("/admin");
    expect(homeRouteForRole("manager")).toBe("/dashboards/manager");
    expect(homeRouteForRole("sales")).toBe("/crm?view=pipeline");
    expect(homeRouteForRole("client")).toBe("/dashboard");
    expect(mapToRoleHomeId("sales")).toBe("sales");
  });

  it("client onboarding has 6 steps", () => {
    expect(CLIENT_ONBOARDING_STEPS).toEqual([
      "welcome",
      "company",
      "business",
      "modules",
      "import",
      "finish",
    ]);
    expect(isClientOnboardingComplete()).toBe(false);
    markClientOnboardingComplete({ companyName: "Test Co" });
    expect(isClientOnboardingComplete()).toBe(true);
    expect(postAuthDestination("client", "travel@globefly.demo")).toBe("/dashboard");
  });

  it("client workspace hides platform/owner/diagnostics", () => {
    expect(isRouteAllowedForViewMode("/crm", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/documents", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/analytics", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/tasks", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/knowledge", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/support", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/settings", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/platform-builder", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/owner", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/kernel", "client")).toBe(false);
  });

  it("role session vault isolates snapshots", () => {
    localStorage.setItem(wsKey("ewp_toolbar_collapsed_v1"), "1");
    snapshotRoleSession("owner");
    localStorage.setItem(wsKey("ewp_toolbar_collapsed_v1"), "0");
    snapshotRoleSession("client");
    switchRoleSession("client", "owner");
    expect(localStorage.getItem(wsKey("ewp_toolbar_collapsed_v1"))).toBe("1");
    restoreRoleSession("client");
    expect(localStorage.getItem(wsKey("ewp_toolbar_collapsed_v1"))).toBe("0");
  });

  it("client demo seed loads data", () => {
    const user = demoUserByEmail("travel@globefly.demo")!;
    seedClientDemoData(user);
    const seed = readClientDemoSeed();
    expect(seed?.clients.length).toBeGreaterThan(0);
    expect(seed?.documents.length).toBeGreaterThan(0);
    expect(seed?.aiMessages.length).toBeGreaterThan(0);
  });

  it("RU keys for multi-role UX", () => {
    for (const k of ["workspace.openDemo", "onboard.clientTitle", "devRole.label", "workspace.slot"]) {
      expect(messages.ru[k], k).toBeTruthy();
    }
  });
});
