import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { QuickActionsPanel } from "@/workspace-engine/QuickActionsPanel";
import {
  BETA_AI_AGENTS,
  BETA_PRODUCTION_STUDIOS,
  BETA_RECENT_DOCUMENTS,
  BETA_RECENT_EVENTS,
  BETA_RECENT_PROJECTS,
  COMING_SOON_RU,
} from "./betaHomeCatalog";
import { useAuthStore } from "@/auth/authStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { ORG_SELECTOR_OPTIONS } from "@/navigation/enterpriseRuNav";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { ROLE_SWITCHER_OPTIONS } from "@/navigation/enterpriseRuNav";

function LinkList({
  title,
  items,
}: {
  title: string;
  items: { id: string; title: string; subtitle: string; route: string }[];
}) {
  return (
    <Card title={title}>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <Link
              to={item.route}
              className="block rounded-md border border-[var(--ew-border)] px-3 py-2 hover:border-[var(--eds-primary)]"
            >
              <span className="font-medium eds-type-small">{item.title}</span>
              <span className="block eds-type-helper">{item.subtitle}</span>
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}

/**
 * Sprint 30.3 — first visually usable Enterprise Home (Russian).
 */
export function BetaHomeDashboard() {
  const user = useAuthStore((s) => s.user);
  const first = loadFirstEntry();
  const orgId = useOrgSelector((s) => s.organizationId);
  const orgLabel =
    ORG_SELECTOR_OPTIONS.find((o) => o.id === orgId)?.label || first.companyName || "Demo Corp";
  const roleId = useRoleSwitcher((s) => s.activeRoleId);
  const roleLabel =
    ROLE_SWITCHER_OPTIONS.find((o) => o.id === roleId)?.label || "Сотрудник";

  return (
    <div className="space-y-4">
      <div>
        <h1 className="eds-type-h1">Добро пожаловать</h1>
        <p className="eds-type-helper">
          {user?.name || "Пользователь"} · {orgLabel} · {roleLabel} · Beta
        </p>
      </div>

      <div className="eds-grid eds-grid--dashboard">
        <LinkList title="Последние проекты" items={BETA_RECENT_PROJECTS} />
        <LinkList title="Последние документы" items={BETA_RECENT_DOCUMENTS} />
        <LinkList title="AI-Агенты" items={BETA_AI_AGENTS} />
        <LinkList title="Последние события" items={BETA_RECENT_EVENTS} />
      </div>

      <QuickActionsPanel />

      <Card title="Продакшн-студия">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {BETA_PRODUCTION_STUDIOS.map((s) => (
            <Link
              key={s.id}
              to={s.available ? `/production-studio?studio=${s.id}` : "/production-studio"}
              className="rounded-md border border-[var(--ew-border)] px-3 py-2"
            >
              <span className="font-medium eds-type-small">{s.label}</span>
              {!s.available ? (
                <Badge tone="warning">{COMING_SOON_RU}</Badge>
              ) : (
                <span className="block eds-type-helper">Открыть</span>
              )}
            </Link>
          ))}
        </div>
      </Card>

      <Card title="Город предприятия">
        <p className="eds-type-helper mb-2">
          Интерактивный город: районы, здания и переход в рабочие модули.
        </p>
        <Link className="text-[var(--eds-primary)] eds-type-small" to="/enterprise-city">
          Открыть Enterprise City →
        </Link>
        {" · "}
        <Link className="text-[var(--eds-primary)] eds-type-small" to="/city">
          /city →
        </Link>
        {" · "}
        <Link className="text-[var(--eds-primary)] eds-type-small" to="/city-visualization">
          Среда визуализации →
        </Link>
      </Card>
    </div>
  );
}
