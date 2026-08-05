import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";
import { listActivity } from "./activityJournal";
import { useWorkspaceManager } from "./workspaceManagerStore";
import { ENTERPRISE_MODULES } from "@/modules/moduleCatalog";
import { webConfig } from "@/config/webConfig";
import { QuickActionsPanel } from "./QuickActionsPanel";
import { RuntimeHealthWidget } from "@/shell/enterprise/RuntimeHealthWidget";

/** Sprint 27.3 / 27.4 — working Dashboard widgets (live Runtime Health). */
export function DashboardWorkspaceWidgets() {
  const items = useNotificationStore((s) => s.items);
  const unread = items.filter((i) => !i.read).length;
  const tabs = useWorkspaceManager((s) => s.tabs);
  const activity = listActivity(6);
  const crm = ENTERPRISE_MODULES.find((m) => m.id === "crm");
  const knowledge = ENTERPRISE_MODULES.find((m) => m.id === "knowledge");
  const projects = ENTERPRISE_MODULES.find((m) => m.id === "projects");

  return (
    <section className="space-y-4" aria-label="Dashboard widgets">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card title="System Status">
          <p className="eds-type-small">
            <Badge tone="success">Platform {webConfig.version}</Badge>
          </p>
          <p className="mt-2 eds-type-helper">Sprint {webConfig.sprint} · Workspace Runtime</p>
          <p className="mt-1 eds-type-helper">{tabs.length} open tab(s)</p>
        </Card>
        <Card title="Runtime Health">
          <RuntimeHealthWidget compact />
        </Card>
        <Card title="AI Status">
          <Badge tone="success">Online</Badge>
          <p className="mt-2 eds-type-helper">Providers · Voice · MCP — live in Runtime Health</p>
          <Link to="/ai-agents" className="mt-2 inline-block text-[var(--eds-primary)] eds-type-helper">
            Open AI Agents →
          </Link>
        </Card>
        <Card title="Queue">
          <p className="eds-type-small font-medium">{unread} unread notifications</p>
          <p className="eds-type-helper mt-1">Mentions · Warnings · Jobs</p>
          <Link to="/dashboard#notifications" className="mt-2 inline-block text-[var(--eds-primary)] eds-type-helper">
            Review queue →
          </Link>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Projects">
          <p className="eds-type-small">{projects?.statusLabel}</p>
          <p className="eds-type-helper mt-1">Readiness {projects?.readinessPct}%</p>
          <Link to="/projects" className="mt-2 inline-block text-[var(--eds-primary)] eds-type-helper">
            Open Projects →
          </Link>
        </Card>
        <Card title="CRM Summary">
          <p className="eds-type-small">{crm?.recentActions[0]}</p>
          <p className="eds-type-helper mt-1">{crm?.description}</p>
          <Link to="/crm" className="mt-2 inline-block text-[var(--eds-primary)] eds-type-helper">
            Open CRM →
          </Link>
        </Card>
        <Card title="Knowledge Summary">
          <p className="eds-type-small">{knowledge?.recentActions[0]}</p>
          <p className="eds-type-helper mt-1">{knowledge?.description}</p>
          <Link to="/knowledge" className="mt-2 inline-block text-[var(--eds-primary)] eds-type-helper">
            Open Knowledge →
          </Link>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Analytics">
          <p className="eds-type-helper">KPI pulse and predictive surfaces live on Analytics hub.</p>
          <Link to="/analytics" className="mt-2 inline-block text-[var(--eds-primary)] eds-type-helper">
            Open Analytics →
          </Link>
        </Card>
        <Card title="Activity">
          <ul className="space-y-2 eds-type-small">
            {activity.map((a) => (
              <li key={a.id}>
                <span className="font-medium">{a.title}</span>
                <span className="mt-0.5 block text-[var(--eds-text-muted)]">{a.detail}</span>
              </li>
            ))}
            {!activity.length ? <li className="text-[var(--eds-text-muted)]">No entries yet.</li> : null}
          </ul>
        </Card>
      </div>

      <div id="notifications">
        <QuickActionsPanel />
      </div>
    </section>
  );
}
