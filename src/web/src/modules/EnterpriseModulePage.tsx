import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { Badge, Button, Card, Skeleton } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { ShellIcon } from "@/shell/enterprise/ShellIcons";
import type { ShellIconId } from "@/shell/enterprise/enterpriseNav";
import type { EnterpriseModuleDef } from "./moduleCatalog";
import { rememberModuleRoute } from "./lastModuleStore";
import { telemetry } from "@/integrations/telemetry";
import { ModuleSection, WorkspaceErrorState } from "@/workspace-engine/LoadingStates";
import { QuickActionsPanel } from "@/workspace-engine/QuickActionsPanel";
import { listActivity } from "@/workspace-engine/activityJournal";
import { logActivity } from "@/workspace-engine/activityJournal";
import { useWorkspaceNavigation } from "@/workspace-engine/useWorkspaceTabs";

const readinessTone: Record<EnterpriseModuleDef["readiness"], "success" | "warning" | "default"> = {
  ga: "success",
  beta: "warning",
  preview: "default",
  coming_soon: "warning",
};

/**
 * Sprint 27.2/27.3 — Module Framework:
 * Overview · Statistics · Recent Activity · Quick Actions · Status · Configuration
 */
export function EnterpriseModulePage({ module }: { module: EnterpriseModuleDef }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { open } = useWorkspaceNavigation();
  const comingSoon = module.readiness === "coming_soon";
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const action = params.get("action");

  useEffect(() => {
    document.title = `${module.label} · ADOS Enterprise`;
    rememberModuleRoute(module.route);
    logActivity({ kind: "navigate", title: `Module ${module.label}`, detail: module.route });
    setLoading(true);
    setError(null);
    const t = window.setTimeout(() => setLoading(false), 180);
    return () => window.clearTimeout(t);
  }, [module.label, module.route]);

  useEffect(() => {
    if (!action) return;
    logActivity({ kind: "create", title: `${module.label}: ${action}`, detail: module.route });
  }, [action, module.label, module.route]);

  const journal = listActivity(8).filter(
    (a) => a.detail.includes(module.route) || a.title.includes(module.label),
  );

  if (error) {
    return (
      <WorkspaceLayout>
        <WorkspaceErrorState title={`${module.label}: ошибка`} detail={error} onRetry={() => setError(null)} />
      </WorkspaceLayout>
    );
  }

  return (
    <WorkspaceLayout>
      <div className="ews-module-page edm-page">
        <header className="ews-module-hero ews-glass">
          <div className="flex flex-wrap items-start gap-4">
            <span className="ews-module-icon" aria-hidden>
              <ShellIcon id={module.icon as ShellIconId} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="eds-type-section">Обзор</p>
              <h1 className="eds-type-title text-2xl lg:text-3xl">{module.label}</h1>
              <p className="mt-2 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">{module.description}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge tone={readinessTone[module.readiness]}>{module.statusLabel}</Badge>
                <Badge>{module.readiness.replace("_", " ")}</Badge>
                <Badge tone="success">Готовность {module.readinessPct}%</Badge>
                {action ? <Badge tone="warning">Действие: {action}</Badge> : null}
              </div>
            </div>
            {module.deepLink ? (
              <Button
                onClick={() => {
                  void telemetry.userActivity(`module_deep:${module.id}`);
                  open(module.deepLink!);
                }}
              >
                Открыть рабочую поверхность
              </Button>
            ) : null}
          </div>
          <div className="ews-readiness-bar" aria-hidden>
            <span style={{ width: `${module.readinessPct}%` }} />
          </div>
        </header>

        {loading ? (
          <div className="mt-4">
            <Skeleton rows={4} height="1.1rem" />
          </div>
        ) : null}

        {comingSoon ? (
          <section className="ews-coming-soon ews-glass mt-4" aria-label="Скоро">
            <h2 className="eds-type-title">Скоро</h2>
            <p className="mt-2 max-w-2xl eds-type-body text-[var(--eds-text-muted)]">
              {module.label} на дорожной карте платформы. Используйте быстрые действия ниже.
            </p>
          </section>
        ) : null}

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <ModuleSection title="Статистика">
            <Card title="Метрики модуля">
              <dl className="ews-module-stats">
                <div>
                  <dt>Готовность</dt>
                  <dd>{module.readinessPct}%</dd>
                </div>
                <div>
                  <dt>Статус</dt>
                  <dd>{module.statusLabel}</dd>
                </div>
                <div>
                  <dt>Действия</dt>
                  <dd>{module.quickActions.length}</dd>
                </div>
                <div>
                  <dt>Дорожная карта</dt>
                  <dd>{module.roadmap.length}</dd>
                </div>
              </dl>
            </Card>
          </ModuleSection>

          <ModuleSection title="Статус">
            <Card title="Операционный статус">
              <ul className="space-y-2 eds-type-small">
                <li className="flex items-center gap-2">
                  <span className="ews-dot ews-dot--ok" aria-hidden /> Хаб активен
                </li>
                <li className="flex items-center gap-2">
                  <span className={`ews-dot ews-dot--${comingSoon ? "warn" : "ok"}`} aria-hidden />
                  {comingSoon ? "Скоро / превью" : "Интерактивный workspace готов"}
                </li>
                <li className="flex items-center gap-2">
                  <span className="ews-dot ews-dot--info" aria-hidden /> Вкладки сессии восстанавливаются
                </li>
              </ul>
            </Card>
          </ModuleSection>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <ModuleSection title="Недавняя активность">
            <Card title="Активность модуля">
              <ul className="space-y-2 eds-type-small">
                {(journal.length ? journal : module.recentActions.map((t, i) => ({
                  id: `seed_${i}`,
                  title: t,
                  detail: module.route,
                  at: new Date().toISOString(),
                  kind: "navigate" as const,
                }))).map((a) => (
                  <li key={a.id} className="flex gap-2">
                    <span className="ews-dot ews-dot--info mt-1.5" aria-hidden />
                    <span>
                      <span className="font-medium">{a.title}</span>
                      <span className="mt-0.5 block text-[var(--eds-text-muted)]">{a.detail}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          </ModuleSection>

          <ModuleSection title="Конфигурация">
            <Card title="Ссылки модуля">
              <ul className="space-y-2 eds-type-small">
                <li>
                  Маршрут: <code>{module.route}</code>
                </li>
                {module.deepLink ? (
                  <li>
                    Deep link:{" "}
                    <Link className="underline" to={module.deepLink}>
                      {module.deepLink}
                    </Link>
                  </li>
                ) : null}
                <li>
                  <Button size="sm" variant="secondary" onClick={() => navigate("/settings")}>
                    Открыть настройки
                  </Button>
                </li>
                <li>
                  <Button size="sm" variant="ghost" onClick={() => setError("Симуляция ошибки модуля для Retry UX")}>
                    Симулировать ошибку
                  </Button>
                </li>
              </ul>
            </Card>
          </ModuleSection>
        </div>

        <div className="mt-4">
          <ModuleSection title="Быстрые действия">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mb-3">
              {module.quickActions.map((qa) => (
                <button
                  key={qa.id}
                  type="button"
                  className="cc-action text-left"
                  onClick={() => {
                    void telemetry.userActivity(`module_qa:${module.id}:${qa.id}`);
                    open(qa.route);
                  }}
                >
                  <span className="font-medium">{qa.label}</span>
                  <span className="eds-type-helper">{qa.route}</span>
                </button>
              ))}
            </div>
            <QuickActionsPanel compact />
          </ModuleSection>
        </div>

        <div className="mt-4">
          <ModuleSection title="План развития">
            <Card title="Дорожная карта">
              <ol className="list-decimal space-y-2 pl-4 eds-type-small">
                {module.roadmap.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ol>
            </Card>
          </ModuleSection>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
