import { Link } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Badge, Card } from "@/ui";
import { CLIENT_DASHBOARD_SECTIONS } from "@/dashboard/betaHomeCatalog";
import { useAuthStore } from "@/auth/authStore";
import { RoleDashboardPolish } from "@/dashboard/RoleDashboardPolish";

/**
 * Sprint 30.3 / 31.1 — Client role dashboard (Russian) with widgets.
 */
export function ClientDashboardPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <DashboardLayout>
      <div className="space-y-4 edm-page" data-testid="client-dashboard">
        <div>
          <h1 className="eds-type-h1">Кабинет клиента</h1>
          <p className="eds-type-helper">
            {user?.name || "Клиент"} · заявки · проекты · документы
          </p>
        </div>
        <RoleDashboardPolish role="client" />
        <div className="eds-grid eds-grid--dashboard">
          {CLIENT_DASHBOARD_SECTIONS.map((s) => (
            <Card key={s.id} title={s.title}>
              <p className="eds-type-helper mb-2">{s.hint}</p>
              <Badge tone="success">live</Badge>
              <div className="mt-2">
                <Link className="text-[var(--eds-primary)] eds-type-small" to={s.route}>
                  Открыть →
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
