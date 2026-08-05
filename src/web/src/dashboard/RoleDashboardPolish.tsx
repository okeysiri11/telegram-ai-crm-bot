/**
 * Sprint 31.1 — Shared role-dashboard polish strip.
 * Composes existing widgets — no parallel dashboard engine.
 */

import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { RuntimeHealthWidget } from "@/shell/enterprise/RuntimeHealthWidget";
import { useNotificationStore } from "@/notifications/notificationStore";
import { listActivity } from "@/workspace-engine/activityJournal";
import { suggestionsForPath } from "@/ai-os-chrome/smartSuggestions";
import { derivePlatformHealth } from "@/platform-integration/platformHealth";

const QUICK_BY_ROLE: Record<string, { label: string; route: string }[]> = {
  admin: [
    { label: "Пользователи", route: "/identity/users" },
    { label: "Здоровье", route: "/health" },
    { label: "Город", route: "/city" },
    { label: "Настройки", route: "/settings" },
  ],
  manager: [
    { label: "CRM", route: "/crm" },
    { label: "Проекты", route: "/projects" },
    { label: "Задачи", route: "/tasks" },
    { label: "Аналитика", route: "/analytics" },
  ],
  employee: [
    { label: "Задачи", route: "/tasks" },
    { label: "Календарь", route: "/calendar" },
    { label: "Документы", route: "/documents" },
    { label: "Знания", route: "/knowledge" },
  ],
  client: [
    { label: "Проекты", route: "/projects" },
    { label: "Документы", route: "/documents" },
    { label: "Уведомления", route: "/notifications" },
    { label: "Профиль", route: "/identity/profile" },
  ],
  dealer: [
    { label: "CRM", route: "/crm" },
    { label: "Клиенты", route: "/identity/users" },
    { label: "Аналитика", route: "/analytics" },
    { label: "Маркетплейс", route: "/marketplace" },
  ],
  owner: [
    { label: "God Mode", route: "/platform-builder/god-mode" },
    { label: "Город", route: "/city" },
    { label: "Здоровье", route: "/health" },
    { label: "AI Runtime", route: "/platform-builder/runtime" },
  ],
};

type Props = {
  role: keyof typeof QUICK_BY_ROLE;
  /** Chart-like health bars from live platform metrics */
  showCharts?: boolean;
};

export function RoleDashboardPolish({ role, showCharts = true }: Props) {
  const items = useNotificationStore((s) => s.items);
  const unread = items.filter((i) => !i.read).length;
  const recentNotifs = items.slice(0, 4);
  const activity = listActivity(5);
  const advice = suggestionsForPath(`/${role}`).slice(0, 3);
  const health = derivePlatformHealth();
  const quick = QUICK_BY_ROLE[role] || QUICK_BY_ROLE.employee;

  return (
    <section className="space-y-4 edm-page-soft" aria-label="Виджеты панели" data-testid="role-dashboard-polish">
      <div className="eds-grid eds-grid--dashboard">
        <Card title="Здоровье runtime" status={<Badge tone="success">live</Badge>}>
          <RuntimeHealthWidget compact />
        </Card>
        <Card title="Уведомления" status={<Badge tone={unread ? "warning" : "success"}>{unread}</Badge>}>
          <ul className="space-y-1 eds-type-small">
            {recentNotifs.map((n) => (
              <li key={n.id} className="truncate">
                {n.title || n.body || "Уведомление"}
              </li>
            ))}
            {!recentNotifs.length ? <li className="eds-type-helper">Нет новых</li> : null}
          </ul>
          <Link className="mt-2 inline-block text-[var(--eds-primary)] eds-type-small" to="/notifications">
            Все уведомления →
          </Link>
        </Card>
        <Card title="Недавняя активность">
          <ul className="space-y-1 eds-type-small">
            {activity.map((a) => (
              <li key={a.id}>
                <span className="font-medium">{a.title}</span>
              </li>
            ))}
            {!activity.length ? <li className="eds-type-helper">Пока пусто</li> : null}
          </ul>
        </Card>
        <Card title="AI-рекомендации">
          <ul className="space-y-2">
            {advice.map((s) => (
              <li key={s.id}>
                <Link className="eds-type-small text-[var(--eds-primary)]" to={s.route}>
                  {s.action}
                </Link>
                <span className="block eds-type-helper">{s.observation}</span>
              </li>
            ))}
            {!advice.length ? (
              <li className="eds-type-helper">Откройте модуль — Concierge подскажет следующий шаг</li>
            ) : null}
          </ul>
        </Card>
      </div>

      {showCharts ? (
        <Card title="Метрики платформы" status={<Badge>{health.level}</Badge>}>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="role-dashboard-charts">
            <MetricBar label="CPU" pct={health.cpuPct} />
            <MetricBar label="Память" pct={health.memoryPct} />
            <MetricBar
              label="Очередь"
              pct={Math.min(100, health.queueLength * 5)}
              caption={`${health.queueLength} задач`}
            />
            <MetricBar
              label="Воркеры"
              pct={health.workersTotal ? Math.round((health.workersBusy / health.workersTotal) * 100) : 0}
              caption={`${health.workersBusy}/${health.workersTotal}`}
            />
          </div>
        </Card>
      ) : null}

      <Card title="Быстрые действия">
        <div className="flex flex-wrap gap-2">
          {quick.map((q) => (
            <Link
              key={q.route}
              to={q.route}
              className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 eds-type-small hover:border-[var(--eds-primary)]"
            >
              {q.label}
            </Link>
          ))}
        </div>
      </Card>
    </section>
  );
}

function MetricBar({ label, pct, caption }: { label: string; pct: number; caption?: string }) {
  const clamped = Math.max(0, Math.min(100, pct));
  const tone =
    clamped > 85 ? "var(--eds-danger)" : clamped > 70 ? "var(--eds-warning)" : "var(--eds-success)";
  return (
    <div>
      <div className="mb-1 flex justify-between eds-type-caption">
        <span>{label}</span>
        <span>{caption || `${clamped}%`}</span>
      </div>
      <div
        className="h-2 overflow-hidden rounded-full"
        style={{ background: "color-mix(in oklab, var(--eds-border) 70%, transparent)" }}
        role="meter"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div
          className="h-full rounded-full transition-[width] duration-300"
          style={{ width: `${clamped}%`, background: tone }}
        />
      </div>
    </div>
  );
}
