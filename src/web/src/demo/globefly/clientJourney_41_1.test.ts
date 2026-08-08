/**
 * Sprint 41.1 — Client journey route allowlist smoke.
 */

import { describe, expect, it } from "vitest";
import { isRouteAllowedForViewMode } from "@/ux-revolution";
import { MODULE_HELP_CATALOG } from "@/help/moduleHelpCatalog";
import { messages } from "@/i18n/messages";

const JOURNEY = [
  "/login",
  "/dashboard",
  "/crm",
  "/crm?view=leads",
  "/crm?view=clients",
  "/documents",
  "/ai-agents",
  "/analytics",
  "/settings",
  "/auth/logout",
];

describe("Sprint 41.1 Client journey smoke", () => {
  it("allows full GlobeFly Client journey routes", () => {
    for (const route of JOURNEY) {
      expect(isRouteAllowedForViewMode(route, "client"), route).toBe(true);
    }
  });

  it("blocks developer surfaces in Client mode", () => {
    for (const route of [
      "/platform-builder/builder-studio",
      "/command-runtime",
      "/ai-studio",
      "/kernel",
      "/owner",
    ]) {
      expect(isRouteAllowedForViewMode(route, "client"), route).toBe(false);
    }
  });

  it("has RU chrome keys for Client shell", () => {
    const keys = [
      "viewMode.label",
      "activity.title",
      "globefly.welcome",
      "nav.aiAssistant",
      "auth.login",
      "common.close",
    ];
    for (const k of keys) {
      expect(messages.ru[k], k).toBeTruthy();
      expect(messages.ru[k]).not.toMatch(/Coming soon|Hide platform|Activity Center/i);
    }
  });

  it("documents help for major Client modules", () => {
    const ids = MODULE_HELP_CATALOG.map((h) => h.moduleId);
    expect(ids).toEqual(
      expect.arrayContaining(["dashboard", "crm", "documents", "ai", "analytics", "tasks", "settings"]),
    );
  });
});
