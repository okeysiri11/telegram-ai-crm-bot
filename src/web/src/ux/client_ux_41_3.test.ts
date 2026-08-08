/**
 * Sprint 41.3 — client UX refinement tests
 * (toolbar persist, dock non-resize default, landings, RU localization).
 */

import { beforeEach, describe, expect, it } from "vitest";
import { TOOLBAR_KEY, useToolbarStore } from "@/navigation/toolbarStore";
import { DOCK_LAYOUT_KEY, useShellLayoutStore } from "@/shell/enterprise/shellLayoutStore";
import { MODULE_LANDINGS, landingForPath } from "@/modules/moduleLandingCatalog";
import { messages } from "@/i18n/messages";
import { ACTIVITY_TABS, SHELL_ACTIVITY_SEED } from "@/shell/enterprise/activityCatalog";

describe("Sprint 41.3 client UX refinement", () => {
  beforeEach(() => {
    localStorage.clear();
    useToolbarStore.setState({ collapsed: false });
    useShellLayoutStore.setState({
      docks: {
        left: { open: false, collapsed: true, pinned: false, autoHide: true, size: 220 },
        right: { open: false, collapsed: true, pinned: false, autoHide: true, size: 300 },
        bottom: { open: false, collapsed: false, pinned: false, autoHide: true, size: 180 },
      },
      activityOpen: false,
    });
  });

  it("persists toolbar collapsed preference", () => {
    useToolbarStore.getState().setCollapsed(true);
    expect(localStorage.getItem(TOOLBAR_KEY)).toBe("1");
    useToolbarStore.getState().toggle();
    expect(localStorage.getItem(TOOLBAR_KEY)).toBe("0");
    expect(useToolbarStore.getState().collapsed).toBe(false);
  });

  it("persists activity dock open/closed and width", () => {
    useShellLayoutStore.getState().setDock("right", { open: true, collapsed: false, size: 320 });
    const raw = localStorage.getItem(DOCK_LAYOUT_KEY);
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw!);
    expect(parsed.right.open).toBe(true);
    expect(parsed.right.collapsed).toBe(false);
    expect(parsed.right.size).toBe(320);
    useShellLayoutStore.getState().toggleDockCollapse("right");
    const again = JSON.parse(localStorage.getItem(DOCK_LAYOUT_KEY)!);
    expect(again.right.collapsed).toBe(true);
  });

  it("covers required module landings with primary CTA", () => {
    const required = [
      "drone",
      "auto",
      "crypto",
      "agro",
      "marketplace",
      "legal",
      "cafe",
      "ai",
      "platform",
      "owner",
      "analytics",
      "crm",
      "knowledge",
      "documents",
    ];
    for (const id of required) {
      const land = MODULE_LANDINGS.find((m) => m.id === id);
      expect(land, id).toBeTruthy();
      expect(land!.primaryAction.label.length).toBeGreaterThan(2);
      expect(land!.primaryAction.route).toMatch(/^\//);
      expect(land!.purpose.length).toBeGreaterThan(5);
      expect(land!.nextStep.length).toBeGreaterThan(5);
      expect(land!.aiRecommendation.length).toBeGreaterThan(5);
      expect(land!.aiGuide.bullets.length).toBeGreaterThan(0);
    }
  });

  it("resolves landings by path", () => {
    expect(landingForPath("/workspace/drone")?.id).toBe("drone");
    expect(landingForPath("/crm")?.id).toBe("crm");
    expect(landingForPath("/analytics")?.id).toBe("analytics");
  });

  it("has Russian strings for activity and chrome keys", () => {
    const keys = [
      "activity.title",
      "activity.tab.notifications",
      "activity.tab.recent",
      "activity.tab.tasks",
      "activity.tab.ai",
      "activity.tab.system",
      "dock.expand",
      "dock.collapse",
      "dock.workspace",
      "toolbar.collapse",
      "toolbar.expand",
      "landing.primaryActions",
      "landing.recent",
      "landing.next",
      "landing.ai",
      "welcome.title",
      "welcome.dismiss",
      "page.where",
      "page.time",
      "page.help",
      "runtime.health",
      "runtime.jobs",
      "runtime.providers",
      "runtime.heartbeat",
      "status.ready",
      "uws.concierge",
      "iface.panel.unpin",
    ];
    for (const k of keys) {
      expect(messages.ru[k], k).toBeTruthy();
      expect(messages.ru[k]).not.toMatch(/Activity Center|Runtime Health|Approval Pending/);
    }
  });

  it("activity seed titles are Russian", () => {
    for (const e of SHELL_ACTIVITY_SEED) {
      expect(e.title).toMatch(/[А-Яа-яЁё]/);
    }
    expect(ACTIVITY_TABS.every((t) => t.labelKey.startsWith("activity.tab."))).toBe(true);
  });

  it("answers UX journey questions for every landing", () => {
    for (const land of MODULE_LANDINGS) {
      // 1 where — title+route
      expect(land.title && land.route).toBeTruthy();
      // 2 why — purpose
      expect(land.purpose).toBeTruthy();
      // 3 what can I do — actions + primary
      expect(land.actions.length + 1).toBeGreaterThan(1);
      // 4 next
      expect(land.nextStep || land.aiRecommendation).toBeTruthy();
    }
  });
});
