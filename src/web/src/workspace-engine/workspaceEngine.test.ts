import { beforeEach, describe, expect, it } from "vitest";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { WORKSPACE_SESSION_KEY } from "@/workspace-engine/types";
import { clearActivity, listActivity, logActivity } from "@/workspace-engine/activityJournal";
import { ENTERPRISE_QUICK_ACTIONS } from "@/workspace-engine/QuickActionsPanel";
import { ENTERPRISE_QUICK_CREATE } from "@/workspace-engine/quickCreateCatalog";
import { quickActionsEngine } from "../../command-center/managers/quickActions";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { filterByBucket, useNotificationStore } from "@/notifications/notificationStore";
import { useShellLayoutStore, DOCK_LAYOUT_KEY } from "@/shell/enterprise/shellLayoutStore";

describe("Sprint 27.4 workspace runtime", () => {
  beforeEach(() => {
    localStorage.removeItem(WORKSPACE_SESSION_KEY);
    localStorage.removeItem(DOCK_LAYOUT_KEY);
    clearActivity();
    useWorkspaceManager.setState({
      activeWorkspaceId: "ws_default",
      tabs: [],
      activeTabId: null,
      closedTabs: [],
      hydrated: false,
    });
  });

  it("hydrates, opens, pins, and closes tabs with persistence", () => {
    const store = useWorkspaceManager.getState();
    store.hydrate();
    expect(useWorkspaceManager.getState().tabs.length).toBeGreaterThan(0);
    store.openTab("/crm", { activate: true });
    expect(useWorkspaceManager.getState().tabs.some((t) => t.path.startsWith("/crm"))).toBe(true);
    const crm = useWorkspaceManager.getState().tabs.find((t) => t.path.startsWith("/crm"))!;
    store.togglePin(crm.id);
    expect(useWorkspaceManager.getState().tabs.find((t) => t.id === crm.id)?.pinned).toBe(true);
    const raw = localStorage.getItem(WORKSPACE_SESSION_KEY);
    expect(raw).toBeTruthy();
    expect(JSON.parse(raw!).tabs.length).toBeGreaterThan(0);
  });

  it("reorders, duplicates, and reopens closed tabs", () => {
    const store = useWorkspaceManager.getState();
    store.hydrate();
    store.openTab("/crm", { activate: true });
    store.openTab("/erp", { activate: true });
    const tabs = useWorkspaceManager.getState().tabs;
    const crm = tabs.find((t) => t.path.startsWith("/crm"))!;
    const erp = tabs.find((t) => t.path.startsWith("/erp"))!;
    store.reorderTabs(erp.id, crm.id);
    const order = useWorkspaceManager.getState().tabs.map((t) => t.path.split("?")[0]);
    expect(order.indexOf("/erp")).toBeLessThan(order.indexOf("/crm"));
    const dup = store.duplicateTab(crm.id);
    expect(dup?.title).toContain("copy");
    store.togglePin(crm.id); // unpin if pinned
    const unpinned = useWorkspaceManager.getState().tabs.find((t) => t.id === crm.id);
    if (unpinned?.pinned) store.togglePin(crm.id);
    store.closeTab(crm.id);
    expect(useWorkspaceManager.getState().closedTabs.some((t) => t.path.startsWith("/crm"))).toBe(true);
    const reopened = store.reopenClosedTab();
    expect(reopened?.path.startsWith("/crm")).toBe(true);
  });

  it("persists dock layout sizes and pins", () => {
    useShellLayoutStore.getState().resizeDock("right", 340);
    useShellLayoutStore.getState().toggleDockPin("right");
    const raw = localStorage.getItem(DOCK_LAYOUT_KEY);
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw!);
    expect(parsed.right.size).toBe(340);
    expect(parsed.right.pinned).toBe(true);
  });

  it("groups global search results by category", () => {
    const groups = searchProvider.searchGrouped("create", 4);
    expect(groups.length).toBeGreaterThan(0);
    expect(groups.some((g) => g.category === "commands")).toBe(true);
    const crm = searchProvider.searchGrouped("crm", 4);
    expect(crm.some((g) => g.label === "CRM" || g.category === "crm")).toBe(true);
  });

  it("exposes quick create entities and command palette opens", () => {
    expect(ENTERPRISE_QUICK_CREATE.map((a) => a.label)).toEqual(
      expect.arrayContaining(["Client", "Project", "Task", "Document", "AI Agent", "Workflow", "Knowledge Page", "Company"]),
    );
    expect(ENTERPRISE_QUICK_ACTIONS.length).toBeGreaterThanOrEqual(8);
    expect(quickActionsEngine.byAction("create_company")?.route).toContain("create_company");
    expect(quickActionsEngine.byAction("open_crm")?.route).toBe("/crm");
  });

  it("filters notification center buckets", () => {
    const items = useNotificationStore.getState().items;
    expect(filterByBucket(items, "mentions").length).toBeGreaterThan(0);
    expect(filterByBucket(items, "jobs").length).toBeGreaterThan(0);
    expect(filterByBucket(items, "errors").length).toBeGreaterThan(0);
    expect(filterByBucket(items, "unread").every((n) => !n.read)).toBe(true);
  });

  it("records activity journal entries", () => {
    logActivity({ kind: "search", title: "Search CRM", detail: "crm" });
    expect(listActivity()[0]?.title).toBe("Search CRM");
  });
});
