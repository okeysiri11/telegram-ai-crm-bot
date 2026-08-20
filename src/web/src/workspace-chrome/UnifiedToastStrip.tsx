/**
 * Unified notification toast strip — Sprint 32.3.6 / mobile UX.
 * Historical unread items stay in Notification Center. Only NEW events toast.
 * Max 2 toasts; auto-dismiss except sticky errors.
 */

import { useEffect, useRef, useState } from "react";
import { Badge, Button } from "@/ui";
import { useNotificationStore, type AppNotification } from "@/notifications/notificationStore";

const AUTO_MS = 5_000;
const MAX_TOASTS = 2;

function isSticky(n: AppNotification): boolean {
  return n.kind === "error" || n.level === "error" || n.kind === "alert";
}

export function UnifiedToastStrip() {
  const items = useNotificationStore((s) => s.items);
  const markRead = useNotificationStore((s) => s.markRead);
  const seen = useRef<Set<string>>(new Set());
  const [queue, setQueue] = useState<AppNotification[]>([]);
  const bootstrapped = useRef(false);

  useEffect(() => {
    if (!bootstrapped.current) {
      items.forEach((item) => seen.current.add(item.id));
      bootstrapped.current = true;
      return;
    }
    const newcomers = items.filter((item) => !item.read && !seen.current.has(item.id));
    if (!newcomers.length) return;
    newcomers.forEach((item) => seen.current.add(item.id));
    setQueue((current) => {
      const sticky = current.filter(isSticky);
      const next = [...newcomers, ...sticky.filter((s) => !newcomers.some((n) => n.id === s.id))];
      return next.slice(0, MAX_TOASTS);
    });
  }, [items]);

  useEffect(() => {
    const timers = queue
      .filter((n) => !isSticky(n))
      .map((n) =>
        window.setTimeout(() => {
          markRead(n.id);
          setQueue((current) => current.filter((x) => x.id !== n.id));
        }, AUTO_MS),
      );
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, [queue, markRead]);

  if (!queue.length) return null;

  return (
    <div className="flex flex-col gap-2" data-testid="unified-toast-strip" aria-live="polite">
      {queue.map((latest) => {
        const tone =
          latest.kind === "alert" || latest.kind === "error"
            ? "danger"
            : latest.kind === "ai" || latest.kind === "workflow" || latest.kind === "success"
              ? "success"
              : latest.kind === "warning"
                ? "warning"
                : "default";
        return (
          <div key={latest.id} className="uws-toast edm-toast" role="status">
            <Badge tone={tone as "default" | "success" | "warning" | "danger"}>{latest.kind}</Badge>
            <div className="min-w-0 flex-1">
              <p className="font-medium eds-type-small">{latest.title}</p>
              <p className="eds-type-small text-[var(--eds-text-muted)]">{latest.body}</p>
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                markRead(latest.id);
                setQueue((current) => current.filter((x) => x.id !== latest.id));
              }}
            >
              {isSticky(latest) ? "OK" : "×"}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
