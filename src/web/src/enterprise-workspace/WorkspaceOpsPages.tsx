/**
 * Sprint 30.7 — Real workspace module pages (Calendar / Tasks / Notifications).
 * Operational surfaces over existing stores — no placeholders.
 */

import { Link } from "react-router-dom";
import { useMemo, useState } from "react";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Input } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";
import { listActivity } from "@/workspace-engine/activityJournal";
import { RU_QUICK_ACTIONS } from "@/navigation/enterpriseRuNav";

const CALENDAR_EVENTS = [
  { id: "ev1", title: "Утренний брифинг", at: "09:00", route: "/dashboard?mode=executive" },
  { id: "ev2", title: "Синхронизация CRM", at: "11:30", route: "/crm" },
  { id: "ev3", title: "Ревью продакшна", at: "15:00", route: "/production-studio" },
  { id: "ev4", title: "Статус AI Runtime", at: "17:00", route: "/ai-agents" },
];

const TASK_SEED = [
  { id: "t1", title: "Проверить сделки CRM", status: "open", route: "/crm" },
  { id: "t2", title: "Запустить AI-агента", status: "open", route: "/ai-agents" },
  { id: "t3", title: "Обновить документы", status: "done", route: "/documents" },
  { id: "t4", title: "Отчёт аналитики", status: "open", route: "/analytics" },
];

export function CalendarPage() {
  return (
    <WorkspaceLayout>
      <div className="space-y-4" data-testid="workspace-calendar">
        <header>
          <h1 className="eds-type-h1">Календарь</h1>
          <p className="eds-type-helper">Расписание предприятия · связанные модули</p>
        </header>
        <div className="eds-grid eds-grid--dashboard">
          {CALENDAR_EVENTS.map((ev) => (
            <Card key={ev.id} title={ev.title} status={<Badge>{ev.at}</Badge>}>
              <Link className="text-[var(--eds-primary)] eds-type-small" to={ev.route}>
                Открыть →
              </Link>
            </Card>
          ))}
        </div>
        <Card title="Быстрые действия">
          <div className="flex flex-wrap gap-2">
            <Link to="/projects">
              <Button size="sm">Проекты</Button>
            </Link>
            <Link to="/crm">
              <Button size="sm" variant="secondary">
                CRM
              </Button>
            </Link>
            <Link to="/desktop">
              <Button size="sm" variant="ghost">
                Рабочий стол
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

export function TasksPage() {
  const [tasks, setTasks] = useState(TASK_SEED);
  const [title, setTitle] = useState("");

  function addTask() {
    const t = title.trim();
    if (!t) return;
    setTasks((prev) => [{ id: `t_${Date.now()}`, title: t, status: "open", route: "/projects" }, ...prev]);
    setTitle("");
  }

  return (
    <WorkspaceLayout>
      <div className="space-y-4" data-testid="workspace-tasks">
        <header>
          <h1 className="eds-type-h1">Задачи</h1>
          <p className="eds-type-helper">Операционные задачи · переход в модули</p>
        </header>
        <Card title="Создать задачу">
          <div className="flex flex-wrap gap-2">
            <Input
              className="min-w-[220px] flex-1"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Название задачи"
              aria-label="Название задачи"
              onKeyDown={(e) => {
                if (e.key === "Enter") addTask();
              }}
            />
            <Button onClick={addTask}>Создать</Button>
          </div>
        </Card>
        <ul className="space-y-2">
          {tasks.map((task) => (
            <li key={task.id}>
              <Card>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-semibold">{task.title}</p>
                    <Badge tone={task.status === "done" ? "success" : "warning"}>
                      {task.status === "done" ? "Готово" : "Открыта"}
                    </Badge>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        setTasks((prev) =>
                          prev.map((x) =>
                            x.id === task.id ? { ...x, status: x.status === "done" ? "open" : "done" } : x,
                          ),
                        )
                      }
                    >
                      {task.status === "done" ? "Открыть снова" : "Завершить"}
                    </Button>
                    <Link to={task.route}>
                      <Button size="sm" variant="secondary">
                        Открыть модуль
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      </div>
    </WorkspaceLayout>
  );
}

export function NotificationsPage() {
  const items = useNotificationStore((s) => s.items);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const recent = useMemo(() => listActivity(10), [items]);

  return (
    <WorkspaceLayout>
      <div className="space-y-4" data-testid="workspace-notifications">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="eds-type-h1">Уведомления</h1>
            <p className="eds-type-helper">Лента уведомлений и недавняя активность</p>
          </div>
          <Button size="sm" variant="secondary" onClick={() => markAllRead()}>
            Прочитать все
          </Button>
        </header>
        <Card title="Уведомления">
          <ul className="space-y-2">
            {items.slice(0, 20).map((n) => (
              <li key={n.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--eds-border)] pb-2">
                <div>
                  <p className="font-medium eds-type-small">{n.title}</p>
                  <p className="eds-type-helper">{n.body || n.kind}</p>
                </div>
                <div className="flex gap-2">
                  {!n.read ? (
                    <Button size="sm" variant="ghost" onClick={() => markRead(n.id)}>
                      Прочитано
                    </Button>
                  ) : (
                    <Badge tone="success">прочитано</Badge>
                  )}
                </div>
              </li>
            ))}
            {!items.length ? <li className="eds-type-helper">Нет уведомлений</li> : null}
          </ul>
        </Card>
        <Card title="Недавняя активность">
          <ul className="space-y-1 eds-type-small">
            {recent.map((a) => (
              <li key={a.id}>
                {a.title}
                {a.detail ? <span className="text-[var(--eds-text-muted)]"> · {a.detail}</span> : null}
              </li>
            ))}
            {!recent.length ? <li className="eds-type-helper">Пусто</li> : null}
          </ul>
        </Card>
        <Card title="Быстрые действия">
          <div className="flex flex-wrap gap-2">
            {RU_QUICK_ACTIONS.slice(0, 4).map((a) => (
              <Link key={a.id} to={a.route}>
                <Button size="sm" variant="secondary">
                  {a.label}
                </Button>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
