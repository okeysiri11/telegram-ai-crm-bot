import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Card, Charts, NotificationsPanel, Badge } from "@/ui";
import { useI18n } from "@/i18n";
import { useNavStore } from "@/navigation/navStore";

export function DashboardPage() {
  const t = useI18n((s) => s.t);
  const favorites = useNavStore((s) => s.favorites);

  return (
    <WorkspaceLayout>
      <div className="mb-4">
        <h1 className="text-2xl font-semibold tracking-tight">{t("nav.dashboard")}</h1>
        <p className="text-sm text-[var(--ew-muted)]">Enterprise Web Foundation · ready for business modules</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card title={t("dash.ai")}>
          <p className="text-sm">Ask the AI Orchestrator about workflows, risks, and opportunities.</p>
        </Card>
        <Card title={t("dash.tasks")}>
          <ul className="space-y-1 text-sm">
            <li>Approve invoice #1042</li>
            <li>Review migration checklist</li>
            <li>Confirm AI recommendation</li>
          </ul>
        </Card>
        <Card title={t("dash.calendar")}>
          <p className="text-sm">Today · 3 meetings · 1 release window</p>
        </Card>
        <Card title={t("dash.notifications")}>
          <NotificationsPanel />
        </Card>
        <Card title={t("dash.kpis")}>
          <Charts labels={["Mon", "Tue", "Wed", "Thu", "Fri"]} values={[62, 71, 68, 80, 77]} />
        </Card>
        <Card title={t("dash.activity")}>
          <ul className="space-y-1 text-sm text-[var(--ew-muted)]">
            <li>Workflow executed · billing</li>
            <li>Security gate passed</li>
            <li>Tenant synced · demo-corp</li>
          </ul>
        </Card>
        <Card title={t("dash.favorites")}>
          <div className="flex flex-wrap gap-2">
            {favorites.map((f) => (
              <Badge key={f}>{f}</Badge>
            ))}
          </div>
        </Card>
        <Card title={t("dash.health")}>
          <p className="text-sm"><Badge tone="success">healthy</Badge> Hub · Orchestrator · Event Bus</p>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
