/**
 * Sprint 30.7 — Workspace navigation, no dead links, command palette RU.
 */
import { describe, expect, it } from "vitest";
import {
  WORKSPACE_MODULE_ROUTES,
  assertNoDeadWorkspaceRoutes,
} from "./workspaceRoutes";
import { ENTERPRISE_RU_SIDEBAR, OWNER_RU_NAV, RU_QUICK_ACTIONS } from "@/navigation/enterpriseRuNav";
import { COMMAND_CATALOG } from "../../command-center/managers/quickActions";
import { commandPalette } from "../../navigation/managers/commandPalette";
import { CLIENT_DASHBOARD_SECTIONS, DEALER_DASHBOARD_SECTIONS } from "@/dashboard/betaHomeCatalog";

const REGISTERED_ROUTES = [
  "/crm",
  "/erp",
  "/knowledge",
  "/ai-agents",
  "/production-studio",
  "/marketplace",
  "/analytics",
  "/notifications",
  "/documents",
  "/calendar",
  "/workspace/finance",
  "/tasks",
  "/identity/users",
  "/settings",
  "/city",
  "/admin",
  "/owner",
  "/dashboard",
  "/desktop",
  "/health",
  "/search",
  "/projects",
];

describe("Sprint 30.7 Enterprise Workspace", () => {
  it("wires every workspace module route", () => {
    expect(WORKSPACE_MODULE_ROUTES.length).toBeGreaterThanOrEqual(15);
    const check = assertNoDeadWorkspaceRoutes(REGISTERED_ROUTES);
    expect(check.ok).toBe(true);
    expect(check.missing).toEqual([]);
  });

  it("sidebar items open real routes (no empty hashes)", () => {
    for (const item of ENTERPRISE_RU_SIDEBAR) {
      expect(item.route.startsWith("/")).toBe(true);
      expect(item.route.includes("#")).toBe(false);
      expect(item.label.length).toBeGreaterThan(0);
    }
    for (const item of OWNER_RU_NAV) {
      expect(item.route.startsWith("/")).toBe(true);
      expect(item.label.length).toBeGreaterThan(0);
    }
  });

  it("command palette exposes Russian open actions", () => {
    const labels = COMMAND_CATALOG.map((c) => c.label);
    expect(labels).toEqual(
      expect.arrayContaining([
        "Открыть модуль",
        "Открыть клиента",
        "Открыть проект",
        "Открыть AI-агента",
        "Открыть город",
        "Глобальный поиск",
      ]),
    );
    expect(commandPalette.hotkeys).toEqual(expect.arrayContaining(["Ctrl+K", "Meta+K"]));
    expect(commandPalette.search("клиент").length).toBeGreaterThan(0);
  });

  it("quick actions and role dashboards have live links", () => {
    for (const qa of RU_QUICK_ACTIONS) {
      expect(qa.route.startsWith("/")).toBe(true);
    }
    for (const s of CLIENT_DASHBOARD_SECTIONS) {
      expect(s.route.startsWith("/")).toBe(true);
    }
    for (const s of DEALER_DASHBOARD_SECTIONS) {
      expect(s.route.startsWith("/")).toBe(true);
    }
  });

  it("exports ops pages", async () => {
    const mod = await import("./WorkspaceOpsPages");
    expect(typeof mod.CalendarPage).toBe("function");
    expect(typeof mod.TasksPage).toBe("function");
    expect(typeof mod.NotificationsPage).toBe("function");
    expect(typeof (await import("@/dashboard/AdminDashboardPage")).AdminDashboardPage).toBe("function");
  }, 15000);
});
