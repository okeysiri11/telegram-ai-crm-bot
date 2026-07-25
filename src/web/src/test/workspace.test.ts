import { describe, expect, it } from "vitest";
import {
  WORKSPACE_VERSION,
  buildWorkspaceDashboard,
  dashboardEngine,
  layoutManager,
  liveUpdates,
  quickActions,
  searchCenter,
  widgetManager,
  workspaceManager,
} from "../../workspace";

describe("Enterprise Workspace Framework", () => {
  it("exposes version and workspace kinds", () => {
    expect(WORKSPACE_VERSION).toBe("9.0.5");
    expect(workspaceManager.kinds()).toContain("personal");
    expect(workspaceManager.list().length).toBeGreaterThanOrEqual(5);
  });

  it("covers dashboards, widgets, layout, search, actions", () => {
    expect(dashboardEngine.kinds()).toContain("executive");
    expect(widgetManager.catalog().length).toBeGreaterThanOrEqual(14);
    expect(layoutManager.features()).toContain("drag_drop");
    expect(searchCenter.search("crm").length).toBeGreaterThan(0);
    expect(quickActions.byShortcut("a")?.id).toBe("open_ai_assistant");
    expect(liveUpdates.sources).toContain("websocket");
  });

  it("builds workspace dashboard", () => {
    const dash = buildWorkspaceDashboard();
    expect(dash.workspace.workspaceId).toBeTruthy();
    expect(dash.sections.kpiOverview?.kind).toBe("kpi_cards");
  });
});
