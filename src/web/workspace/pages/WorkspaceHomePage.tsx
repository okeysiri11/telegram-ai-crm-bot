import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Charts } from "@/ui";
import { buildWorkspaceDashboard } from "../dashboard/workspaceDashboard";
import { WidgetCard } from "../components/WidgetCard";
import { QuickActionsBar } from "../components/QuickActionsBar";
import { SearchPanel } from "../components/SearchPanel";
import {
  favoritesManager,
  layoutManager,
  recentActivity,
  widgetManager,
  workspaceManager,
} from "../managers";
import { liveUpdates } from "../realtime/liveUpdates";
import { useWorkspaceStore } from "@/workspace/workspaceStore";

export function WorkspaceHomePage() {
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const [tick, setTick] = useState(0);
  const [lastLive, setLastLive] = useState<string>("—");
  const dash = buildWorkspaceDashboard();
  const widgets = widgetManager.list().slice(0, 8);

  useEffect(() => {
    const ws = workspaceManager.active();
    setWorkspace({
      company: ws.organization,
      department: ws.kind,
      project: ws.name,
      permissions: ws.permissions,
      activeModules: ws.activeModules,
    });
    liveUpdates.connect();
    const unsub = liveUpdates.subscribe((u) => {
      setLastLive(`${u.source} · ${u.widgetIds.length} widgets · ${u.at}`);
      setTick((t) => t + 1);
    });
    // EP-07: rely on shared live poller via liveUpdates; no duplicate interval.
    return () => {
      unsub();
    };
  }, [setWorkspace]);

  void tick;

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="eds-type-h1">Workspace</h1>
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              {dash.workspace.name} · {dash.workspace.kind} · modules: {dash.workspace.activeModules.join(", ")}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/workspace/settings"><Button size="sm" variant="secondary">Settings</Button></Link>
            <Link to="/workspace/layout"><Button size="sm" variant="secondary">Layout</Button></Link>
            <Link to="/workspace/dashboards"><Button size="sm">Dashboards</Button></Link>
          </div>
        </div>

        <QuickActionsBar />

        <div className="eds-grid eds-grid--dashboard">
          <Card title="KPI Overview">
            <Charts labels={["Mon", "Tue", "Wed", "Thu", "Fri"]} values={[62, 71, 68, 80, 77]} />
          </Card>
          <Card title="AI Assistant">
            <p className="eds-type-small">Ask about workflows, risks, and opportunities.</p>
            <Badge tone="success">ready</Badge>
          </Card>
          <Card title="Today's Tasks">
            <ul className="space-y-1 eds-type-small">
              <li>Approve invoice #1042</li>
              <li>Review migration checklist</li>
              <li>Confirm AI recommendation</li>
            </ul>
          </Card>
          <Card title="Calendar">
            <p className="eds-type-small">Today · 3 meetings · 1 release window</p>
          </Card>
          <Card title="Notifications">
            <p className="eds-type-small">In-app alerts synced with Notification Center</p>
          </Card>
          <Card title="Active Workflows">
            <p className="eds-type-small">Billing · Onboarding · Security gate</p>
          </Card>
          <Card title="Team Activity">
            <ul className="space-y-1 eds-type-small">
              {dash.sections.teamActivity.map((a) => (
                <li key={a.id}>{a.kind}: {a.summary}</li>
              ))}
            </ul>
          </Card>
          <Card title="Reports">
            <div className="flex flex-wrap gap-2">
              {dash.sections.reports.map((r) => (
                <Badge key={r.id}>{r.label}</Badge>
              ))}
            </div>
          </Card>
          <Card title="Marketplace">
            <p className="eds-type-small">Extension catalog · featured packs</p>
          </Card>
          <Card title="System Status">
            <Badge tone="success">healthy</Badge>
            <p className="mt-2 eds-type-caption">Live: {lastLive}</p>
          </Card>
        </div>

        <div className="eds-grid eds-grid--dashboard">
          <SearchPanel />
          <Card title="Favorites">
            <ul className="space-y-1">
              {favoritesManager.list().map((f) => (
                <li key={f.id} className="eds-type-small">
                  <Link className="text-[var(--eds-primary)]" to={f.path}>{f.kind}: {f.label}</Link>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Recent activity">
            <ul className="space-y-1 eds-type-small">
              {recentActivity.list().map((a) => (
                <li key={a.id}>{a.kind} — {a.summary}</li>
              ))}
            </ul>
          </Card>
          <Card title="Layout">
            <p className="eds-type-small">Features: {layoutManager.features().join(", ")}</p>
            <p className="eds-type-caption mt-1">
              Saved layout · multi-monitor ready · {layoutManager.get(dash.workspace.workspaceId).widgets.length} widgets
            </p>
          </Card>
        </div>

        <div>
          <h2 className="eds-type-h3 mb-3">Widget board</h2>
          <div className="eds-grid eds-grid--dashboard">
            {widgets.map((widget) => (
              <WidgetCard key={widget.widgetId} widget={widget} onChange={() => setTick((t) => t + 1)} />
            ))}
          </div>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
