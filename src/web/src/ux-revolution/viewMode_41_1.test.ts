/**
 * Sprint 41.1 — View Mode unit tests (UI only; auth untouched).
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  groupsForMode,
  isRouteAllowedForViewMode,
  useViewModeStore,
  VIEW_MODE_KEY,
  VIEW_MODE_OPTIONS,
} from "@/ux-revolution";
import { useAuthStore } from "@/auth/authStore";

describe("Sprint 41.1 View Mode", () => {
  beforeEach(() => {
    localStorage.removeItem(VIEW_MODE_KEY);
    useViewModeStore.setState({ viewMode: "platform_owner" });
  });

  it("exposes five view modes", () => {
    expect(VIEW_MODE_OPTIONS.map((o) => o.id)).toEqual([
      "client",
      "manager",
      "company_admin",
      "platform_owner",
      "developer",
    ]);
  });

  it("Client mode blocks builders and runtime", () => {
    expect(isRouteAllowedForViewMode("/crm", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/crm?view=leads", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/ai-agents", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/documents", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/platform-builder/builder-studio", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/command-runtime", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/ai-studio", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/kernel", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/owner", "client")).toBe(false);
  });

  it("Platform Owner and Developer allow everything", () => {
    expect(isRouteAllowedForViewMode("/platform-builder/runtime", "platform_owner")).toBe(true);
    expect(isRouteAllowedForViewMode("/command-runtime", "developer")).toBe(true);
  });

  it("Client nav groups exclude platform/builder routes", () => {
    const groups = groupsForMode("pro", { viewMode: "client" });
    const routes = groups.flatMap((g) => g.items.map((i) => i.route));
    expect(routes.some((r) => r.includes("platform-builder"))).toBe(false);
    expect(routes.some((r) => r.includes("command-runtime"))).toBe(false);
    expect(routes.some((r) => r.startsWith("/crm") || r === "/crm")).toBe(true);
    expect(groups.map((g) => g.id)).not.toContain("owner");
    expect(groups.map((g) => g.id)).not.toContain("city");
  });

  it("setViewMode does not clear auth session", () => {
    useAuthStore.setState({
      user: {
        id: "u1",
        email: "client@globefly.demo",
        name: "Client",
        tenantId: "globefly",
      },
      accessToken: "access_test",
      refreshToken: "refresh_test",
      authMode: "isam",
    });
    useViewModeStore.getState().setViewMode("client");
    expect(useViewModeStore.getState().viewMode).toBe("client");
    expect(useAuthStore.getState().user?.email).toBe("client@globefly.demo");
    expect(useAuthStore.getState().accessToken).toBe("access_test");
    useViewModeStore.getState().setViewMode("developer");
    expect(useAuthStore.getState().accessToken).toBe("access_test");
  });
});
