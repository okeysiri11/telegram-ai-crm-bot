/**
 * Sprint 42.0 — Enterprise Workspace Revolution tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import { TOOLBAR_KEY, useToolbarStore } from "@/navigation/toolbarStore";
import {
  WORKSPACE_DOCK_KEY,
  useWorkspaceDockStore,
  DOCK_CATALOG,
} from "@/workspace-chrome/workspaceDockStore";
import { MODULE_LANDINGS, landingForPath } from "@/modules/moduleLandingCatalog";
import { messages } from "@/i18n/messages";
import { isRouteAllowedForViewMode } from "@/ux-revolution";

describe("Sprint 42.0 workspace revolution", () => {
  beforeEach(() => {
    localStorage.clear();
    useToolbarStore.setState({ collapsed: false });
    useWorkspaceDockStore.getState().reset();
  });

  it("persists toolbar collapse like a dock preference", () => {
    useToolbarStore.getState().setCollapsed(true);
    expect(localStorage.getItem(TOOLBAR_KEY)).toBe("1");
    expect(useToolbarStore.getState().collapsed).toBe(true);
  });

  it("workspace dock pin close reorder persist", () => {
    const store = useWorkspaceDockStore.getState();
    store.pin("crypto");
    expect(useWorkspaceDockStore.getState().favourites.find((f) => f.id === "crypto")?.pinned).toBe(true);
    store.close("analytics");
    expect(useWorkspaceDockStore.getState().favourites.some((f) => f.id === "analytics")).toBe(false);
    store.close("crypto"); // pinned — should stay
    expect(useWorkspaceDockStore.getState().favourites.some((f) => f.id === "crypto")).toBe(true);
    const idsBefore = useWorkspaceDockStore.getState().favourites.map((f) => f.id);
    if (idsBefore.length >= 2) {
      store.reorder(idsBefore[1]!, idsBefore[0]!);
    }
    const raw = localStorage.getItem(WORKSPACE_DOCK_KEY);
    expect(raw).toBeTruthy();
    expect(DOCK_CATALOG.length).toBeGreaterThanOrEqual(8);
  });

  it("module landings match sprint primary buttons and AI guide", () => {
    const expectPrimary: Record<string, string> = {
      crm: "Создать клиента",
      crypto: "Создать OTC-сделку",
      drone: "Создать дрон",
      auto: "Добавить автомобиль",
      agro: "Открыть ферму",
      marketplace: "Создать продукт",
      analytics: "Открыть дашборд",
      legal: "Создать договор",
      knowledge: "Открыть знания",
    };
    for (const [id, label] of Object.entries(expectPrimary)) {
      const land = MODULE_LANDINGS.find((m) => m.id === id);
      expect(land, id).toBeTruthy();
      expect(land!.primaryAction.label).toBe(label);
      expect(land!.aiGuide.bullets.length).toBeGreaterThanOrEqual(2);
      expect(land!.stats.length).toBeGreaterThan(0);
      expect(land!.actions.length).toBeGreaterThanOrEqual(3);
      expect(land!.helpRoute).toBeTruthy();
    }
  });

  it("landing never empty: demo and tutorial routes exist", () => {
    for (const land of MODULE_LANDINGS) {
      expect(land.emptyDemoRoute).toMatch(/^\//);
      expect(land.emptyTutorialRoute).toMatch(/^\//);
      expect(land.aiGuide.recommendedAction.route).toMatch(/^\//);
    }
  });

  it("resolves landings by path", () => {
    expect(landingForPath("/crm")?.id).toBe("crm");
    expect(landingForPath("/workspace/drone")?.id).toBe("drone");
    expect(landingForPath("/marketplace")?.id).toBe("marketplace");
  });

  it("client mode blocks platform and owner routes", () => {
    expect(isRouteAllowedForViewMode("/crm", "client")).toBe(true);
    expect(isRouteAllowedForViewMode("/platform-builder", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/owner", "client")).toBe(false);
    expect(isRouteAllowedForViewMode("/kernel", "client")).toBe(false);
  });

  it("RU localization for sprint 42 keys", () => {
    for (const k of [
      "toolbar.ai",
      "landing.aiGuide",
      "landing.aiToday",
      "landing.stats",
      "landing.recentObjects",
      "empty.title",
      "empty.demo",
      "dock.favourites",
      "dock.close",
      "iface.workspace.hint",
    ]) {
      expect(messages.ru[k], k).toBeTruthy();
    }
  });
});
