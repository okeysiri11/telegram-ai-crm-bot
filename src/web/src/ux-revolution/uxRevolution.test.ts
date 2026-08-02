/**
 * Sprint 33.1 — Enterprise UX Revolution foundation tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  SIMPLE_MODE_NAV,
  filterNavForMode,
  matchAiNavigationIntent,
  resolveModuleContext,
  ENTERPRISE_UX_ROLES,
  buildUxPaletteCommands,
  EXPERIENCE_MODE_KEY,
  UX_REVOLUTION_SPRINT,
} from "@/ux-revolution";
import { webConfig } from "@/config/webConfig";
import { homeRouteForRole } from "@/navigation/roleHome";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";

describe("Sprint 33.1 UX Revolution", () => {
  beforeEach(() => {
    localStorage.removeItem(EXPERIENCE_MODE_KEY);
  });

  it("bumps webConfig sprint to 33.1", () => {
    expect(webConfig.sprint).toBe("33.1");
    expect(UX_REVOLUTION_SPRINT).toBe("33.1");
  });

  it("Simple Mode allowlist has required modules", () => {
    const ids = SIMPLE_MODE_NAV.map((i) => i.id);
    expect(ids).toEqual(
      expect.arrayContaining([
        "dashboard",
        "ai_assistant",
        "crm",
        "projects",
        "documents",
        "calendar",
        "finance",
        "settings",
        "notifications",
        "search",
      ]),
    );
  });

  it("filters Pro items out in Simple mode", () => {
    const items = [
      { id: "crm", route: "/crm" },
      { id: "erp", route: "/erp" },
      { id: "marketplace", route: "/marketplace" },
    ];
    const simple = filterNavForMode(items, "simple");
    expect(simple.map((i) => i.id)).toEqual(["crm"]);
    expect(filterNavForMode(items, "pro")).toHaveLength(3);
  });

  it("resolves CRM context navigation", () => {
    const ctx = resolveModuleContext("/crm?view=deals", { pro: false });
    expect(ctx?.moduleId).toBe("crm");
    expect(ctx?.items.some((i) => i.id === "crm_deals")).toBe(true);
    expect(ctx?.items.some((i) => i.label === "Клиенты")).toBe(true);
  });

  it("hides Pro-only context in Simple mode", () => {
    expect(resolveModuleContext("/erp", { pro: false })).toBeNull();
    expect(resolveModuleContext("/erp", { pro: true })?.moduleId).toBe("erp");
  });

  it("matches AI navigation intents (EN + RU)", () => {
    expect(matchAiNavigationIntent("Create client")?.id).toBe("create_client");
    expect(matchAiNavigationIntent("открой финансы")?.route).toBe("/analytics");
    expect(matchAiNavigationIntent("Open Knowledge Graph")?.requiresPro).toBe(true);
    expect(matchAiNavigationIntent("Show overdue projects")?.route).toContain("overdue");
  });

  it("exposes eight enterprise role workspaces", () => {
    expect(ENTERPRISE_UX_ROLES).toHaveLength(8);
    expect(firstEntryRoleCatalog.enterpriseList()).toHaveLength(8);
    expect(homeRouteForRole("ceo")).toContain("/dashboard");
    expect(homeRouteForRole("sales")).toBe("/crm");
    expect(homeRouteForRole("owner")).toBe("/owner");
  });

  it("builds palette quick actions filtered by mode", () => {
    const simple = buildUxPaletteCommands("simple");
    expect(simple.every((c) => !c.requiresPro)).toBe(true);
    const pro = buildUxPaletteCommands("pro");
    expect(pro.some((c) => c.requiresPro)).toBe(true);
    expect(pro.some((c) => c.section === "open_module")).toBe(true);
  });
});
