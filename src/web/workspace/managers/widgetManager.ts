import type { WidgetInstance, WidgetKind } from "../types";

const catalog: { kind: WidgetKind; title: string }[] = [
  { kind: "kpi_cards", title: "KPI Cards" },
  { kind: "charts", title: "Charts" },
  { kind: "ai_assistant", title: "AI Assistant" },
  { kind: "tasks", title: "Tasks" },
  { kind: "calendar", title: "Calendar" },
  { kind: "notifications", title: "Notifications" },
  { kind: "workflow_queue", title: "Workflow Queue" },
  { kind: "crm_summary", title: "CRM Summary" },
  { kind: "erp_summary", title: "ERP Summary" },
  { kind: "finance_summary", title: "Finance Summary" },
  { kind: "hr_summary", title: "HR Summary" },
  { kind: "analytics", title: "Analytics" },
  { kind: "marketplace", title: "Marketplace" },
  { kind: "system_health", title: "System Health" },
];

let widgets: WidgetInstance[] = [
  { widgetId: "w_kpi", kind: "kpi_cards", title: "KPI Cards", x: 0, y: 0, w: 4, h: 2, config: { refreshSec: 30 }, realtime: true },
  { widgetId: "w_ai", kind: "ai_assistant", title: "AI Assistant", x: 4, y: 0, w: 4, h: 2, config: {}, realtime: true },
  { widgetId: "w_tasks", kind: "tasks", title: "Today's Tasks", x: 8, y: 0, w: 4, h: 2, config: {}, realtime: true },
  { widgetId: "w_calendar", kind: "calendar", title: "Calendar", x: 0, y: 2, w: 4, h: 2, config: {}, realtime: false },
  { widgetId: "w_notif", kind: "notifications", title: "Notifications", x: 4, y: 2, w: 4, h: 2, config: {}, realtime: true },
  { widgetId: "w_workflow", kind: "workflow_queue", title: "Active Workflows", x: 8, y: 2, w: 4, h: 2, config: {}, realtime: true },
  { widgetId: "w_charts", kind: "charts", title: "Charts", x: 0, y: 4, w: 6, h: 3, config: {}, realtime: true },
  { widgetId: "w_crm", kind: "crm_summary", title: "CRM Summary", x: 6, y: 4, w: 3, h: 2, config: {}, realtime: false },
  { widgetId: "w_erp", kind: "erp_summary", title: "ERP Summary", x: 9, y: 4, w: 3, h: 2, config: {}, realtime: false },
  { widgetId: "w_finance", kind: "finance_summary", title: "Finance Summary", x: 0, y: 7, w: 4, h: 2, config: {}, realtime: true },
  { widgetId: "w_hr", kind: "hr_summary", title: "HR Summary", x: 4, y: 7, w: 4, h: 2, config: {}, realtime: false },
  { widgetId: "w_analytics", kind: "analytics", title: "Analytics", x: 8, y: 7, w: 4, h: 2, config: {}, realtime: true },
  { widgetId: "w_market", kind: "marketplace", title: "Marketplace", x: 0, y: 9, w: 6, h: 2, config: {}, realtime: false },
  { widgetId: "w_health", kind: "system_health", title: "System Health", x: 6, y: 9, w: 6, h: 2, config: {}, realtime: true },
];

export const widgetManager = {
  catalog() {
    return [...catalog];
  },
  list(): WidgetInstance[] {
    return [...widgets];
  },
  get(id: string) {
    return widgets.find((w) => w.widgetId === id);
  },
  configure(widgetId: string, config: WidgetInstance["config"]) {
    widgets = widgets.map((w) => (w.widgetId === widgetId ? { ...w, config: { ...w.config, ...config } } : w));
    return this.get(widgetId);
  },
  resize(widgetId: string, w: number, h: number) {
    widgets = widgets.map((x) => (x.widgetId === widgetId ? { ...x, w, h } : x));
    return this.get(widgetId);
  },
  move(widgetId: string, x: number, y: number) {
    widgets = widgets.map((item) => (item.widgetId === widgetId ? { ...item, x, y } : item));
    return this.get(widgetId);
  },
  refreshRealtime() {
    return widgets.filter((w) => w.realtime).map((w) => w.widgetId);
  },
};
