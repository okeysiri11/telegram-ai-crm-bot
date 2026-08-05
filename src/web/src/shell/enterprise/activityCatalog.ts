/**
 * Sprint 27.1 — Activity Center seed data (right panel).
 * Complements live-ops SEED_ACTIVITY without duplicating engines.
 */

export type ActivityTabId = "recent" | "notifications" | "tasks" | "ai" | "system";

export type ActivityEntry = {
  id: string;
  tab: ActivityTabId;
  title: string;
  detail: string;
  at: string;
  tone?: "ok" | "warn" | "info";
};

export const ACTIVITY_TABS: { id: ActivityTabId; label: string }[] = [
  { id: "recent", label: "Recent Activity" },
  { id: "notifications", label: "Notifications" },
  { id: "tasks", label: "Running Tasks" },
  { id: "ai", label: "AI Messages" },
  { id: "system", label: "System Events" },
];

const ago = (m: number) => new Date(Date.now() - m * 60_000).toISOString();

export const SHELL_ACTIVITY_SEED: ActivityEntry[] = [
  {
    id: "r1",
    tab: "recent",
    title: "Dashboard opened",
    detail: "Command Center session",
    at: ago(1),
    tone: "info",
  },
  {
    id: "r2",
    tab: "recent",
    title: "CRM pipeline sync",
    detail: "186 active deals",
    at: ago(8),
    tone: "ok",
  },
  {
    id: "n1",
    tab: "notifications",
    title: "Escalation waiting",
    detail: "Control Tower · 2 items",
    at: ago(12),
    tone: "warn",
  },
  {
    id: "n2",
    tab: "notifications",
    title: "Invite accepted",
    detail: "Pilot workspace",
    at: ago(40),
    tone: "ok",
  },
  {
    id: "t1",
    tab: "tasks",
    title: "Sales Specialist",
    detail: "Running · brief generation",
    at: ago(3),
    tone: "info",
  },
  {
    id: "t2",
    tab: "tasks",
    title: "Risk Monitor",
    detail: "Running · health probes",
    at: ago(5),
    tone: "ok",
  },
  {
    id: "a1",
    tab: "ai",
    title: "Advisor",
    detail: "Morning priorities ready",
    at: ago(6),
    tone: "info",
  },
  {
    id: "a2",
    tab: "ai",
    title: "Concierge",
    detail: "Suggested CRM → Analytics route",
    at: ago(15),
    tone: "ok",
  },
  {
    id: "s1",
    tab: "system",
    title: "Providers",
    detail: "Gateway heartbeat OK",
    at: ago(2),
    tone: "ok",
  },
  {
    id: "s2",
    tab: "system",
    title: "Build",
    detail: "enterprise-web-platform ready",
    at: ago(20),
    tone: "info",
  },
];
