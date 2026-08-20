import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";
import { getVertical } from "@/vertical-workspace/catalog";
import { useMobileChromeStore } from "./mobileChromeStore";
import { MobileFavoritesRow } from "./MobileFavoritesRow";
import { quickActionsForWorkspace, workspaceHomePath } from "./mobileWorkspace";
import { useState } from "react";

export function MobileHome({
  workspaceId,
  workspaceLabel,
  roleLabel,
  demo,
}: {
  workspaceId: string;
  workspaceLabel: string;
  roleLabel: string;
  demo?: boolean;
}) {
  const home = workspaceHomePath(workspaceId);
  const vertical = getVertical(workspaceId);
  const actions = [...quickActionsForWorkspace(workspaceId), { id: "more", label: "Ещё", href: "__drawer__" }];
  const setDrawerOpen = useMobileChromeStore((s) => s.setDrawerOpen);
  const unread = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const important = (vertical?.tasks || []).slice(0, 3);

  return (
    <div className="ados-mobile-home" data-testid="mobile-home">
      <Card>
        {demo ? (
          <div className="mb-2">
            <Badge tone="warning">DEMO</Badge>
          </div>
        ) : null}
        <p className="eds-type-caption text-[var(--eds-text-muted)]">Workspace</p>
        <h1 className="text-2xl font-semibold" data-testid="mobile-home-workspace">
          {workspaceLabel}
        </h1>
        <p className="mt-1 eds-type-body">Роль: {roleLabel}</p>
        <Link to={home} className="mt-3 block">
          <Button className="w-full">Открыть рабочее пространство</Button>
        </Link>
      </Card>

      <section>
        <h2 className="mb-2 font-semibold">Быстрые действия</h2>
        <div className="ados-mobile-qa">
          {actions.map((action) =>
            action.href === "__drawer__" ? (
              <button key={action.id} type="button" onClick={() => setDrawerOpen(true)}>
                {action.label}
              </button>
            ) : (
              <Link key={action.id} to={action.href}>
                {action.label}
              </Link>
            ),
          )}
        </div>
      </section>

      <MobileFavoritesRow />

      <section>
        <h2 className="mb-2 font-semibold">Важное сегодня</h2>
        <div className="space-y-2">
          <Link to="/crm?view=deals" className="ados-mobile-card block">
            Активные сделки
          </Link>
          {important.map((task) => (
            <div key={task.title} className="ados-mobile-card">
              <p>{task.title}</p>
              <p className="eds-type-caption text-[var(--eds-text-muted)]">{task.status}</p>
            </div>
          ))}
          <Link to="/notifications" className="ados-mobile-card block">
            Уведомления · {unread}
          </Link>
        </div>
      </section>

      <section>
        <Button variant="secondary" className="w-full" onClick={() => setAnalyticsOpen((v) => !v)}>
          {analyticsOpen ? "Скрыть аналитику" : "Показать аналитику"}
        </Button>
        {analyticsOpen && vertical?.stats?.length ? (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {vertical.stats.map((stat) => (
              <div key={stat.label} className="ados-mobile-card">
                <p className="eds-type-caption">{stat.label}</p>
                <p className="text-xl font-semibold">{stat.value}</p>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}
