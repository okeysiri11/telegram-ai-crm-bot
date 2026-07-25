import {
  buildVerticalFederationDashboard,
  crossVerticalLinks,
  verticalRegistry,
} from "../dashboard/federationDashboard";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

export function VerticalFederationPage() {
  const dash = buildVerticalFederationDashboard();

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade">
        <header className="space-y-2">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Sprint 27.3 · Vertical Federation · v{dash.version}
          </p>
          <h1 className="eds-type-h1">{dash.title}</h1>
          <p className="eds-type-body text-[var(--eds-text-muted)]">
            Registry · Vertical Executive AI · Cross-Vertical Bus · Marketplace · Knowledge Federation
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge>Verticals {dash.kpi.verticalsTotal}</Badge>
            <Badge>Production {dash.kpi.production}</Badge>
            <Badge>Agents {dash.kpi.agentsTotal}</Badge>
            <Badge>AI {(dash.kpi.aiUtilizationAvg * 100).toFixed(0)}%</Badge>
            <Badge>{dash.executiveAiConnected ? "Executive AI Connected" : "Offline"}</Badge>
          </div>
        </header>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Federation KPI">
            <p className="eds-type-small">Avg KPI {dash.kpi.avgKpi}</p>
            <p className="eds-type-small">Agents {dash.kpi.agentsTotal}</p>
            <p className="eds-type-small">AI util {(dash.kpi.aiUtilizationAvg * 100).toFixed(0)}%</p>
          </Card>
          <Card title="Events">
            <ul className="space-y-1 eds-type-small">
              {dash.events.map((e) => (
                <li key={e.message}>
                  [{e.type}] {e.message}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Alerts">
            <ul className="space-y-1 eds-type-small">
              {dash.alerts.map((a) => (
                <li key={a.message}>
                  [{a.level}] {a.message}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Recommendations">
            <ul className="space-y-1 eds-type-small">
              {dash.recommendations.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </Card>
          <Card title="Cross-vertical links">
            <ul className="max-h-40 space-y-1 overflow-auto eds-type-small">
              {crossVerticalLinks.list().map((l) => (
                <li key={`${l.source}-${l.target}`}>
                  {l.source} → {l.target}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Vertical states">
            <ul className="max-h-40 space-y-1 overflow-auto eds-type-small">
              {dash.verticals.map((v) => (
                <li key={v.id}>
                  {v.name}: {v.status} · KPI {v.kpiScore} · agents {v.agents}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <Card title="Vertical Registry">
          <ul className="space-y-2 eds-type-small">
            {verticalRegistry.list().map((v) => (
              <li key={v.id} className="rounded-md border border-[var(--eds-border)] p-2">
                <div className="flex flex-wrap items-center gap-2">
                  <strong>{v.name}</strong>
                  <Badge>{v.status}</Badge>
                  <Badge>KPI {v.kpiScore}</Badge>
                </div>
                <p className="eds-type-caption mt-1">
                  owner {v.owner} · {v.aiDirector} · AI {(v.aiUtilization * 100).toFixed(0)}% · activity {v.activity}
                </p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
