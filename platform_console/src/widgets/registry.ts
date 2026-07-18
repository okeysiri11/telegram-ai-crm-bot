import type { WidgetDefinition, LayoutItem } from '../types/widgets';

export const WIDGET_REGISTRY: WidgetDefinition[] = [
  { id: 'platform_health', title: 'Platform Health', defaultW: 4, defaultH: 2, channels: ['system', 'health'] },
  { id: 'system_status', title: 'System Status', defaultW: 4, defaultH: 2, channels: ['system'] },
  { id: 'active_requests', title: 'Requests', defaultW: 4, defaultH: 2, channels: ['requests', 'dashboard'] },
  { id: 'manager_load', title: 'Managers', defaultW: 4, defaultH: 2, channels: ['managers'] },
  { id: 'workflow_status', title: 'Workflow Status', defaultW: 4, defaultH: 2, channels: ['workflows'] },
  { id: 'top_kpis', title: 'KPI', defaultW: 4, defaultH: 2, channels: ['dashboard'] },
  { id: 'recent_events', title: 'Realtime Events', defaultW: 6, defaultH: 3, channels: ['dashboard', 'audit'] },
  { id: 'job_queue_size', title: 'Queue Status', defaultW: 3, defaultH: 2, channels: ['dashboard'] },
  { id: 'running_jobs', title: 'Jobs', defaultW: 3, defaultH: 2, channels: ['dashboard'] },
  { id: 'notifications_queue', title: 'Notifications', defaultW: 4, defaultH: 2, channels: ['notifications'] },
  { id: 'observability_performance', title: 'Performance', defaultW: 4, defaultH: 2 },
  { id: 'sla_status', title: 'SLA Status', defaultW: 4, defaultH: 2, channels: ['requests'] },
];

export const DEFAULT_LAYOUT: LayoutItem[] = WIDGET_REGISTRY.map((w, i) => ({
  id: `layout-${w.id}`,
  widgetId: w.id,
  x: (i % 3) * 4,
  y: Math.floor(i / 3) * 2,
  w: w.defaultW,
  h: w.defaultH,
}));

export function getWidgetDef(id: string): WidgetDefinition | undefined {
  return WIDGET_REGISTRY.find((w) => w.id === id);
}

export function widgetsForRole(hasRole: (r: 'readonly' | 'administrator' | 'owner') => boolean): WidgetDefinition[] {
  return WIDGET_REGISTRY.filter((w) => {
    if (!w.minRole) return true;
    return hasRole(w.minRole);
  });
}

/** Map console widget ids to management API widget ids where they differ */
export const API_WIDGET_ID: Record<string, string> = {
  platform_health: 'platform_health',
};

export function apiWidgetId(consoleId: string): string {
  return API_WIDGET_ID[consoleId] || consoleId;
}
