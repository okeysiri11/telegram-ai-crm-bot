import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { LiveWidgetChrome } from "./LiveWidgetChrome";
import type { LiveWidgetId, LiveWidgetPlacement } from "./types";
import { ENTERPRISE_MODULES } from "@/modules/moduleCatalog";
import { TODAY_ITEMS } from "@/dashboard/commandCenterCatalog";
import { useLiveDashboardData } from "./LiveDashboardDataContext";
import { RuntimeHealthWidget } from "@/shell/enterprise/RuntimeHealthWidget";

function Meter({ value, label }: { value: number; label: string }) {
  return (
    <div className="eld-meter">
      <div className="eld-meter-row">
        <span className="font-medium">{label}</span>
        <span>{value}%</span>
      </div>
      <div className="eld-meter-bar" aria-hidden>
        <span style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function toneBadge(tone: string): "success" | "warning" | "danger" | "default" {
  if (tone === "ok") return "success";
  if (tone === "warn") return "warning";
  if (tone === "err") return "danger";
  return "default";
}

/** Renders a single live dashboard widget by id. */
export function LiveWidgetBody({ id }: { id: LiveWidgetId }) {
  const {
    metrics,
    health,
    notifications,
    markAllRead,
    activity,
    activityFilter,
    setActivityFilter,
  } = useLiveDashboardData();
  const crm = ENTERPRISE_MODULES.find((m) => m.id === "crm");
  const projects = ENTERPRISE_MODULES.find((m) => m.id === "projects");
  const knowledge = ENTERPRISE_MODULES.find((m) => m.id === "knowledge");

  switch (id) {
    case "runtime_cpu":
      return <Meter value={metrics.cpuPct} label="CPU" />;
    case "runtime_memory":
      return (
        <>
          <Meter value={metrics.memoryPct} label="Memory" />
          <p className="mt-2 eds-type-helper">{metrics.memoryLabel}</p>
        </>
      );
    case "runtime_ai":
      return (
        <p className="eds-type-small">
          <Badge tone={toneBadge(metrics.aiTone)}>AI</Badge> {metrics.aiStatus}
        </p>
      );
    case "runtime_providers":
      return (
        <p className="eds-type-small">
          <span className={`ews-dot ews-dot--${metrics.providersTone}`} aria-hidden />{" "}
          {metrics.providersDetail}
        </p>
      );
    case "runtime_mcp":
      return (
        <p className="eds-type-small">
          <span className={`ews-dot ews-dot--${metrics.mcpTone}`} aria-hidden /> {metrics.mcpDetail}
        </p>
      );
    case "runtime_agents":
      return (
        <>
          <p className="eds-type-title text-2xl">{metrics.activeAgents}</p>
          <Link to="/ai-agents" className="eds-type-helper text-[var(--eds-primary)]">
            Open AI Agents →
          </Link>
        </>
      );
    case "runtime_jobs":
      return (
        <>
          <p className="eds-type-title text-2xl">{metrics.backgroundJobs}</p>
          <p className="eds-type-helper">Background jobs · workflows</p>
        </>
      );
    case "runtime_queue":
      return (
        <>
          <p className="eds-type-title text-2xl">{metrics.eventQueue}</p>
          <p className="eds-type-helper">Event queue depth</p>
        </>
      );
    case "runtime_notifications":
      return (
        <>
          <p className="eds-type-title text-2xl">{metrics.notifications}</p>
          <button type="button" className="eds-type-helper text-[var(--eds-primary)]" onClick={() => markAllRead()}>
            Mark all read
          </button>
        </>
      );
    case "runtime_sessions":
      return (
        <>
          <p className="eds-type-title text-2xl">{metrics.activeSessions}</p>
          <p className="eds-type-helper">Workspace tabs · sessions</p>
          <Link to="/identity/sessions" className="eds-type-helper text-[var(--eds-primary)]">
            Sessions →
          </Link>
        </>
      );
    case "enterprise_health":
      return <RuntimeHealthWidget compact />;
    case "enterprise_ai":
      return (
        <ul className="space-y-1 eds-type-small">
          {health
            .filter((h) => ["ai", "providers", "voice", "mcp"].includes(h.id))
            .map((h) => (
              <li key={h.id} className="flex items-center gap-2">
                <span className={`ews-dot ews-dot--${h.tone}`} aria-hidden />
                {h.label}: {h.detail}
              </li>
            ))}
        </ul>
      );
    case "enterprise_activity":
      return (
        <>
          <div className="mb-2 flex flex-wrap gap-1">
            {["all", "ai", "system", "user"].map((f) => (
              <button
                key={f}
                type="button"
                className={`eld-chip${activityFilter === f ? " is-active" : ""}`}
                onClick={() => setActivityFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
          <ul className="space-y-1 eds-type-small max-h-40 overflow-y-auto">
            {activity
              .filter(
                (a) =>
                  activityFilter === "all" ||
                  a.kind === activityFilter ||
                  (activityFilter === "system" && a.kind === "navigate"),
              )
              .map((a) => (
                <li key={a.id}>
                  <span className="font-medium">{a.title}</span>
                  <span className="block text-[var(--eds-text-muted)]">{a.detail}</span>
                </li>
              ))}
            {!activity.length ? <li className="eds-type-helper">No activity yet.</li> : null}
          </ul>
        </>
      );
    case "enterprise_notifications":
      return (
        <ul className="space-y-1 eds-type-small max-h-40 overflow-y-auto">
          {notifications.slice(0, 6).map((n) => (
            <li key={n.id}>
              <Badge tone={n.kind === "error" ? "danger" : n.kind === "warning" ? "warning" : "default"}>
                {n.kind}
              </Badge>{" "}
              {n.title}
            </li>
          ))}
        </ul>
      );
    case "enterprise_tasks":
      return (
        <ul className="space-y-1 eds-type-small">
          {TODAY_ITEMS.tasks.map((t) => (
            <li key={t.id}>
              {t.label} <span className="text-[var(--eds-text-muted)]">· {t.due}</span>
            </li>
          ))}
        </ul>
      );
    case "enterprise_projects":
      return (
        <>
          <p className="eds-type-small">{projects?.statusLabel}</p>
          <p className="eds-type-helper">Readiness {projects?.readinessPct}%</p>
          <Link to="/projects" className="eds-type-helper text-[var(--eds-primary)]">
            Open Projects →
          </Link>
        </>
      );
    case "enterprise_crm":
      return (
        <>
          <p className="eds-type-small">{crm?.recentActions[0]}</p>
          <p className="eds-type-helper">{crm?.description}</p>
          <Link to="/crm" className="eds-type-helper text-[var(--eds-primary)]">
            Open CRM →
          </Link>
        </>
      );
    case "enterprise_finance":
      return (
        <>
          <p className="eds-type-title text-xl">₴ 1.28M</p>
          <Badge tone="success">+8.2%</Badge>
          <Link to="/analytics" className="mt-2 block eds-type-helper text-[var(--eds-primary)]">
            Finance / Analytics →
          </Link>
        </>
      );
    case "enterprise_knowledge":
      return (
        <>
          <p className="eds-type-small">{knowledge?.recentActions[0]}</p>
          <Link to="/knowledge" className="eds-type-helper text-[var(--eds-primary)]">
            Knowledge Base →
          </Link>
        </>
      );
    case "enterprise_calendar":
      return (
        <ul className="space-y-1 eds-type-small">
          {TODAY_ITEMS.meetings.map((m) => (
            <li key={m.id}>
              <span className="font-medium">{m.time}</span> {m.label}
            </li>
          ))}
        </ul>
      );
    default:
      return <p className="eds-type-helper">Widget {id}</p>;
  }
}

export function LiveDashboardWidget({ placement }: { placement: LiveWidgetPlacement }) {
  const { bumpTick, refreshHealth } = useLiveDashboardData();
  return (
    <LiveWidgetChrome
      id={placement.id}
      colSpan={placement.colSpan}
      collapsed={placement.collapsed}
      pinned={placement.pinned}
      onRefresh={() => {
        bumpTick();
        refreshHealth();
      }}
    >
      <LiveWidgetBody id={placement.id} />
    </LiveWidgetChrome>
  );
}
