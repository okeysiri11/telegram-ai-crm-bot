import { Link } from "react-router-dom";
import { useMemo } from "react";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Badge, Card } from "@/ui";
import { OWNER_RU_NAV, ROLE_SWITCHER_OPTIONS } from "@/navigation/enterpriseRuNav";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { OwnerAiDashboard } from "@/ai-runtime/OwnerAiDashboard";
import { OWNER_SUBSYSTEMS } from "@/platform-integration/ownerSubsystems";
import { deriveOwnerMetrics, deriveGodModeMetrics } from "@/enterprise-business";
import { RoleDashboardPolish } from "@/dashboard/RoleDashboardPolish";
import { ProductionOwnerStrip } from "@/ai-production-studio/ProductionOwnerStrip";
import { AgentOsMonitor } from "@/ai-runtime/AgentOsMonitor";
import type { AiTaskSecurityContext } from "@/ai-runtime/aiTaskSecurity";
import { MobileRouteGate } from "@/shell/mobile/MobileRouteGate";
import { MobilePlatformHome } from "@/shell/mobile/MobilePlatformHome";

/**
 * Sprint 30.2–31.1 — Owner Mode dashboard with live metrics + God Mode strip.
 */
export function OwnerDashboardPage() {
  const isOwner = useRoleSwitcher((s) => s.isOwnerView());
  const roleId = useRoleSwitcher((s) => s.activeRoleId);
  const roleLabel = ROLE_SWITCHER_OPTIONS.find((o) => o.id === roleId)?.label || "Владелец";
  const metrics = useMemo(() => deriveOwnerMetrics(), []);
  const god = useMemo(() => deriveGodModeMetrics(), []);
  const ctx = useMemo<AiTaskSecurityContext>(
    () => ({
      roles: ["owner", roleId],
      permissions: ["*", "ai_agents"],
      orgId: "org_owner",
      workspaceId: "ws_owner",
      actor: "owner",
    }),
    [roleId],
  );

  return (
    <DashboardLayout>
      <MobileRouteGate
        mobile={<MobilePlatformHome />}
        desktop={
      <div className="space-y-4 edm-page" data-testid="owner-dashboard">
        <div>
          <h1 className="eds-type-h1">Панель владельца</h1>
          <p className="eds-type-helper">
            Единый Dashboard · Workflow · Hercules · Студия AI · Память · {roleLabel}
            {!isOwner ? " · просмотр с переключённой ролью" : ""}
          </p>
        </div>

        <Card title="Единый Dashboard" status={<Badge tone="success">46.0</Badge>} data-testid="owner-unified-dashboard">
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { label: "Работающие Workflow", to: "/workflows" },
              { label: "Очередь Hercules", to: "/platform-builder/hercules" },
              { label: "Студия AI", to: "/ai-command" },
              { label: "Последние проекты", to: "/projects" },
              { label: "Последние документы", to: "/documents" },
              { label: "Последние генерации", to: "/ai-workspace" },
              { label: "Расход AI", to: "/workflows" },
              { label: "Уведомления", to: "/notifications" },
              { label: "Рекомендации AI", to: "/ai-command" },
              { label: "Быстрые действия", to: "/ai-command" },
              { label: "Настройки", to: "/settings" },
              { label: "Память", to: "/memory" },
            ].map((item) => (
              <li key={item.label}>
                <Link
                  to={item.to}
                  className="block rounded-md border border-[var(--ew-border)] px-3 py-2 eds-type-small hover:border-[var(--eds-primary)]"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-3 eds-type-helper">
            Каждое действие доступно вручную или через AI Command («Создай проект», «Сделай рекламу»).
          </p>
        </Card>

        <Card
          title="Owner God Mode"
          status={<Badge tone="success">live</Badge>}
          data-testid="owner-god-mode"
        >
          <div className="eds-grid eds-grid--dashboard">
            {god.map((m) => (
              <div
                key={m.id}
                className="rounded-md border border-[var(--ew-border)] px-3 py-2"
              >
                <p className="eds-type-caption">{m.title}</p>
                <Badge tone={m.tone || "default"}>{m.value}</Badge>
                <div className="mt-1">
                  <Link className="text-[var(--eds-primary)] eds-type-small" to={m.route}>
                    Открыть →
                  </Link>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            <Link className="text-[var(--eds-primary)] eds-type-small" to="/platform-builder/god-mode">
              Control Center →
            </Link>
            <Link className="text-[var(--eds-primary)] eds-type-small" to="/city">
              Город · God Mode →
            </Link>
            <Link className="text-[var(--eds-primary)] eds-type-small" to="/health">
              Здоровье →
            </Link>
          </div>
        </Card>

        <div className="eds-grid eds-grid--dashboard" id="health">
          {metrics.map((m) => (
            <Card key={m.id} title={m.title}>
              <Badge tone={m.tone || "default"}>{m.value}</Badge>
              <div className="mt-2">
                <Link className="text-[var(--eds-primary)] eds-type-small" to={m.route}>
                  Открыть →
                </Link>
              </div>
            </Card>
          ))}
        </div>

        <RoleDashboardPolish role="owner" />

        <ProductionOwnerStrip />

        <AgentOsMonitor compact />

        <Card title="Подсистемы платформы" status={<Badge tone="success">Owner</Badge>}>
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {OWNER_SUBSYSTEMS.map((s) => (
              <li key={s.id}>
                <Link
                  to={s.route}
                  className="block rounded-md border border-[var(--ew-border)] px-3 py-2 eds-type-small hover:border-[var(--eds-primary)]"
                >
                  <strong>{s.label}</strong>
                  <span className="block eds-type-helper">{s.description}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>

        {isOwner ? <OwnerAiDashboard ctx={ctx} /> : null}

        <Card title="Навигация владельца">
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {OWNER_RU_NAV.map((item) => (
              <li key={item.id}>
                <Link
                  to={item.route}
                  className="block rounded-md border border-[var(--ew-border)] px-3 py-2 eds-type-small hover:border-[var(--eds-primary)]"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>
        }
      />
    </DashboardLayout>
  );
}
