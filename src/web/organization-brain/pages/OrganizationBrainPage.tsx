import { buildOrganizationDashboard, executiveBoard } from "../dashboard/organizationDashboard";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

export function OrganizationBrainPage() {
  const dash = buildOrganizationDashboard();

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade">
        <header className="space-y-2">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Sprint 27.2 · Organization Brain · v{dash.version}
          </p>
          <h1 className="eds-type-h1">{dash.title}</h1>
          <p className="eds-type-body text-[var(--eds-text-muted)]">
            Executive Board · Department AI · Decision Engine · Meetings · Org Knowledge
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge>State {dash.companyState}</Badge>
            <Badge>NPS {dash.kpi.nps}</Badge>
            <Badge>AI {(dash.kpi.aiUtilization * 100).toFixed(0)}%</Badge>
            <Badge>ARR +{(dash.kpi.arrGrowth * 100).toFixed(0)}%</Badge>
          </div>
        </header>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Company KPI">
            <p className="eds-type-small">Margin {(dash.kpi.margin * 100).toFixed(0)}%</p>
            <p className="eds-type-small">Employee load {(dash.employeeLoadAvg * 100).toFixed(0)}%</p>
            <p className="eds-type-small">AI load {(dash.aiLoadAvg * 100).toFixed(0)}%</p>
          </Card>
          <Card title="Financials">
            <p className="eds-type-small">Revenue MTD ${dash.financials.revenueMtd.toLocaleString()}</p>
            <p className="eds-type-small">Opex MTD ${dash.financials.opexMtd.toLocaleString()}</p>
            <p className="eds-type-small">Runway {dash.financials.cashRunwayMonths} mo</p>
          </Card>
          <Card title="Strategic goals">
            <ul className="space-y-1 eds-type-small">
              {dash.strategicGoals.map((g) => (
                <li key={g}>{g}</li>
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
          <Card title="Department efficiency">
            <ul className="max-h-40 space-y-1 overflow-auto eds-type-small">
              {dash.departments.map((d) => (
                <li key={d.id}>
                  {d.name}: {(d.efficiency * 100).toFixed(0)}% · KPI {d.kpiScore}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <Card title="AI Executive Board">
          <ul className="space-y-2 eds-type-small">
            {executiveBoard.list().map((m) => (
              <li key={m.agentId} className="rounded-md border border-[var(--eds-border)] p-2">
                <div className="flex flex-wrap items-center gap-2">
                  <strong>{m.name}</strong>
                  <Badge>{m.title}</Badge>
                  <Badge>{m.status}</Badge>
                </div>
                <p className="eds-type-caption mt-1">
                  {m.domain} · load {(m.load * 100).toFixed(0)}%
                </p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
