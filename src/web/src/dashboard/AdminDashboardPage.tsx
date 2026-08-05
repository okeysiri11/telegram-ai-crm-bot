/**
 * Sprint 30.7 / 31.1 — Admin dashboard (Russian) with live widgets.
 */

import { Link } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Badge, Card } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { RoleDashboardPolish } from "@/dashboard/RoleDashboardPolish";

const ADMIN_SECTIONS = [
  { id: "users", title: "Пользователи", hint: "Управление учётными записями", route: "/identity/users" },
  { id: "roles", title: "Роли", hint: "Роли и права доступа", route: "/identity/roles" },
  { id: "orgs", title: "Организации", hint: "Компании и тенанты", route: "/identity/organizations" },
  { id: "security", title: "Безопасность", hint: "Сессии · MFA · аудит", route: "/identity/security" },
  { id: "settings", title: "Настройки", hint: "Конфигурация платформы", route: "/settings" },
  { id: "health", title: "Здоровье", hint: "CPU · API · Runtime", route: "/health" },
  { id: "runtime", title: "AI Runtime", hint: "Очередь и оркестрация", route: "/platform-builder/runtime" },
  { id: "governance", title: "Аудит", hint: "Governance и политики", route: "/platform-builder/governance" },
  { id: "city", title: "Город", hint: "Enterprise City", route: "/city" },
  { id: "logs", title: "Журналы", hint: "Command Runtime", route: "/command-runtime" },
] as const;

export function AdminDashboardPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <DashboardLayout>
      <div className="space-y-4 edm-page" data-testid="admin-dashboard">
        <div>
          <h1 className="eds-type-h1">Панель администратора</h1>
          <p className="eds-type-helper">
            {user?.name || "Администратор"} · пользователи · безопасность · настройки
          </p>
        </div>
        <RoleDashboardPolish role="admin" />
        <div className="eds-grid eds-grid--dashboard">
          {ADMIN_SECTIONS.map((s) => (
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
