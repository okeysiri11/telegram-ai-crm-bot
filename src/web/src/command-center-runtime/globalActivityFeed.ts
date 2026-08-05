import { listActivity, type ActivityEntry, type ActivityKind } from "@/workspace-engine/activityJournal";
import { useNotificationStore, type AppNotification } from "@/notifications/notificationStore";

export type FeedKind =
  | "ai"
  | "system"
  | "crm"
  | "user"
  | "job"
  | "notification"
  | "workflow"
  | "error"
  | "warning";

export type GlobalFeedItem = {
  id: string;
  kind: FeedKind;
  title: string;
  detail: string;
  at: string;
  source: "journal" | "notification" | "synthetic";
};

function mapJournalKind(kind: ActivityKind): FeedKind {
  if (kind === "ai") return "ai";
  if (kind === "error") return "error";
  if (kind === "create" || kind === "navigate" || kind === "search" || kind === "login") return "user";
  if (kind === "notification") return "notification";
  return "system";
}

function mapNotification(n: AppNotification): FeedKind {
  if (n.kind === "ai") return "ai";
  if (n.kind === "error") return "error";
  if (n.kind === "warning" || n.kind === "alert") return "warning";
  if (n.kind === "job" || n.kind === "workflow" || n.kind === "task") return "job";
  if (n.kind === "mention") return "user";
  if (n.title.toLowerCase().includes("crm") || n.body.toLowerCase().includes("client")) return "crm";
  return "notification";
}

const SYNTHETIC: GlobalFeedItem[] = [
  {
    id: "syn_wf_1",
    kind: "workflow",
    title: "Workflow execution",
    detail: "Invoice Approval · step Review",
    at: new Date(Date.now() - 120_000).toISOString(),
    source: "synthetic",
  },
  {
    id: "syn_crm_1",
    kind: "crm",
    title: "CRM activity",
    detail: "Lead Demo Corp moved to Negotiation",
    at: new Date(Date.now() - 300_000).toISOString(),
    source: "synthetic",
  },
  {
    id: "syn_ai_1",
    kind: "ai",
    title: "AI event",
    detail: "Ops Copilot completed weekly summary",
    at: new Date(Date.now() - 480_000).toISOString(),
    source: "synthetic",
  },
];

/** Merge journal + notifications + light synthetic enterprise events into one timeline. */
export function buildGlobalActivityFeed(limit = 40): GlobalFeedItem[] {
  const journal: GlobalFeedItem[] = listActivity(30).map((e: ActivityEntry) => ({
    id: `j_${e.id}`,
    kind: mapJournalKind(e.kind),
    title: e.title,
    detail: e.detail,
    at: e.at,
    source: "journal" as const,
  }));

  const notifications: GlobalFeedItem[] = useNotificationStore.getState().items.slice(0, 20).map((n) => ({
    id: `n_${n.id}`,
    kind: mapNotification(n),
    title: n.title,
    detail: n.body,
    at: n.createdAt,
    source: "notification" as const,
  }));

  return [...journal, ...notifications, ...SYNTHETIC]
    .sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime())
    .slice(0, limit);
}

export const FEED_KIND_LABELS: Record<FeedKind, string> = {
  ai: "AI",
  system: "System",
  crm: "CRM",
  user: "User",
  job: "Jobs",
  notification: "Notifications",
  workflow: "Workflow",
  error: "Errors",
  warning: "Warnings",
};
