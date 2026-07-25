import { buildReleaseDashboard } from "../dashboard/releaseDashboard";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

export function ReleaseCandidatePage() {
  const dash = buildReleaseDashboard();

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade">
        <header className="space-y-2">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Sprint 26.8 · {dash.releaseCode} · v{dash.version}
          </p>
          <h1 className="eds-type-h1">{dash.title}</h1>
          <p className="eds-type-body text-[var(--eds-text-muted)]">
            Final integration gate for the AI Enterprise Platform — health, coverage, security and readiness.
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge>{dash.health}</Badge>
            <Badge>Readiness {dash.overallReadinessPct}%</Badge>
            <Badge>
              Modules {dash.integratedModules}/{dash.totalModules}
            </Badge>
          </div>
        </header>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Health">
            <p className="eds-type-h2">{dash.overallReadinessPct}%</p>
            <p className="eds-type-caption mt-1">Overall platform readiness</p>
            <p className="eds-type-small mt-2">Status: {dash.health}</p>
          </Card>
          <Card title="Coverage">
            <ul className="space-y-1 eds-type-small">
              {Object.entries(dash.coverage).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}%
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Status">
            <p className="eds-type-small">Applications: {dash.applicationCount}</p>
            <p className="eds-type-small">Platform packages: {dash.platformPackages}</p>
            <p className="eds-type-small">React routes: {dash.reactRoutes}</p>
            <p className="eds-type-small">
              Integration: {dash.integratedModules}/{dash.totalModules}
            </p>
          </Card>
          <Card title="Critical Issues">
            {dash.criticalIssues.length === 0 ? (
              <p className="eds-type-small text-[var(--eds-text-muted)]">None</p>
            ) : (
              <ul className="space-y-1 eds-type-small">
                {dash.criticalIssues.map((i) => (
                  <li key={i}>{i}</li>
                ))}
              </ul>
            )}
          </Card>
          <Card title="Warnings">
            <ul className="space-y-1 eds-type-small">
              {dash.warnings.map((w) => (
                <li key={w}>{w}</li>
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
        </div>
      </div>
    </WorkspaceLayout>
  );
}
