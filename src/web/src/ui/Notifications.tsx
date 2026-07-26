import { useNotificationStore } from "@/notifications/notificationStore";
import { Badge } from "./Badge";

export function NotificationsPanel() {
  const items = useNotificationStore((s) => s.items);
  const markRead = useNotificationStore((s) => s.markRead);
  const kindLabel: Record<string, string> = {
    ai: "AI",
    workflow: "Process",
    alert: "Error",
    toast: "Success",
    task: "Task",
    in_app: "Notice",
  };
  return (
    <ul className="space-y-2 uws-notif-panel">
      {items.map((n) => (
        <li key={n.id} className="rounded-md border border-[var(--ew-border)] p-2 text-sm eds-anim-fade">
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className="font-medium">{n.title}</span>
            <Badge>{kindLabel[n.kind] || n.kind}</Badge>
          </div>
          <p className="text-[var(--ew-muted)]">{n.body}</p>
          {!n.read ? (
            <button type="button" className="mt-1 text-xs text-[var(--ew-brand)]" onClick={() => markRead(n.id)}>
              Mark read
            </button>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
