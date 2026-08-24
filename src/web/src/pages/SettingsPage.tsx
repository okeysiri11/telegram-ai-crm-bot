import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, type ReactNode } from "react";
import { FullLayout } from "@/layouts/FullLayout";
import { Avatar, Badge, Button, Card, Select, Switch } from "@/ui";
import { useI18n, type Locale } from "@/i18n";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { InterfaceSettingsPanel } from "@/preferences/InterfaceSettingsPanel";
import { useThemeStore, type ThemeMode } from "@/theme/themeStore";
import { resetFirstEntry, isFirstEntryComplete } from "@/onboarding/firstEntryStore";
import { rememberModuleRoute } from "@/modules/lastModuleStore";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { webConfig } from "@/config/webConfig";
import { MobileRouteGate } from "@/shell/mobile/MobileRouteGate";
import { MobileSettingsPage } from "@/shell/mobile/MobileSettingsPage";

/**
 * Settings — единый раздел настроек (Epic 46.0).
 * Профиль · Организация · AI · Голос · Telegram · Интеграции · Безопасность · …
 */
export function SettingsPage() {
  const [params] = useSearchParams();
  const embed = params.get("embed") === "1";
  const tab = params.get("tab") || "general";
  const navigate = useNavigate();
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const prefs = usePreferencesStore();
  const setMode = useThemeStore((s) => s.setMode);
  const mode = useThemeStore((s) => s.mode);
  const firstEntryDone = isFirstEntryComplete();
  const user = useAuthStore((s) => s.user);
  const accessExpiresAt = useAuthStore((s) => s.accessExpiresAt);
  const authMode = useAuthStore((s) => s.authMode);
  const logout = useAuthStore((s) => s.logout);
  const ws = useWorkspaceStore((s) => s.workspace);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const activeWorkspaceId = useWorkspaceManager((s) => s.activeWorkspaceId);
  const setActiveWorkspace = useWorkspaceManager((s) => s.setActiveWorkspace);
  const tabs = useWorkspaceManager((s) => s.tabs);

  useEffect(() => {
    document.title = `${t("nav.settings")} · ADOS Enterprise`;
    rememberModuleRoute("/settings");
  }, [t]);

  const SETTINGS_TABS: { id: string; label: string }[] = [
    { id: "general", label: "Общие" },
    { id: "profile", label: "Профиль" },
    { id: "organization", label: "Организация" },
    { id: "interface", label: "Интерфейс" },
    { id: "ai", label: "AI" },
    { id: "voice", label: "Голос" },
    { id: "telegram", label: "Telegram" },
    { id: "integrations", label: "Интеграции" },
    { id: "security", label: "Безопасность" },
    { id: "notifications", label: "Уведомления" },
    { id: "models", label: "Модели" },
    { id: "memory", label: "Память" },
    { id: "automation", label: "Автоматизация" },
    { id: "license", label: "Лицензия" },
  ];

  function SectionCard({
    title,
    description,
    href,
    cta,
  }: {
    title: string;
    description: string;
    href: string;
    cta: string;
  }) {
    return (
      <Card title={title}>
        <p className="mb-3 text-sm text-[var(--ew-muted)]">{description}</p>
        <Button size="sm" onClick={() => navigate(href)}>
          {cta}
        </Button>
      </Card>
    );
  }

  const sectionPanels: Record<string, ReactNode> = {
    ai: (
      <SectionCard
        title="Настройки AI и режима"
        description="Human / AI / Voice, подтверждения, озвучивание, план выполнения."
        href="/settings/ai-mode"
        cta="Открыть настройки AI"
      />
    ),
    voice: (
      <SectionCard
        title="Голос"
        description="Голосовой режим, озвучивание ответов, push-to-talk."
        href="/settings/ai-mode"
        cta="Настроить голос"
      />
    ),
    telegram: (
      <SectionCard
        title="Telegram"
        description="Мобильная Enterprise CRM — уведомления и канал."
        href="/settings?tab=notifications"
        cta="К уведомлениям"
      />
    ),
    integrations: (
      <SectionCard
        title="Интеграции"
        description="Провайдеры, webhooks и внешние сервисы."
        href="/integrations"
        cta="Открыть интеграции"
      />
    ),
    security: (
      <SectionCard
        title="Безопасность"
        description="Роли, сессии, JWT, аудит."
        href="/identity/security"
        cta="Центр безопасности"
      />
    ),
    models: (
      <SectionCard
        title="Модели"
        description="Выбор и лимиты AI-моделей."
        href="/ai-command"
        cta="AI Command"
      />
    ),
    memory: (
      <SectionCard
        title="Память"
        description="Непрерывная память и рабочая область."
        href="/ai-workspace"
        cta="Моя рабочая область"
      />
    ),
    automation: (
      <SectionCard
        title="Автоматизация"
        description="Workflow, планировщик, Hercules."
        href="/workflows"
        cta="Открыть автоматизацию"
      />
    ),
    license: (
      <Card title="Лицензия">
        <p className="text-sm">
          ADOS Enterprise · версия {webConfig.version} · спринт {webConfig.sprint}
        </p>
      </Card>
    ),
    profile: (
      <Card title="Профиль">
        <div className="flex items-center gap-3">
          {user ? <Avatar name={user.name} /> : null}
          <div>
            <p className="font-medium">{user?.name || "—"}</p>
            <p className="eds-type-helper">{user?.email}</p>
          </div>
        </div>
        <div className="mt-3">
          <Link to="/identity/profile">
            <Button size="sm">Открыть профиль</Button>
          </Link>
        </div>
      </Card>
    ),
    organization: (
      <Card title="Организация">
        <Select value={ws.company} onChange={(e) => setWorkspace({ company: e.target.value })}>
          <option value="globefly">GlobeFly</option>
          <option value="demo-corp">demo-corp</option>
          <option value="acme-ltd">acme-ltd</option>
        </Select>
        <div className="mt-3">
          <Link to="/identity/organizations">
            <Button size="sm" variant="secondary">
              Организации
            </Button>
          </Link>
        </div>
      </Card>
    ),
    notifications: (
      <Card title="Уведомления">
        <Switch
          checked={prefs.notificationsEnabled}
          onChange={(v) => prefs.update({ notificationsEnabled: v })}
          label="Показывать уведомления"
        />
        <div className="mt-3">
          <Button size="sm" variant="secondary" onClick={() => navigate("/notifications")}>
            Центр уведомлений
          </Button>
        </div>
      </Card>
    ),
  };

  const body = (
    <>
      <h1 className="mb-2 text-2xl font-semibold">{t("nav.settings")}</h1>
      <p className="mb-4 text-sm text-[var(--ew-muted)]">Единый раздел настроек платформы</p>
      <div className="mb-4 flex flex-wrap gap-2" data-testid="settings-tabs">
        {SETTINGS_TABS.map((item) => (
          <Button
            key={item.id}
            size="sm"
            variant={tab === item.id ? "primary" : "secondary"}
            onClick={() => navigate(item.id === "general" ? "/settings" : `/settings?tab=${item.id}`)}
          >
            {item.label}
          </Button>
        ))}
      </div>

      {tab === "interface" ? (
        <InterfaceSettingsPanel />
      ) : sectionPanels[tab] ? (
        <div className="max-w-3xl">{sectionPanels[tab]}</div>
      ) : (
        <div className="grid max-w-5xl gap-4 lg:grid-cols-2">
          <Card title={t("nav.theme")}>
            <Select
              value={prefs.theme === "system" ? mode : prefs.theme}
              onChange={(e) => {
                const next = e.target.value as ThemeMode;
                prefs.update({ theme: next });
                setMode(next);
              }}
            >
              <option value="light">{t("iface.theme.light")}</option>
              <option value="dark">{t("iface.theme.dark")}</option>
              <option value="system">{t("iface.theme.system")}</option>
            </Select>
          </Card>

          <Card title={t("nav.language")}>
            <Select
              value={prefs.language}
              onChange={(e) => {
                const language = e.target.value as Locale;
                prefs.update({ language });
                setLocale(language);
              }}
            >
              <option value="ru">Русский</option>
              <option value="en">English</option>
              <option value="uk">Українська</option>
            </Select>
          </Card>

          <Card title={t("nav.workspace")}>
            <label className="eds-type-label mb-1 block">{t("iface.workspace.active")}</label>
            <Select value={activeWorkspaceId} onChange={(e) => setActiveWorkspace(e.target.value)}>
              <option value="ws_default">{t("iface.workspace.default")}</option>
              <option value="ws_ops">{t("iface.workspace.ops")}</option>
              <option value="ws_exec">{t("iface.workspace.exec")}</option>
            </Select>
            <p className="mt-2 eds-type-helper">
              {tabs.length} {t("iface.tabsRestore")}
            </p>
          </Card>

          <Card title={t("iface.session")}>
            <ul className="space-y-2 eds-type-small">
              <li>
                {t("iface.session.mode")}: <Badge>{authMode || "—"}</Badge>
              </li>
              <li>
                {t("auth.tenant")}: {user?.tenantId || "—"}
              </li>
              <li>
                {t("iface.session.expires")}: {accessExpiresAt || "—"}
              </li>
            </ul>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
              >
                {t("auth.logout")}
              </Button>
            </div>
          </Card>

          <Card title={t("iface.firstEntry")}>
            <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">
              {firstEntryDone ? t("iface.firstEntry.done") : t("iface.firstEntry.pending")}
            </p>
            <div className="flex flex-wrap gap-2">
              <Link to="/onboarding/first-entry">
                <Button size="sm" variant="secondary">
                  {t("iface.firstEntry.open")}
                </Button>
              </Link>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  resetFirstEntry();
                  navigate("/onboarding/first-entry");
                }}
              >
                {t("iface.firstEntry.reset")}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </>
  );

  if (embed) {
    return <div className="edt-embed-root p-4">{body}</div>;
  }

  return (
    <FullLayout>
      <MobileRouteGate mobile={tab === "general" ? <MobileSettingsPage /> : body} desktop={body} />
    </FullLayout>
  );
}
