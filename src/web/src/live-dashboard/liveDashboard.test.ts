import { beforeEach, describe, expect, it } from "vitest";
import {
  DASHBOARD_PROFILES,
  LIVE_WIDGET_CATALOG,
  layoutForProfile,
  bootstrapLayouts,
} from "./liveDashboardCatalog";
import { useLiveDashboardStore } from "./liveDashboardStore";
import { LIVE_DASHBOARD_KEY } from "./types";
import { dashboardEventBus } from "./dashboardEventBus";

describe("Sprint 27.6 live dashboard", () => {
  beforeEach(() => {
    localStorage.removeItem(LIVE_DASHBOARD_KEY);
    useLiveDashboardStore.setState({
      hydrated: false,
      profileId: "ceo",
      activeLayoutId: "layout_ceo",
      layouts: bootstrapLayouts(),
      fullscreenId: null,
      activityFilter: "all",
      tick: 0,
    });
  });

  it("exposes runtime and enterprise widgets", () => {
    expect(LIVE_WIDGET_CATALOG.filter((w) => w.group === "runtime").length).toBe(10);
    expect(LIVE_WIDGET_CATALOG.filter((w) => w.group === "enterprise").length).toBe(10);
  });

  it("defines all dashboard profiles", () => {
    expect(Object.keys(DASHBOARD_PROFILES)).toEqual(
      expect.arrayContaining(["ceo", "manager", "sales", "developer", "finance", "administrator"]),
    );
    expect(layoutForProfile("developer").widgets.some((w) => w.id === "runtime_cpu")).toBe(true);
  });

  it("persists profile, layout, collapse, and pin", () => {
    const store = useLiveDashboardStore.getState();
    store.hydrate();
    store.setProfile("developer");
    const cpu = useLiveDashboardStore.getState().getActiveWidgets().find((w) => w.id === "runtime_cpu");
    expect(cpu).toBeTruthy();
    store.toggleCollapse("runtime_cpu");
    store.togglePin("runtime_cpu");
    store.resizeWidget("runtime_cpu", 2);
    const raw = localStorage.getItem(LIVE_DASHBOARD_KEY);
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw!);
    expect(parsed.profileId).toBe("developer");
    const widget = parsed.layouts
      .find((l: { id: string }) => l.id === parsed.activeLayoutId)
      .widgets.find((w: { id: string }) => w.id === "runtime_cpu");
    expect(widget.collapsed).toBe(true);
    expect(widget.pinned).toBe(true);
    expect(widget.colSpan).toBe(2);
  });

  it("reorders widgets and saves custom layout", () => {
    const store = useLiveDashboardStore.getState();
    store.hydrate();
    store.setProfile("ceo");
    const widgets = store.getActiveWidgets();
    const a = widgets[0]!.id;
    const b = widgets[1]!.id;
    store.moveWidget(b, a);
    const after = useLiveDashboardStore.getState().getActiveWidgets();
    expect(after[0]!.id).toBe(b);
    store.saveCurrentAs("My Ops Board");
    expect(useLiveDashboardStore.getState().layouts.some((l) => l.name === "My Ops Board")).toBe(true);
  });

  it("publishes dashboard event bus ticks", () => {
    let seen = 0;
    const unsub = dashboardEventBus.subscribe(() => {
      seen += 1;
    });
    const before = useLiveDashboardStore.getState().tick;
    dashboardEventBus.publish({ type: "notifications" });
    expect(seen).toBe(1);
    expect(useLiveDashboardStore.getState().tick).toBeGreaterThan(before);
    unsub();
  });
});
