import { Link, useNavigate } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useLastModuleStore } from "@/modules/lastModuleStore";
import { openClientDemoWorkspace } from "@/multi-role/applyDemoSession";
import { useNotificationStore } from "@/notifications/notificationStore";
import { MobileActionButton } from "./MobileActionButton";
import { useMobileChromeStore } from "./mobileChromeStore";
import { MobileFavoritesRow } from "./MobileFavoritesRow";
import { MobileWorkspaceCards } from "./MobileWorkspaceHub";
import {
  demoWorkspaceAvailable,
  importantTodayFromLive,
  isClientDemoSession,
  isOperationalWorkspaceRoute,
  isOwnerSystemContext,
  MOBILE_EXTRA_ACTIONS,
  mobileHomeQuickActions,
  workspaceContextCopy,
  workspaceHomePath,
} from "./mobileWorkspace";

export function MobileHome({
  workspaceId,
  workspaceLabel,
  roleLabel,
  demo,
}: {
  workspaceId: string;
  workspaceLabel: string;
  roleLabel: string;
  demo?: boolean;
}) {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const email = useAuthStore((s) => s.user?.email);
  const home = workspaceHomePath(workspaceId);
  const context = workspaceContextCopy(workspaceId, workspaceLabel);
  const actions = mobileHomeQuickActions(workspaceId);
  const setMoreOpen = useMobileChromeStore((s) => s.setMoreOpen);
  const setDrawerOpen = useMobileChromeStore((s) => s.setDrawerOpen);
  const lastRoute = useLastModuleStore((s) => s.lastRoute);
  const notifications = useNotificationStore((s) => s.items);
  const unread = notifications.filter((i) => !i.read).length;
  const unreadTasks = notifications.filter((i) => !i.read && i.kind === "task").length;
  const unreadAlerts = notifications.filter((i) => !i.read && (i.kind === "alert" || i.kind === "toast")).length;
  const important = importantTodayFromLive({ unread, healthFailed: 0, unreadTasks, unreadAlerts });
  const continueHref = isOperationalWorkspaceRoute(lastRoute) ? lastRoute : null;
  const showDemo = demoWorkspaceAvailable();
  const demoDisabled = isClientDemoSession(email);
  const owner = isOwnerSystemContext(workspaceId) || context.systemOwner;
  const workspaceCta = owner ? "Открыть рабочее пространство" : `Перейти в ${context.title}`;

  return (
    <div className="ados-mobile-home" data-testid="mobile-home">
      {showDemo ? (
        <MobileActionButton
          testId="mobile-open-demo"
          variant="secondary"
          disabled={demoDisabled}
          disabledReason={demoDisabled ? "Вы уже в демо-пространстве" : undefined}
          onClick={async () => {
            const creds = openClientDemoWorkspace();
            try {
              await login(creds.email, creds.password, creds.tenantId);
            } catch {
              /* demo seed still applied */
            }
            navigate("/dashboard");
          }}
        >
          Открыть демо-пространство
        </MobileActionButton>
      ) : null}

      <Card>
        {demo ? (
          <div className="mb-2">
            <Badge tone="warning">DEMO</Badge>
          </div>
        ) : null}
        <p className="eds-type-caption text-[var(--eds-text-muted)]">{context.kicker}</p>
        <h1 className="text-2xl font-semibold" data-testid="mobile-home-workspace">
          {context.title}
        </h1>
        <p className="mt-1 eds-type-body">
          {context.roleKicker}: {owner ? "Владелец" : roleLabel}
        </p>
        {context.hint ? <p className="mt-1 eds-type-caption text-[var(--eds-text-muted)]">{context.hint}</p> : null}
        <div className="mt-3">
          <MobileActionButton testId="mobile-open-workspace" to={home} disabled={false}>
            {workspaceCta}
          </MobileActionButton>
        </div>
      </Card>

      {owner ? (
        <section data-testid="mobile-continue-work">
          <h2 className="mb-2 font-semibold">Продолжить работу</h2>
          {continueHref ? (
            <Link to={continueHref} className="ados-mobile-card block">
              Недавнее рабочее пространство
            </Link>
          ) : (
            <p className="eds-type-body text-[var(--eds-text-muted)]">Откройте рабочее пространство ниже.</p>
          )}
        </section>
      ) : null}

      <section data-testid="mobile-important-today">
        <h2 className="mb-2 font-semibold">Важное сегодня</h2>
        {important.length ? (
          <div className="space-y-2">
            {important.map((item) => (
              <Link key={item.id} to={item.href} className="ados-mobile-card block">
                {item.label}
              </Link>
            ))}
          </div>
        ) : (
          <p className="eds-type-body text-[var(--eds-text-muted)]">На сегодня критичных событий нет.</p>
        )}
      </section>

      {owner ? <MobileWorkspaceCards /> : null}

      <section>
        <h2 className="mb-2 font-semibold">Быстрые действия</h2>
        <div className="ados-mobile-qa">
          {actions.map((action) =>
            action.action === "more" ? (
              <button key={action.id} type="button" data-testid="mobile-open-more" onClick={() => setMoreOpen(true)}>
                {action.label}
              </button>
            ) : action.action === "panel" ? (
              <button
                key={action.id}
                type="button"
                data-testid="mobile-open-panel"
                aria-label="Открыть операционную панель"
                onClick={() => setDrawerOpen(true)}
              >
                {action.label}
              </button>
            ) : (
              <button
                key={action.id}
                type="button"
                data-testid={
                  action.id === "ai" ? "mobile-open-ai" : action.id === "settings" ? "mobile-open-settings" : undefined
                }
                onClick={() => navigate(action.href)}
              >
                {action.label}
              </button>
            ),
          )}
        </div>
        <div className="ados-mobile-extra">
          {MOBILE_EXTRA_ACTIONS.map((item) => (
            <Link key={item.id} to={item.href}>
              {item.label}
            </Link>
          ))}
        </div>
      </section>

      <MobileFavoritesRow />
    </div>
  );
}
