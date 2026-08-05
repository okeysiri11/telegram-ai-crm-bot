import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { SHELL_ACTIVITY_SEED } from "@/shell/enterprise/activityCatalog";
import { useRuntimeHealth, toStatusSnapshots } from "@/shell/enterprise/useRuntimeHealth";
import { useNotificationStore } from "@/notifications/notificationStore";
import { webConfig } from "@/config/webConfig";
import { ENTERPRISE_MODULES } from "./moduleCatalog";

/**
 * Sprint 27.2 / 27.4 — Dashboard platform pulse (live Runtime Health probes).
 */
export function PlatformPulsePanel() {
  const items = useNotificationStore((s) => s.items);
  const notifications = items.filter((i) => !i.read);
  const { items: healthItems } = useRuntimeHealth(20_000);
  const statuses = toStatusSnapshots(healthItems);

  const recent = SHELL_ACTIVITY_SEED.filter((e) => e.tab === "recent").slice(0, 5);
  const quick = ENTERPRISE_MODULES.filter((m) => m.id !== "dashboard").slice(0, 8);

  return (
    <section className="space-y-4" aria-label="Platform pulse">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Runtime & Backend">
          <ul className="space-y-2 eds-type-small">
            {statuses
              .filter((s) => ["runtime", "api", "database", "build", "version"].includes(s.id))
              .map((s) => (
                <li key={s.id} className="flex items-center gap-2">
                  <span className={`ews-dot ews-dot--${s.tone}`} aria-hidden />
                  <span className="font-medium">{s.label}</span>
                  <span className="text-[var(--eds-text-muted)]">{s.detail}</span>
                </li>
              ))}
          </ul>
        </Card>
        <Card title="AI · Providers · Voice · MCP">
          <ul className="space-y-2 eds-type-small">
            {statuses
              .filter((s) => ["providers", "voice", "mcp", "queue"].includes(s.id))
              .map((s) => (
                <li key={s.id} className="flex items-center gap-2">
                  <span className={`ews-dot ews-dot--${s.tone}`} aria-hidden />
                  <span className="font-medium">{s.label}</span>
                  <span className="text-[var(--eds-text-muted)]">{s.detail}</span>
                </li>
              ))}
          </ul>
          <p className="mt-2 eds-type-helper">
            Sprint {webConfig.sprint} · Health Service singleton (no per-panel poll)
          </p>
        </Card>
        <Card title="Notifications & Activity">
          <p className="eds-type-small">
            <Badge tone={notifications.length ? "warning" : "success"}>
              {notifications.length} unread
            </Badge>
          </p>
          <ul className="mt-2 space-y-1 eds-type-helper">
            {recent.map((e) => (
              <li key={e.id}>{e.title}</li>
            ))}
          </ul>
          <Link to="/dashboard#notifications" className="mt-2 inline-block text-[var(--eds-primary)] eds-type-helper">
            Open Notification Center →
          </Link>
        </Card>
      </div>
      <Card title="Quick module jump">
        <div className="flex flex-wrap gap-2">
          {quick.map((m) => (
            <Link key={m.id} to={m.route} className="cc-action eds-type-small">
              {m.label}
            </Link>
          ))}
        </div>
      </Card>
    </section>
  );
}
