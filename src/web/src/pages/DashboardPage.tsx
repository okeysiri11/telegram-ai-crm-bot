/**
 * Enterprise Command Center Dashboard — Sprint 32.3.2 + Live 32.3.4 + Executive 32.3.5.
 * EP-01: CEO Morning Experience — answers happening / attention / AI / risks / opportunities in ~10s.
 */

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Charts, Input, NotificationsPanel, Skeleton } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";
import { personalizationEngine } from "../../workspace/managers/personalizationEngine";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { MissionControlStrip } from "@/dashboard/MissionControlStrip";
import { ExecutiveMorningBrief } from "@/dashboard/ExecutiveMorningBrief";
import { deriveMorningBrief } from "@/dashboard/deriveMorningBrief";
import {
  DEFAULT_COMMAND_LAYOUT,
  KPI_CARDS,
  QUICK_ACTIONS,
  TODAY_ITEMS,
  loadCommandLayout,
  saveCommandLayout,
  type CommandWidgetId,
} from "@/dashboard/commandCenterCatalog";
import {
  ActivityFeedPanel,
  AiOperationsPanel,
  EnterpriseHealthPanel,
  LiveMetaBar,
  MissionTimelinePanel,
  useLiveEnterprise,
} from "@/live-ops";
import {
  EXECUTIVE_LAYOUT,
  loadExecutivePref,
  resolveExecutiveMode,
  saveExecutivePref,
} from "@/demo/executiveMode";
import { EnterpriseIntelligenceDashboard } from "@/enterprise-intelligence";
import { telemetry } from "@/integrations/telemetry";
import { CTA, rememberNavDecision, withDecisionQuery } from "@/decision-flow";
import { EnterpriseModuleGrid } from "@/shell/enterprise";
import { PlatformPulsePanel } from "@/modules/PlatformPulsePanel";
import { rememberModuleRoute } from "@/modules/lastModuleStore";
import { DashboardWorkspaceWidgets } from "@/workspace-engine/DashboardWorkspaceWidgets";
import { NotificationCenterPanel, ActivityJournalPanel } from "@/workspace-engine/NotificationCenterPanel";
import { QuickActionsPanel } from "@/workspace-engine/QuickActionsPanel";
import {
  AiCommandCenterPanel,
  EnterpriseMetricsStrip,
  GlobalActivityFeed,
  UniversalQuickActionsBar,
} from "@/command-center-runtime";
import { LiveDashboardShell } from "@/live-dashboard";
import { BetaHomeDashboard } from "@/dashboard/BetaHomeDashboard";
import { ExecutiveSummaryDashboard, useExperienceModeStore } from "@/ux-revolution";
import { MobileHome, useIsMobile, isDemoAccount, workspaceLabel, resolveMobileHomeWorkspace } from "@/shell/mobile";
import { resolveRoleLabel, useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";

const KPI_ROUTES: Record<string, string> = {
  sales: "/workspace/crm",
  clients: "/workspace/crm",
  deals: "/workspace/crm",
  processes: "/platform-builder/workflow-center",
  automation: "/platform-builder/ai-team",
  documents: "/workspace/docs",
};

const KPI_WHY: Record<string, string> = {
  sales: "Денежный пульс бизнеса сегодня",
  clients: "Рост базы влияет на pipeline",
  deals: "Активные сделки требуют внимания",
  processes: "Операционная нагрузка прямо сейчас",
  automation: "Доля работы, которую берёт AI",
  documents: "Знания, доступные команде",
};

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { openPalette } = useNavigationUi();
  const ws = useWorkspaceStore((s) => s.workspace);
  const notifCount = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const first = loadFirstEntry();
  const role = firstEntryRoleCatalog.get(first.roleId);
  const [layout, setLayout] = useState<CommandWidgetId[]>(() => loadCommandLayout());
  const [q, setQ] = useState("");
  const [execOverride, setExecOverride] = useState<boolean | null>(() => loadExecutivePref());
  const [intelOpen, setIntelOpen] = useState(false);
  const personal = personalizationEngine.get();
  const { snapshot, busy, error, refresh } = useLiveEnterprise(true);
  const uxMode = useExperienceModeStore((s) => s.mode);
  const isMobile = useIsMobile();
  const storedVertical = useVerticalWorkspaceStore((s) => s.verticalId);
  const roleId = useRoleSwitcher((s) => s.activeRoleId);
  const preferExecutiveSummary =
    params.get("mode") === "executive" ||
    (uxMode === "simple" && params.get("mode") !== "full");

  useEffect(() => {
    document.title = "Главная · ADOS Enterprise";
    rememberModuleRoute("/dashboard");
  }, []);

  const company = first.companyName || ws.company;
  const roleLabel = role?.label || resolveRoleLabel(roleId) || user?.roleId || user?.roles?.[0] || "User";

  const executive = resolveExecutiveMode({
    queryMode: params.get("mode"),
    roleId: first.roleId || user?.roleId,
    roles: user?.roles,
    storedPref: execOverride,
  });

  const effectiveLayout = executive ? EXECUTIVE_LAYOUT : layout;

  const brief = useMemo(
    () =>
      deriveMorningBrief(snapshot, {
        company,
        unread: notifCount,
        conciergeName: first.conciergeName,
      }),
    [snapshot, company, notifCount, first.conciergeName],
  );

  const liveKpis = useMemo(() => {
    const healthy = snapshot.health.filter((h) => h.ok).length;
    const feedN = snapshot.activity.length;
    return KPI_CARDS.map((k) => {
      if (k.id === "automation") {
        return { ...k, value: `${Math.min(99, 60 + healthy * 4)}%`, delta: snapshot.aiOps.completed[0] || k.delta };
      }
      if (k.id === "processes") {
        return { ...k, value: String(snapshot.aiOps.queue.length + healthy), delta: busy ? "live…" : "stable" };
      }
      if (k.id === "deals") {
        return { ...k, delta: `feed ${feedN}` };
      }
      return k;
    });
  }, [snapshot, busy]);

  function visible(id: CommandWidgetId) {
    return effectiveLayout.includes(id);
  }

  function hideSection(id: CommandWidgetId) {
    if (executive) return;
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

  function setExecutive(on: boolean) {
    setExecOverride(on);
    saveExecutivePref(on);
    void telemetry.userActivity(on ? "executive_on" : "executive_off");
    navigate(on ? "/dashboard?mode=executive" : "/dashboard?mode=full");
  }

  if (isMobile) {
    const verticalId = resolveMobileHomeWorkspace(storedVertical, "/");
    return (
      <WorkspaceLayout>
        <MobileHome
          workspaceId={verticalId}
          workspaceLabel={workspaceLabel(verticalId)}
          roleLabel={roleLabel}
          demo={isDemoAccount(user?.email, user?.tenantId)}
        />
      </WorkspaceLayout>
    );
  }

  return (
    <WorkspaceLayout>
      <div className={`command-center eds-anim-fade${executive ? " is-executive" : ""}`}>
        {preferExecutiveSummary ? (
          <ExecutiveSummaryDashboard />
        ) : (
          <>
        {!executive ? <BetaHomeDashboard /> : null}

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
                {executive ? "Режим руководителя · Утренний брифинг" : "Командный центр предприятия"}
              </p>
              <h1 className="truncate text-2xl font-semibold tracking-tight lg:text-3xl xl:text-4xl">
                {company}
              </h1>
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge>{roleLabel}</Badge>
                <Badge tone={brief.tone === "alert" ? "danger" : brief.tone === "watch" ? "warning" : "success"}>
                  {brief.tone === "calm" ? "Под контролем" : brief.tone === "watch" ? "Внимание" : "Действие"}
                </Badge>
                <Badge tone="success">{notifCount} уведомлений</Badge>
                {executive ? <Badge tone="warning">Руководитель</Badge> : null}
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
              <Button size="sm" variant={executive ? "secondary" : "ghost"} onClick={() => setExecutive(!executive)}>
                {executive ? "Полный Dashboard" : "Executive Mode"}
              </Button>
              <Button size="sm" variant="secondary" onClick={openPalette}>
                Уведомления ({notifCount})
              </Button>
              <Link to="/settings">
                <Button size="sm" variant="secondary">
                  Settings
                </Button>
              </Link>
              <Link to="/platform-builder/control-tower">
                <Button size="sm">Control Tower</Button>
              </Link>
            </div>
          </div>
        </header>

        <LiveMetaBar snapshot={snapshot} busy={busy} error={error} onRefresh={() => void refresh()} />

        {busy && snapshot.updatedAt === new Date(0).toISOString() ? (
          <Card title="Загрузка Morning Brief" className="mb-4">
            <Skeleton rows={5} height="1.25rem" />
          </Card>
        ) : (
          <div className="mb-4">
            <ExecutiveMorningBrief brief={brief} conciergeName={first.conciergeName} />
          </div>
        )}

        <section className="mb-6" aria-label="Enterprise Live Dashboard">
          <LiveDashboardShell />
        </section>

        <section className="mb-6" aria-label="Enterprise modules">
          <div className="cc-section-head">
            <h2>Enterprise Modules</h2>
            <p className="eds-type-helper">CRM · ERP · AI · Knowledge · Analytics · more</p>
          </div>
          <EnterpriseModuleGrid />
        </section>

        <section className="mb-6" aria-label="Enterprise metrics">
          <div className="cc-section-head">
            <h2>Enterprise Metrics</h2>
            <p className="eds-type-helper">Projects · Clients · Tasks · Revenue · AI · Workflows · Health · API</p>
          </div>
          <EnterpriseMetricsStrip />
        </section>

        <section className="mb-6" aria-label="Universal quick actions">
          <div className="cc-section-head">
            <h2>Universal Quick Actions</h2>
            <p className="eds-type-helper">Create and open from the Command Center · also ⌘/Ctrl+K</p>
          </div>
          <UniversalQuickActionsBar />
        </section>

        <section className="mb-6" aria-label="AI Command Center">
          <div className="cc-section-head">
            <h2>AI Command Center</h2>
            <p className="eds-type-helper">Agents · jobs · providers · memory · cost</p>
          </div>
          <AiCommandCenterPanel />
        </section>

        <section className="mb-6" aria-label="Global activity feed">
          <div className="cc-section-head">
            <h2>Global Activity Feed</h2>
            <p className="eds-type-helper">AI · System · CRM · User · Jobs · Workflows · Errors</p>
          </div>
          <GlobalActivityFeed />
        </section>

        <section className="mb-6" aria-label="Platform pulse">
          <div className="cc-section-head">
            <h2>Platform Pulse</h2>
            <p className="eds-type-helper">Runtime · AI · queues · API · events</p>
          </div>
          <PlatformPulsePanel />
        </section>

        <section className="mb-6" aria-label="Workspace widgets">
          <div className="cc-section-head">
            <h2>Workspace Widgets</h2>
            <p className="eds-type-helper">System · CRM · Knowledge · Activity · Quick Actions</p>
          </div>
          <DashboardWorkspaceWidgets />
        </section>

        <section className="mb-6 grid gap-4 lg:grid-cols-2" aria-label="Notifications and activity">
          <NotificationCenterPanel />
          <ActivityJournalPanel />
        </section>

        <section className="mb-6" aria-label="Quick actions">
          <QuickActionsPanel />
        </section>

        <div className="mb-4">
          <button
            type="button"
            className="eds-ops-chrome-toggle"
            onClick={() => setIntelOpen((v) => !v)}
          >
            {intelOpen ? "Hide Enterprise Intelligence" : "Show Enterprise Intelligence details"}
          </button>
          {intelOpen ? (
            <section className="mt-3">
              <EnterpriseIntelligenceDashboard />
            </section>
          ) : null}
        </div>

        <div className="cc-grid">
          {visible("business_kpi") ? (
            <section className="cc-span-12">
              <div className="cc-section-head">
                <h2>Business pulse</h2>
                {!executive ? (
                  <Button size="sm" variant="ghost" onClick={() => hideSection("business_kpi")}>
                    Скрыть
                  </Button>
                ) : null}
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 edm-stagger">
                {liveKpis.map((k) => (
                  <Link
                    key={k.id}
                    to={withDecisionQuery(KPI_ROUTES[k.id] || "/platform-builder/control-tower", {
                      from: "/dashboard",
                      step: "act",
                      focus: k.id,
                    })}
                    className="cc-kpi cc-kpi--decision edm-kpi"
                    data-widget={k.widgetKind}
                    onClick={() => {
                      rememberNavDecision("/dashboard", KPI_ROUTES[k.id] || "/platform-builder/control-tower", KPI_WHY[k.id] || k.label, "act");
                      void telemetry.userActivity(`kpi_open:${k.id}`);
                    }}
                  >
                    <p className="cc-kpi-label">{k.label}</p>
                    <p className="cc-kpi-value edm-kpi">{k.value}</p>
                    <Badge tone={k.tone === "up" ? "success" : "default"}>{k.delta}</Badge>
                    <p className="cc-kpi-why">{KPI_WHY[k.id] || "Ключевой сигнал"}</p>
                    <span className="cc-kpi-next">{CTA.kpi[k.id] || "Take action"} →</span>
                  </Link>
                ))}
              </div>
              {!executive ? (
                <div className="mt-4">
                  <Card title="Trend">
                    <Charts labels={["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]} values={[62, 71, 68, 80, 77, 84]} />
                  </Card>
                </div>
              ) : null}
            </section>
          ) : null}

          {visible("quick_actions") ? (
            <section className="cc-span-5">
              <div className="cc-section-head">
                <h2>Решить сейчас</h2>
                {!executive ? (
                  <Button size="sm" variant="ghost" onClick={() => hideSection("quick_actions")}>
                    Скрыть
                  </Button>
                ) : null}
              </div>
              <Card title="Decision flow">
                <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">
                  Observation → Recommendation → Decision → Action. One obvious next step.
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {QUICK_ACTIONS.map((a) => (
                    <Link
                      key={a.id}
                      to={withDecisionQuery(a.route, { from: "/dashboard", step: "decide", focus: a.id })}
                      className="cc-action"
                      onClick={() => rememberNavDecision("/dashboard", a.route, a.label, "decide")}
                    >
                      <span className="cc-action-hint">{a.hint}</span>
                      <span className="font-medium">{CTA.quick[a.id] || a.label}</span>
                    </Link>
                  ))}
                </div>
              </Card>
            </section>
          ) : null}

          {visible("mission_control") ? (
            <section className={executive ? "cc-span-7" : "cc-span-12"}>
              <div className="cc-section-head">
                <h2>Mission Control</h2>
                {!executive ? (
                  <Button size="sm" variant="ghost" onClick={() => hideSection("mission_control")}>
                    Скрыть
                  </Button>
                ) : null}
              </div>
              <MissionControlStrip />
            </section>
          ) : null}

          {visible("enterprise_health") ? (
            <section className="cc-span-12">
              <div className="cc-section-head">
                <h2>Enterprise Health</h2>
                {!executive ? (
                  <Button size="sm" variant="ghost" onClick={() => hideSection("enterprise_health")}>
                    Скрыть
                  </Button>
                ) : null}
              </div>
              <EnterpriseHealthPanel health={snapshot.health} />
            </section>
          ) : null}

          {visible("activity_feed") ? (
            <section className="cc-span-6">
              <div className="cc-section-head">
                <h2>Activity Feed</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("activity_feed")}>
                  Скрыть
                </Button>
              </div>
              <ActivityFeedPanel items={snapshot.activity} />
            </section>
          ) : null}

          {visible("mission_timeline") ? (
            <section className="cc-span-6">
              <div className="cc-section-head">
                <h2>Mission Timeline</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("mission_timeline")}>
                  Скрыть
                </Button>
              </div>
              <MissionTimelinePanel buckets={snapshot.timeline} />
            </section>
          ) : null}

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
                </Card>
                <Card title="Уведомления">
                  <NotificationsPanel />
                </Card>
              </div>
            </section>
          ) : null}

          {visible("ai_activity") ? (
            <section className="cc-span-6">
              <div className="cc-section-head">
                <h2>AI Operations</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("ai_activity")}>
                  Скрыть
                </Button>
              </div>
              <AiOperationsPanel ops={snapshot.aiOps} />
              <div className="mt-3 flex flex-wrap gap-2">
                <Link to="/platform-builder/ai-team">
                  <Button size="sm">AI Team</Button>
                </Link>
                <Link to="/platform-builder/concierge">
                  <Button size="sm" variant="secondary">
                    Concierge
                  </Button>
                </Link>
              </div>
            </section>
          ) : null}

          {visible("ai_recommendations") ? (
            <section className="cc-span-6">
              <div className="cc-section-head">
                <h2>AI Concierge</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("ai_recommendations")}>
                  Скрыть
                </Button>
              </div>
              <Card title="Главный проводник — Concierge dock">
                <p className="eds-type-small text-[var(--eds-text-muted)]">
                  Утренние рекомендации уже в Morning Brief. Concierge помогает углубить любое решение.
                </p>
                <div className="mt-3">
                  <Link to="/platform-builder/concierge">
                    <Button size="sm">Open AI Concierge</Button>
                  </Link>
                </div>
              </Card>
            </section>
          ) : null}

          {visible("personal_scaffold") ? (
            <section className="cc-span-12">
              <div className="cc-section-head">
                <h2>Personal Dashboard</h2>
                <Button size="sm" variant="ghost" onClick={() => hideSection("personal_scaffold")}>
                  Скрыть
                </Button>
              </div>
              <Card title="Персонализация">
                <p className="mb-3 max-w-3xl eds-type-small text-[var(--eds-text-muted)]">
                  Layout: ewp_command_center_layout_v4 · Home: {personal.homePage}
                </p>
                <Button size="sm" variant="secondary" onClick={resetLayout}>
                  Сбросить layout
                </Button>
              </Card>
            </section>
          ) : null}
        </div>
          </>
        )}
      </div>
    </WorkspaceLayout>
  );
}
