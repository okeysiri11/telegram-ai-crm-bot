import type { LayoutSnapshot, WidgetInstance } from "../types";
import { widgetManager } from "./widgetManager";

const layouts = new Map<string, LayoutSnapshot>();

function snapshot(workspaceId: string): LayoutSnapshot {
  const existing = layouts.get(workspaceId);
  if (existing) return existing;
  const layout: LayoutSnapshot = {
    layoutId: `layout_${workspaceId}`,
    workspaceId,
    widgets: widgetManager.list(),
    multiMonitorReady: true,
  };
  layouts.set(workspaceId, layout);
  return layout;
}

export const layoutManager = {
  get(workspaceId: string) {
    return snapshot(workspaceId);
  },
  save(workspaceId: string, widgets: WidgetInstance[]) {
    const layout: LayoutSnapshot = {
      layoutId: `layout_${workspaceId}`,
      workspaceId,
      widgets,
      multiMonitorReady: true,
    };
    layouts.set(workspaceId, layout);
    return layout;
  },
  features() {
    return ["drag_drop", "resize", "docking", "responsive_grid", "multi_monitor_ready"] as const;
  },
};
