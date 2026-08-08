/**
 * Sprint 42.3 — Client demo polish & UX review acceptance tests.
 */

import { describe, expect, it } from "vitest";
import { MODULE_LANDINGS, landingForPath } from "@/modules/moduleLandingCatalog";
import { isRouteAllowedForViewMode } from "@/ux-revolution";
import { DOCK_CATALOG } from "@/workspace-chrome/workspaceDockStore";
import { messages } from "@/i18n/messages";
import { ENTERPRISE_QUICK_ACTIONS } from "@/workspace-engine/QuickActionsPanel";

describe("Sprint 42.3 client demo polish", () => {
  it("landing titles are RU for client-facing hubs", () => {
    const expectRu: Record<string, string> = {
      analytics: "Аналитика",
      documents: "Документы",
      knowledge: "Знания",
      marketplace: "Маркетплейс",
      legal: "Юридический",
      drone: "БПЛА",
      auto: "Авто",
      agro: "Агро",
    };
    for (const [id, title] of Object.entries(expectRu)) {
      expect(MODULE_LANDINGS.find((m) => m.id === id)?.title).toBe(title);
    }
  });

  it("primary actions deep-link past landings (no self-loop)", () => {
    for (const land of MODULE_LANDINGS) {
      const base = land.primaryAction.route.split("?")[0] || "";
      if (base === land.route) {
        expect(land.primaryAction.route.includes("?"), `${land.id} primary must include view/action`).toBe(
          true,
        );
      }
    }
  });

  it("demo=1 and support routes are client-reachable", () => {
    expect(isRouteAllowedForViewMode("/crm?demo=1", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/support", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/marketplace", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/workspace/legal", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/workspace/crypto", "manager")).toBe(true);
    expect(isRouteAllowedForViewMode("/workspace/drone", "manager")).toBe(true);
  });

  it("client quick actions never include blocked routes when filtered", () => {
    const clientVisible = ENTERPRISE_QUICK_ACTIONS.filter((a) =>
      isRouteAllowedForViewMode(a.route, "client"),
    );
    expect(clientVisible.length).toBeGreaterThan(3);
    expect(clientVisible.every((a) => isRouteAllowedForViewMode(a.route, "client"))).toBe(true);
    expect(clientVisible.some((a) => a.route.includes("/projects"))).toBe(false);
    expect(clientVisible.some((a) => a.route.startsWith("/city"))).toBe(false);
  });

  it("dock catalog uses Russian labels", () => {
    expect(DOCK_CATALOG.find((d) => d.id === "analytics")?.label).toBe("Аналитика");
    expect(DOCK_CATALOG.find((d) => d.id === "documents")?.label).toBe("Документы");
    expect(DOCK_CATALOG.find((d) => d.id === "knowledge")?.label).toBe("Знания");
  });

  it("search workspace i18n keys exist in RU", () => {
    const ru = messages.ru;
    for (const k of [
      "search.workspaceTitle",
      "search.workspaceHint",
      "search.workspacePlaceholder",
      "search.openPalette",
      "search.modules",
      "search.grouped",
      "search.typedHint",
    ]) {
      expect(ru[k], k).toBeTruthy();
      expect(ru[k]).not.toMatch(/Search Workspace|Open Command/);
    }
  });

  it("resolves module landings for demo walkthrough paths", () => {
    for (const path of ["/crm", "/analytics", "/documents", "/knowledge", "/ai-agents"]) {
      expect(landingForPath(path), path).toBeTruthy();
    }
  });
});
