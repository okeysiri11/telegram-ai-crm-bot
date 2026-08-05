/**
 * Sprint 31.0 / 31.1 — Manager & Employee role dashboards (Russian) with widgets.
 */

import { Link } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Badge, Card } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { RoleDashboardPolish } from "@/dashboard/RoleDashboardPolish";

const MANAGER_SECTIONS = [
  { id: "team", title: "Команда", hint: "Пользователи и роли", route: "/identity/users" },
  { id: "projects", title: "Проекты", hint: "Канбан и задачи", route: "/projects" },
  { id: "crm", title: "CRM", hint: "Клиенты и сделки", route: "/crm" },
  { id: "tasks", title: "Задачи", hint: "Операционный бэклог", route: "/tasks" },
  { id: "calendar", title: "Календарь", hint: "Встречи недели", route: "/calendar" },
  { id: "analytics", title: "Аналитика", hint: "KPI команды", route: "/analytics" },
  { id: "notifications", title: "Уведомления", hint: "Входящие", route: "/notifications" },
  { id: "ai", title: "AI-агенты", hint: "Помощники отдела", route: "/ai-agents" },
] as const;

const EMPLOYEE_SECTIONS = [
  { id: "tasks", title: "Мои задачи", hint: "Текущий бэклог", route: "/tasks" },
  { id: "calendar", title: "Календарь", hint: "Расписание", route: "/calendar" },
  { id: "documents", title: "Документы", hint: "Drive", route: "/documents" },
  { id: "knowledge", title: "Знания", hint: "База знаний", route: "/knowledge" },
  { id: "notifications", title: "Уведомления", hint: "Входящие", route: "/notifications" },
  { id: "crm", title: "CRM", hint: "Клиенты (если доступно)", route: "/crm" },
  { id: "profile", title: "Профиль", hint: "Личные данные", route: "/identity/profile" },
  { id: "settings", title: "Настройки", hint: "Предпочтения", route: "/settings" },
] as const;

function RoleDash({
  title,
  subtitle,
  sections,
  testId,
  role,
}: {
  title: string;
  subtitle: string;
  sections: readonly { id: string; title: string; hint: string; route: string }[];
  testId: string;
  role: "manager" | "employee";
}) {
  const user = useAuthStore((s) => s.user);
  return (
    <DashboardLayout>
      <div className="space-y-4 edm-page" data-testid={testId}>
        <div>
          <h1 className="eds-type-h1">{title}</h1>
          <p className="eds-type-helper">
            {user?.name || subtitle} · Closed Beta
          </p>
        </div>
        <RoleDashboardPolish role={role} />
        <div className="eds-grid eds-grid--dashboard">
          {sections.map((s) => (
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

export function ManagerDashboardPage() {
  return (
    <RoleDash
      title="Панель менеджера"
      subtitle="Менеджер"
      sections={MANAGER_SECTIONS}
      testId="manager-dashboard"
      role="manager"
    />
  );
}

export function EmployeeDashboardPage() {
  return (
    <RoleDash
      title="Панель сотрудника"
      subtitle="Сотрудник"
      sections={EMPLOYEE_SECTIONS}
      testId="employee-dashboard"
      role="employee"
    />
  );
}
