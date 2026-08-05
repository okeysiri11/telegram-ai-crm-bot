import { create } from "zustand";

export type NotificationKind =
  | "in_app"
  | "toast"
  | "alert"
  | "task"
  | "ai"
  | "workflow"
  | "info"
  | "warning"
  | "success"
  | "error"
  | "system"
  | "runtime"
  | "mention"
  | "job";

export type NotificationLevel =
  | "info"
  | "warning"
  | "success"
  | "error"
  | "system"
  | "ai"
  | "runtime"
  | "mention"
  | "job";

/** Sprint 27.4 — notification center buckets. */
export type NotificationBucket =
  | "unread"
  | "mentions"
  | "warnings"
  | "errors"
  | "success"
  | "jobs"
  | "all";

export type AppNotification = {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string;
  createdAt: string;
  read: boolean;
  level?: NotificationLevel;
};

type NotifState = {
  items: AppNotification[];
  push: (n: Omit<AppNotification, "id" | "createdAt" | "read">) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clear: () => void;
};

export function notificationBucket(n: AppNotification): NotificationBucket[] {
  const buckets: NotificationBucket[] = ["all"];
  if (!n.read) buckets.push("unread");
  if (n.kind === "mention" || n.level === "mention") buckets.push("mentions");
  if (n.kind === "warning" || n.level === "warning" || n.kind === "alert") buckets.push("warnings");
  if (n.kind === "error" || n.level === "error") buckets.push("errors");
  if (n.kind === "success" || n.level === "success") buckets.push("success");
  if (n.kind === "job" || n.level === "job" || n.kind === "workflow" || n.kind === "task") buckets.push("jobs");
  return buckets;
}

export function filterByBucket(items: AppNotification[], bucket: NotificationBucket): AppNotification[] {
  if (bucket === "all") return items;
  return items.filter((n) => notificationBucket(n).includes(bucket));
}

export const useNotificationStore = create<NotifState>((set) => ({
  items: [
    {
      id: "n1",
      kind: "ai",
      level: "ai",
      title: "AI insight ready",
      body: "Weekly forecast available",
      createdAt: new Date().toISOString(),
      read: false,
    },
    {
      id: "n2",
      kind: "warning",
      level: "warning",
      title: "Approval pending",
      body: "Invoice workflow awaits owner",
      createdAt: new Date().toISOString(),
      read: false,
    },
    {
      id: "n3",
      kind: "runtime",
      level: "runtime",
      title: "Runtime heartbeat",
      body: "Local demo auth active · ISAM offline",
      createdAt: new Date().toISOString(),
      read: false,
    },
    {
      id: "n4",
      kind: "mention",
      level: "mention",
      title: "@you in Projects",
      body: "Ops Manager mentioned you on Migration review",
      createdAt: new Date().toISOString(),
      read: false,
    },
    {
      id: "n5",
      kind: "job",
      level: "job",
      title: "Background job finished",
      body: "Knowledge reindex completed",
      createdAt: new Date().toISOString(),
      read: true,
    },
    {
      id: "n6",
      kind: "success",
      level: "success",
      title: "Client created",
      body: "Demo Corp lead saved in CRM",
      createdAt: new Date().toISOString(),
      read: true,
    },
    {
      id: "n7",
      kind: "error",
      level: "error",
      title: "Provider timeout",
      body: "Voice provider probe timed out (local)",
      createdAt: new Date().toISOString(),
      read: false,
    },
  ],
  push: (n) =>
    set((s) => ({
      items: [
        {
          ...n,
          level: n.level || (n.kind as NotificationLevel),
          id: `n_${Math.random().toString(36).slice(2, 9)}`,
          createdAt: new Date().toISOString(),
          read: false,
        },
        ...s.items,
      ].slice(0, 100),
    })),
  markRead: (id) =>
    set((s) => ({
      items: s.items.map((i) => (i.id === id ? { ...i, read: true } : i)),
    })),
  markAllRead: () => set((s) => ({ items: s.items.map((i) => ({ ...i, read: true })) })),
  clear: () => set({ items: [] }),
}));
