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
import { useViewModeStore, viewModeLabel } from "@/ux-revolution";
import { useI18n } from "@/i18n";
import { readGlobeFlySeed, GLOBEFLY_TENANT_ID } from "@/demo/globefly";

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
 * Sprint 41.1 — GlobeFly Client mode: business chrome only.
 */
export function BetaHomeDashboard() {
  const t = useI18n((s) => s.t);
  const locale = useI18n((s) => s.locale);
  const user = useAuthStore((s) => s.user);
  const first = loadFirstEntry();
  const orgId = useOrgSelector((s) => s.organizationId);
  const orgLabel =
    ORG_SELECTOR_OPTIONS.find((o) => o.id === orgId)?.label || first.companyName || "Demo Corp";
  const viewMode = useViewModeStore((s) => s.viewMode);
  const modeLabel = viewModeLabel(viewMode, locale === "en" ? "en" : "ru");
  const isClient = viewMode === "client" || viewMode === "manager";
  const gf = orgId === GLOBEFLY_TENANT_ID ? readGlobeFlySeed() : null;

  const clientLinks = [
    { id: "crm", title: "CRM", subtitle: "Лиды, клиенты и сделки", route: "/crm" },
    { id: "leads", title: "Лиды", subtitle: "Создать и квалифицировать", route: "/crm?view=leads" },
    { id: "docs", title: "Документы", subtitle: "Файлы компании", route: "/documents" },
    { id: "ai", title: "AI-ассистент", subtitle: "Вопросы и рекомендации", route: "/ai-agents" },
    { id: "reports", title: "Отчёты", subtitle: "Аналитика и графики", route: "/analytics" },
    { id: "tasks", title: "Задачи", subtitle: "Назначения и статусы", route: "/tasks" },
  ];

  return (
    <div className="space-y-4" data-testid="beta-home-dashboard">
      <div>
        <h1 className="eds-type-h1">
          {orgId === GLOBEFLY_TENANT_ID ? t("globefly.welcome") : "Добро пожаловать"}
        </h1>
        <p className="eds-type-helper">
          {user?.name || "Пользователь"} · {orgLabel} · {modeLabel}
        </p>
      </div>

      {gf ? (
        <div className="eds-grid eds-grid--dashboard">
          <Card title="Открытые лиды">
            <p className="eds-type-h2">{gf.dashboard.openLeads}</p>
          </Card>
          <Card title="Активные сделки">
            <p className="eds-type-h2">{gf.dashboard.activeDeals}</p>
          </Card>
          <Card title="Выручка (месяц)">
            <p className="eds-type-h2">{gf.dashboard.revenueMtd.toLocaleString("ru-RU")} ₽</p>
          </Card>
        </div>
      ) : null}

      {isClient ? (
        <>
          <div className="eds-grid eds-grid--dashboard">
            <LinkList title="Рабочие модули" items={clientLinks} />
            <LinkList
              title="Клиенты GlobeFly"
              items={(gf?.clients || []).map((c) => ({
                id: c.id,
                title: c.name,
                subtitle: c.email,
                route: "/crm?view=clients",
              }))}
            />
            <LinkList
              title="Документы"
              items={(gf?.documents || []).map((d) => ({
                id: d.id,
                title: d.name,
                subtitle: `${d.type} · ${d.sizeKb} КБ`,
                route: "/documents",
              }))}
            />
            <LinkList
              title="Подсказки AI"
              items={(gf?.aiPrompts || []).map((p, i) => ({
                id: `ai_${i}`,
                title: p,
                subtitle: "Открыть ассистента",
                route: "/ai-agents",
              }))}
            />
          </div>
          <QuickActionsPanel />
        </>
      ) : (
        <>
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
          </Card>
        </>
      )}
    </div>
  );
}
