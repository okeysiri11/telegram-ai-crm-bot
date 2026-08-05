import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useNotificationStore } from "@/notifications/notificationStore";
import { Badge } from "@/ui";
import { DockPanel } from "./DockPanel";
import { useShellLayoutStore } from "./shellLayoutStore";
import {
  ACTIVITY_TABS,
  SHELL_ACTIVITY_SEED,
  type ActivityTabId,
} from "./activityCatalog";
import { buildActivityTimeline } from "./activityTimeline";

function relTime(iso: string) {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60_000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  const h = Math.round(mins / 60);
  return `${h}h`;
}

/** Right dock — Activity / Notifications (resize · pin · auto-hide via DockPanel). */
export function ActivityPanel() {
  const rightOpen = useShellLayoutStore((s) => s.docks.right.open);
  const notifications = useNotificationStore((s) => s.items);
  const [tab, setTab] = useState<ActivityTabId>("recent");

  const entries = useMemo(() => {
    if (tab === "notifications") {
      const fromStore = notifications.slice(0, 12).map((n) => ({
        id: n.id,
        title: n.title || "Notification",
        detail: n.body || "",
        at: n.createdAt || new Date().toISOString(),
        tone: (n.read ? "info" : "warn") as "info" | "warn" | "ok",
      }));
      if (fromStore.length) return fromStore;
    }
    if (tab === "recent") {
      const timeline = buildActivityTimeline(16).map((e) => ({
        id: e.id,
        title: e.title,
        detail: e.detail,
        at: e.at,
        tone: (e.kind === "error" ? "warn" : e.kind === "ai" ? "ok" : "info") as
          | "info"
          | "warn"
          | "ok",
      }));
      if (timeline.length) return timeline;
    }
    return SHELL_ACTIVITY_SEED.filter((e) => e.tab === tab);
  }, [tab, notifications]);

  if (!rightOpen) return null;

  return (
    <DockPanel side="right" title="Activity Center" subtitle="Live enterprise pulse" className="ews-activity-dock">
      <div className="ews-activity-tabs" role="tablist">
        {ACTIVITY_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? "is-active" : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <ul className="ews-activity-list">
        {entries.map((e) => (
          <li key={e.id} className="ews-activity-item">
            <span className={`ews-dot ews-dot--${e.tone || "info"}`} aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="ews-activity-title">{e.title}</p>
              <p className="eds-type-helper truncate">{e.detail}</p>
            </div>
            <time className="eds-type-helper shrink-0" dateTime={e.at}>
              {relTime(e.at)}
            </time>
          </li>
        ))}
      </ul>

      <div className="ews-activity-foot">
        <Link to="/dashboard#notifications" className="eds-type-helper text-[var(--eds-primary)]">
          Notification Center →
        </Link>
        <Badge>{entries.length}</Badge>
      </div>
    </DockPanel>
  );
}
