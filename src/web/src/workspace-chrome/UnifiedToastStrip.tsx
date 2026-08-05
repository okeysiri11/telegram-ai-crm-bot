/**
 * Unified notification toast strip — Sprint 32.3.6.
 * Uses existing notificationStore; no new Notification System.
 */

import { useEffect, useState } from "react";
import { Badge, Button } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";

export function UnifiedToastStrip() {
  const items = useNotificationStore((s) => s.items);
  const markRead = useNotificationStore((s) => s.markRead);
  const [visibleId, setVisibleId] = useState<string | null>(null);

  const latest = items.find((i) => !i.read) || items[0] || null;

  useEffect(() => {
    if (!latest || latest.read) {
      setVisibleId(null);
      return;
    }
    setVisibleId(latest.id);
    const id = window.setTimeout(() => setVisibleId(null), 6_000);
    return () => window.clearTimeout(id);
  }, [latest?.id, latest?.read]);

  if (!latest || visibleId !== latest.id) return null;

  const tone =
    latest.kind === "alert"
      ? "danger"
      : latest.kind === "ai" || latest.kind === "workflow"
        ? "success"
        : latest.kind === "toast"
          ? "warning"
          : "default";

  return (
    <div className="uws-toast edm-toast" role="status">
      <Badge tone={tone as "default" | "success" | "warning" | "danger"}>{latest.kind}</Badge>
      <div className="min-w-0 flex-1">
        <p className="font-medium eds-type-small">{latest.title}</p>
        <p className="eds-type-small text-[var(--eds-text-muted)]">{latest.body}</p>
      </div>
      <Button size="sm" variant="ghost" onClick={() => markRead(latest.id)}>
        OK
      </Button>
    </div>
  );
}
