import { Link } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Badge, Card } from "@/ui";
import { DEALER_DASHBOARD_SECTIONS } from "@/dashboard/betaHomeCatalog";
import { useAuthStore } from "@/auth/authStore";
import { RoleDashboardPolish } from "@/dashboard/RoleDashboardPolish";

/**
 * Sprint 30.3 / 31.1 — Dealer role dashboard (Russian) with widgets.
 */
export function DealerDashboardPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <DashboardLayout>
      <div className="space-y-4 edm-page" data-testid="dealer-dashboard">
        <div>
          <h1 className="eds-type-h1">Кабинет дилера</h1>
          <p className="eds-type-helper">
            {user?.name || "Дилер"} · клиенты · заказы · продажи · CRM
          </p>
        </div>
        <RoleDashboardPolish role="dealer" />
        <div className="eds-grid eds-grid--dashboard">
          {DEALER_DASHBOARD_SECTIONS.map((s) => (
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
