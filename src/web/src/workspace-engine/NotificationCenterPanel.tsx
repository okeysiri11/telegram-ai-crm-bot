import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import {
  filterByBucket,
  useNotificationStore,
  type AppNotification,
  type NotificationBucket,
  type NotificationKind,
} from "@/notifications/notificationStore";
import { listActivity, clearActivity, type ActivityEntry } from "./activityJournal";

const BUCKETS: { id: NotificationBucket; label: string }[] = [
  { id: "all", label: "All" },
  { id: "unread", label: "Unread" },
  { id: "mentions", label: "Mentions" },
  { id: "warnings", label: "Warnings" },
  { id: "errors", label: "Errors" },
  { id: "success", label: "Success" },
  { id: "jobs", label: "Jobs" },
];

function toneFor(kind: NotificationKind): "success" | "warning" | "danger" | "default" {
  if (kind === "success") return "success";
  if (kind === "warning" || kind === "alert" || kind === "mention") return "warning";
  if (kind === "error") return "danger";
  return "default";
}

export function NotificationCenterPanel() {
  const items = useNotificationStore((s) => s.items);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const clear = useNotificationStore((s) => s.clear);
  const push = useNotificationStore((s) => s.push);
  const [bucket, setBucket] = useState<NotificationBucket>("unread");

  const visible = useMemo(() => filterByBucket(items, bucket), [items, bucket]);
  const unreadCount = useMemo(() => items.filter((i) => !i.read).length, [items]);

  return (
    <Card title="Notification Center">
      <p className="mb-2 eds-type-helper">{unreadCount} unread · Mentions · Warnings · Errors · Success · Jobs</p>
      <div className="mb-3 flex flex-wrap gap-2">
        {BUCKETS.map((b) => (
          <Button
            key={b.id}
            size="sm"
            variant={bucket === b.id ? "primary" : "ghost"}
            onClick={() => setBucket(b.id)}
          >
            {b.label}
          </Button>
        ))}
        <Button
          size="sm"
          variant="secondary"
          onClick={() =>
            push({
              kind: "mention",
              title: "Test mention",
              body: "Notification Center queue check",
              level: "mention",
            })
          }
        >
          Push test
        </Button>
        <Button size="sm" variant="secondary" onClick={() => markAllRead()}>
          Mark all read
        </Button>
        <Button size="sm" variant="ghost" onClick={() => clear()}>
          Clear
        </Button>
      </div>
      <ul className="space-y-2 max-h-72 overflow-y-auto">
        {visible.map((n: AppNotification) => (
          <li key={n.id} className="ews-activity-item">
            <Badge tone={toneFor(n.kind)}>{n.level || n.kind}</Badge>
            <div className="min-w-0 flex-1">
              <p className="ews-activity-title">{n.title}</p>
              <p className="eds-type-helper">{n.body}</p>
            </div>
            {!n.read ? (
              <Button size="sm" variant="ghost" onClick={() => markRead(n.id)}>
                Read
              </Button>
            ) : null}
          </li>
        ))}
        {!visible.length ? <li className="eds-type-helper">Queue empty for this filter.</li> : null}
      </ul>
    </Card>
  );
}

export function ActivityJournalPanel() {
  const [items, setItems] = useState<ActivityEntry[]>(() => listActivity(30));

  return (
    <Card title="Recent Activity">
      <div className="mb-2 flex gap-2">
        <Button size="sm" variant="secondary" onClick={() => setItems(listActivity(30))}>
          Refresh
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            clearActivity();
            setItems([]);
          }}
        >
          Clear
        </Button>
      </div>
      <ul className="space-y-2 max-h-72 overflow-y-auto">
        {items.map((e) => (
          <li key={e.id} className="ews-activity-item">
            <Badge>{e.kind}</Badge>
            <div className="min-w-0 flex-1">
              <p className="ews-activity-title">{e.title}</p>
              <p className="eds-type-helper">{e.detail}</p>
            </div>
            <time className="eds-type-helper shrink-0">{new Date(e.at).toLocaleTimeString()}</time>
          </li>
        ))}
        {!items.length ? <li className="eds-type-helper">No activity yet — open modules to populate.</li> : null}
      </ul>
    </Card>
  );
}
