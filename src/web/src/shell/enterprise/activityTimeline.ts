/**
 * Unified activity timeline — Sprint 28.5.
 * Normalizes journal · notifications · desktop closed stack hints.
 */

import { listActivity, type ActivityEntry } from "@/workspace-engine/activityJournal";
import { useNotificationStore } from "@/notifications/notificationStore";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";

export type TimelineKind =
  | "module"
  | "window"
  | "ai"
  | "production"
  | "notification"
  | "error"
  | "approval"
  | "system";

export type TimelineItem = {
  id: string;
  kind: TimelineKind;
  title: string;
  detail: string;
  at: string;
  path?: string;
};

function mapJournal(a: ActivityEntry): TimelineItem {
  const kind: TimelineKind =
    a.kind === "ai"
      ? "ai"
      : a.kind === "error"
        ? "error"
        : a.kind === "navigate"
          ? "module"
          : a.kind === "notification"
            ? "notification"
            : "system";
  return { id: a.id, kind, title: a.title, detail: a.detail, at: a.at };
}

export function buildActivityTimeline(limit = 40): TimelineItem[] {
  const items: TimelineItem[] = [];

  for (const a of listActivity(limit)) {
    items.push(mapJournal(a));
  }

  try {
    const notes = useNotificationStore.getState().items.slice(0, 12);
    for (const n of notes) {
      items.push({
        id: `n_${n.id}`,
        kind: n.kind === "error" ? "error" : n.kind === "warning" ? "approval" : "notification",
        title: n.title,
        detail: n.body,
        at: n.createdAt,
      });
    }
  } catch {
    /* store optional in tests */
  }

  try {
    for (const e of enterpriseEventBus.recent(10)) {
      if (e.type === "job_update") {
        items.push({
          id: `ev_${e.at}_${e.type}`,
          kind: "production",
          title: "Production / job update",
          detail: JSON.stringify(e.payload || {}).slice(0, 120),
          at: e.at,
        });
      } else if (e.type === "ai_request") {
        items.push({
          id: `ev_${e.at}_ai`,
          kind: "ai",
          title: "AI action",
          detail: String(e.payload?.stream || "ai"),
          at: e.at,
        });
      } else if (e.type === "open_module" || e.type === "navigate") {
        items.push({
          id: `ev_${e.at}_nav`,
          kind: "module",
          title: "Module opened",
          detail: e.path || "",
          at: e.at,
          path: e.path,
        });
      }
    }
  } catch {
    /* ignore */
  }

  return items
    .sort((a, b) => b.at.localeCompare(a.at))
    .slice(0, limit);
}
