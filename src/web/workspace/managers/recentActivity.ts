import type { ActivityItem } from "../types";

const items: ActivityItem[] = [
  { id: "ra1", kind: "document", summary: "Opened Q3 board pack", at: new Date().toISOString() },
  { id: "ra2", kind: "task", summary: "Completed invoice approval", at: new Date(Date.now() - 3600000).toISOString() },
  { id: "ra3", kind: "workflow", summary: "Billing workflow executed", at: new Date(Date.now() - 7200000).toISOString() },
  { id: "ra4", kind: "ai", summary: "AI recommended capacity plan", at: new Date(Date.now() - 10800000).toISOString() },
  { id: "ra5", kind: "security", summary: "MFA challenge passed", at: new Date(Date.now() - 14400000).toISOString() },
  { id: "ra6", kind: "report", summary: "Generated finance summary", at: new Date(Date.now() - 86400000).toISOString() },
];

export const recentActivity = {
  list(): ActivityItem[] {
    return [...items];
  },
  byKind(kind: ActivityItem["kind"]) {
    return items.filter((i) => i.kind === kind);
  },
};
