/**
 * Enterprise Command Center Dashboard — Sprint 32.3.2.
 * Answers: Where am I? What's happening? What next?
 * Reuses Mission Control, widgets catalog, notifications, RBAC context, AI routes.
 */

import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Charts, Input, NotificationsPanel } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";
import { widgetManager } from "../../workspace/managers/widgetManager";
import { personalizationEngine } from "../../workspace/managers/personalizationEngine";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { MissionControlStrip } from "@/dashboard/MissionControlStrip";
import {
  AI_ACTIVITY,
  BUSINESS_MODULES,
  DEFAULT_COMMAND_LAYOUT,
  KPI_CARDS,
  QUICK_ACTIONS,
  TODAY_ITEMS,
  loadCommandLayout,
  saveCommandLayout,
  type CommandWidgetId,
} from "@/dashboard/commandCenterCatalog";
import { telemetry } from "@/integrations/telemetry";

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const { openPalette } = useNavigationUi();
  const ws = useWorkspaceStore((s) => s.workspace);
  const notifCount = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const first = loadFirstEntry();
  const role = firstEntryRoleCatalog.get(first.roleId);
  const [layout, setLayout] = useState<CommandWidgetId[]>(() => loadCommandLayout());
  const [q, setQ] = useState("");
  const widgets = useMemo(() => widgetManager.list().slice(0, 6), []);
  const personal = personalizationEngine.get();

  const company = first.companyName || ws.company;
  const roleLabel = role?.label || user?.roleId || user?.roles?.[0] || "User";

  function visible(id: CommandWidgetId) {
    return layout.includes(id);
  }

  function hideSection(id: CommandWidgetId) {
    const next = layout.filter((x) => x !== id);
    const saved = saveCommandLayout(next.length ? next : [...DEFAULT_COMMAND_LAYOUT]);
    setLayout(saved);
    personalizationEngine.update({
      homePage: "/dashboard",
    });
    void telemetry.userActivity(`cc_hide:${id}`);
  }

  function resetLayout() {
    const saved = saveCommandLayout([...DEFAULT_COMMAND_LAYOUT]);
    setLayout(saved);
  }

  return (
    <WorkspaceLayout>
      <div className="command-center eds-anim-fade">
        {/* SECTION 1 — Header */}
        <header className="cc-header">
          <div className="flex min-w-0 items-center gap-4">
            <div className="cc-logo" aria-hidden>
              {first.logoDataUrl ? (
                <img src={first.logoDataUrl} alt="" className="h-full w-full object-cover" />
              ) : (
                <span>{company.slice(0, 2).toUpperCase()}</span>
              )}
            </div>
            <div className="min-w-0">
              <p className="eds-type-caption uppercase tracking-[0.16em] text-[var(--eds-text-muted)]">
                Enterprise Command Center
              </p>
              <h1 className="truncate text-2xl font-semibold tracking-tight lg:text-3xl xl:text-4xl">
                {company}
              </h1>
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge>{roleLabel}</Badge>
                <Badge>{ws.project || first.workspaceId || "workspace"}</Badge>
                <Badge tone="success">{notifCount} уведомлений</Badge>
              </div>
            </div>
          </div>
          <div className="flex min-w-[16rem] flex-1 flex-col gap-2 sm:max-w-md">
            <Input
              placeholder="Поиск · ⌘K"
              aria-label="Поиск по workspace"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onFocus={openPalette}
              onKeyDown={(e) => {
                if (e.key === "Enter" && q.trim()) {
                  const hit = searchProvider.search(q)[0];
                  if (hit) {
                    void telemetry.userActivity(`cc_search:${hit.path}`);
                    navigate(hit.path);
                    setQ("");
                  } else {
                    openPalette();
                  }
                }
              }}
            />
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={openPalette}>
                Уведомления ({notifCount})
              </Button>
              <Link to="/settings">
                <Button size="sm" variant="secondary">
                  Профиль
                </Button>
              </Link>
              <Link to="/platform-builder/mission-control">
                <Button size="sm" variant="secondary">
                  Mission Control
                </Button>
              </Link>
            </div>
          </div>
        </header>

        <p className="cc-lead">
          Где я — <strong>{company}</strong>. Что происходит — активность системы и AI ниже. Что делать
          дальше — Quick Actions и рекомендации Concierge.
        </p>

        <div className="cc-grid">
          {/* SECTION 2 — Mission Control */}
          {visible("mission_control") ? (
            <section className="cc-span-12">
              <div className="cc-section-head">
                <h2>Mission Control</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("mission_control")}>
                  Скрыть
                </Button>
              </div>
              <MissionControlStrip />
            </section>
          ) : null}

          {/* SECTION 3 — Today's Overview */}
          {visible("today_overview") ? (
            <section className="cc-span-7">
              <div className="cc-section-head">
                <h2>Today&apos;s Overview</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("today_overview")}>
                  Скрыть
                </Button>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <Card title="Задачи">
                  <ul className="space-y-2 eds-type-small">
                    {TODAY_ITEMS.tasks.map((t) => (
                      <li key={t.id}>
                        <span className="font-medium">{t.label}</span>
                        <span className="mt-0.5 block text-[var(--eds-text-muted)]">{t.due}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
                <Card title="Встречи / календарь">
                  <ul className="space-y-2 eds-type-small">
                    {TODAY_ITEMS.meetings.map((m) => (
                      <li key={m.id}>
                        <Badge>{m.time}</Badge> {m.label}
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 eds-type-small text-[var(--eds-text-muted)]">
                    Дедлайны: {TODAY_ITEMS.deadlines.map((d) => d.label).join(" · ")}
                  </p>
                </Card>
                <Card title="Уведомления">
                  <NotificationsPanel />
                </Card>
                <Card title="Последние изменения" className="md:col-span-2 xl:col-span-3">
                  <ul className="flex flex-wrap gap-3 eds-type-small">
                    {TODAY_ITEMS.changes.map((c) => (
                      <li key={c.id}>
                        <Badge tone="success">{c.label}</Badge>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>
            </section>
          ) : null}

          {/* SECTION 5 adjacent — Quick Actions (placed for visual balance) */}
          {visible("quick_actions") ? (
            <section className="cc-span-5">
              <div className="cc-section-head">
                <h2>Quick Actions</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("quick_actions")}>
                  Скрыть
                </Button>
              </div>
              <Card title="Что сделать дальше">
                <div className="grid gap-2 sm:grid-cols-2">
                  {QUICK_ACTIONS.map((a) => (
                    <Link key={a.id} to={a.route} className="cc-action">
                      <span className="cc-action-hint">{a.hint}</span>
                      <span className="font-medium">{a.label}</span>
                    </Link>
                  ))}
                </div>
              </Card>
            </section>
          ) : null}

          {/* SECTION 4 — Business KPI */}
          {visible("business_kpi") ? (
            <section className="cc-span-12">
              <div className="cc-section-head">
                <h2>Business KPI</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("business_kpi")}>
                  Скрыть
                </Button>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
                {KPI_CARDS.map((k) => (
                  <article key={k.id} className="cc-kpi" data-widget={k.widgetKind}>
                    <p className="cc-kpi-label">{k.label}</p>
                    <p className="cc-kpi-value">{k.value}</p>
                    <Badge tone={k.tone === "up" ? "success" : "default"}>{k.delta}</Badge>
                  </article>
                ))}
              </div>
              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                <Card title="Trend">
                  <Charts labels={["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]} values={[62, 71, 68, 80, 77, 84]} />
                </Card>
                <Card title="Widget registry (existing)">
                  <ul className="columns-2 gap-4 eds-type-small space-y-1">
                    {widgets.map((w) => (
                      <li key={w.widgetId}>
                        <Badge>{w.kind}</Badge> {w.title}
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>
            </section>
          ) : null}

          {/* SECTION 6 — AI Activity */}
          {visible("ai_activity") ? (
            <section className="cc-span-6">
              <div className="cc-section-head">
                <h2>AI Activity</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("ai_activity")}>
                  Скрыть
                </Button>
              </div>
              <Card title="AI Core · Concierge · Team">
                <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">
                  Concierge: {first.conciergeName || "не настроен"} · режим AI Team:{" "}
                  {first.aiTeamMode || "—"}
                </p>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="mb-2 font-medium">Работают</p>
                    <ul className="space-y-1 eds-type-small">
                      {AI_ACTIVITY.running.map((x) => (
                        <li key={x}>
                          <Badge tone="success">{x}</Badge>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="mb-2 font-medium">Последние действия</p>
                    <ul className="space-y-1 eds-type-small text-[var(--eds-text-muted)]">
                      {AI_ACTIVITY.recent.map((x) => (
                        <li key={x}>· {x}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="mb-2 font-medium">Предложения</p>
                    <ul className="space-y-1 eds-type-small">
                      {AI_ACTIVITY.suggestions.map((x) => (
                        <li key={x}>· {x}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="mb-2 font-medium">Автоматизации</p>
                    <ul className="space-y-1 eds-type-small text-[var(--eds-text-muted)]">
                      {AI_ACTIVITY.completed.map((x) => (
                        <li key={x}>· {x}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link to="/platform-builder/ai-team">
                    <Button size="sm">AI Team</Button>
                  </Link>
                  <Link to="/platform-builder/concierge">
                    <Button size="sm" variant="secondary">
                      Concierge
                    </Button>
                  </Link>
                </div>
              </Card>
            </section>
          ) : null}

          {/* SECTION 7 — Business Modules */}
          {visible("business_modules") ? (
            <section className="cc-span-6">
              <div className="cc-section-head">
                <h2>Business Modules</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("business_modules")}>
                  Скрыть
                </Button>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {BUSINESS_MODULES.map((m) => (
                  <Link key={m.id} to={m.route} className="cc-module">
                    <span className="font-medium">{m.label}</span>
                    <span className="eds-type-small text-[var(--eds-text-muted)]">{m.description}</span>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}

          {/* SECTION 8 — Personal Dashboard scaffold */}
          {visible("personal_scaffold") ? (
            <section className="cc-span-12">
              <div className="cc-section-head">
                <h2>Personal Dashboard</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("personal_scaffold")}>
                  Скрыть
                </Button>
              </div>
              <Card title="Персонализация (архитектура)">
                <p className="mb-3 max-w-3xl eds-type-small text-[var(--eds-text-muted)]">
                  Структура готова для следующих спринт: менять расположение виджетов, скрывать блоки,
                  закреплять панели и создавать собственные Dashboard — без нового Dashboard Engine.
                  Сейчас используется `personalizationEngine` + `commandCenterCatalog` layout.
                </p>
                <ul className="mb-4 eds-type-small space-y-1 text-[var(--eds-text-muted)]">
                  <li>· Layout key: ewp_command_center_layout_v1</li>
                  <li>· Home: {personal.homePage}</li>
                  <li>· Виджеты engine: {personal.widgets.join(", ")}</li>
                  <li>· Видимые секции: {layout.join(" · ")}</li>
                </ul>
                <Button size="sm" variant="secondary" onClick={resetLayout}>
                  Сбросить layout
                </Button>
              </Card>
            </section>
          ) : null}
        </div>
      </div>
    </WorkspaceLayout>
  );
}
