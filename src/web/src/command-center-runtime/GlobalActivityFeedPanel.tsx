import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import {
  buildGlobalActivityFeed,
  FEED_KIND_LABELS,
  type FeedKind,
  type GlobalFeedItem,
} from "./globalActivityFeed";
import { useNotificationStore } from "@/notifications/notificationStore";

function toneFor(kind: FeedKind): "success" | "warning" | "danger" | "default" {
  if (kind === "error") return "danger";
  if (kind === "warning") return "warning";
  if (kind === "ai" || kind === "workflow") return "success";
  return "default";
}

const FILTERS: Array<FeedKind | "all"> = [
  "all",
  "ai",
  "system",
  "crm",
  "user",
  "job",
  "notification",
  "workflow",
  "error",
  "warning",
];

/** Live enterprise timeline — journal + notifications + workflow/CRM signals. */
export function GlobalActivityFeed({ compact = false }: { compact?: boolean }) {
  const notifTick = useNotificationStore((s) => s.items.length);
  const [filter, setFilter] = useState<FeedKind | "all">("all");
  const [tick, setTick] = useState(0);

  const items = useMemo(() => {
    void notifTick;
    void tick;
    const all = buildGlobalActivityFeed(compact ? 12 : 40);
    return filter === "all" ? all : all.filter((i) => i.kind === filter);
  }, [filter, notifTick, tick, compact]);

  return (
    <Card title="Global Activity Feed">
      <div className="mb-2 flex flex-wrap gap-1">
        {FILTERS.map((f) => (
          <Button
            key={f}
            size="sm"
            variant={filter === f ? "primary" : "ghost"}
            onClick={() => setFilter(f)}
          >
            {f === "all" ? "All" : FEED_KIND_LABELS[f]}
          </Button>
        ))}
        <Button size="sm" variant="secondary" onClick={() => setTick((t) => t + 1)}>
          Refresh
        </Button>
      </div>
      <ul className={`space-y-2 ${compact ? "max-h-56" : "max-h-96"} overflow-y-auto`} aria-live="polite">
        {items.map((item: GlobalFeedItem) => (
          <li key={item.id} className="ews-activity-item">
            <Badge tone={toneFor(item.kind)}>{FEED_KIND_LABELS[item.kind]}</Badge>
            <div className="min-w-0 flex-1">
              <p className="ews-activity-title">{item.title}</p>
              <p className="eds-type-helper truncate">{item.detail}</p>
            </div>
            <time className="eds-type-helper shrink-0">{new Date(item.at).toLocaleTimeString()}</time>
          </li>
        ))}
        {!items.length ? <li className="eds-type-helper">No events for this filter.</li> : null}
      </ul>
    </Card>
  );
}
