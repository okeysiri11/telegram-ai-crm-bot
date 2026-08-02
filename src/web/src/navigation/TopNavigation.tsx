import { Link, useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/auth/authStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { Avatar, Badge, Button, Input, Select } from "@/ui";
import { Breadcrumbs } from "./Breadcrumbs";
import { useThemeStore, type ThemeMode } from "@/theme/themeStore";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { navigationHistory } from "../../navigation/managers/navigationHistory";
import { useState } from "react";
import { telemetry } from "@/integrations/telemetry";
import { useShellLayoutStore } from "@/shell/enterprise";
import { useRoleSwitcher } from "./roleSwitcherStore";
import { useOrgSelector } from "./orgSelectorStore";
import { ORG_SELECTOR_OPTIONS, ROLE_SWITCHER_OPTIONS } from "./enterpriseRuNav";
import type { Locale } from "@/i18n";
import { SimpleProModeToggle, RoleWorkspaceSelector } from "@/ux-revolution";

function nextTheme(mode: ThemeMode): ThemeMode {
  if (mode === "light") return "dark";
  if (mode === "dark") return "system";
  return "light";
}

function themeLabelRu(mode: ThemeMode): string {
  if (mode === "system") return "Авто";
  if (mode === "dark") return "Тёмная";
  if (mode === "corporate") return "Корпоративная";
  return "Светлая";
}

/**
 * Sprint 30.2 — Russian top bar: search, org, language, role, notifications, AI, profile.
 */
export function TopNavigation({
  onMenuToggle,
}: {
  onMenuToggle?: () => void;
} = {}) {
  const t = useI18n((s) => s.t);
  const locale = useI18n((s) => s.locale);
  const setLocale = useI18n((s) => s.setLocale);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const count = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const mode = useThemeStore((s) => s.mode);
  const setMode = useThemeStore((s) => s.setMode);
  const { openPalette } = useNavigationUi();
  const toggleDock = useShellLayoutStore((s) => s.toggleDock);
  const leftOpen = useShellLayoutStore((s) => s.docks.left.open);
  const bottomOpen = useShellLayoutStore((s) => s.docks.bottom.open);
  const [q, setQ] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const setRole = useRoleSwitcher((s) => s.setRole);
  const organizationId = useOrgSelector((s) => s.organizationId);
  const setOrganization = useOrgSelector((s) => s.setOrganization);

  function runSearch() {
    const query = q.trim();
    if (!query) {
      openPalette();
      return;
    }
    const hit = searchProvider.search(query)[0];
    if (hit) {
      navigationHistory.push({ kind: "search", label: query, path: hit.path });
      void telemetry.userActivity(`search:${hit.path}`);
      navigate(hit.path);
      setQ("");
      return;
    }
    void telemetry.userActivity("search_workspace");
    navigate(`/search?q=${encodeURIComponent(query)}`);
    setQ("");
  }

  return (
    <header className="ews-header ews-glass border-b border-[var(--ew-border)]">
      <div className="flex flex-wrap items-center gap-2 px-4 py-3">
        {onMenuToggle ? (
          <Button
            size="sm"
            variant="secondary"
            className="md:hidden eds-anim-micro"
            onClick={onMenuToggle}
            aria-label={t("nav.openMenu")}
          >
            {t("nav.menu")}
          </Button>
        ) : null}

        <Link to="/dashboard" className="ews-logo" aria-label={t("nav.homeAria")}>
          <span className="ews-logo-mark">AE</span>
          <span className="ews-logo-text">
            ADOS <span>{t("nav.enterprise")}</span>
          </span>
        </Link>

        <SimpleProModeToggle className="hidden sm:inline-flex" />
        <RoleWorkspaceSelector />

        <div className="min-w-40 flex-1">
          <Input
            placeholder={t("common.searchPlaceholder")}
            aria-label={t("common.search")}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onFocus={openPalette}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                runSearch();
              }
            }}
          />
        </div>

        <label className="hidden items-center gap-1 eds-type-caption lg:inline-flex">
          <span className="text-[var(--eds-text-muted)]">{t("org.switcher")}</span>
          <Select
            className="eds-focus-ring max-w-[9rem]"
            value={organizationId}
            onChange={(e) => {
              setOrganization(e.target.value);
              void telemetry.userActivity(`org:${e.target.value}`);
            }}
            aria-label={t("org.switcher")}
          >
            {ORG_SELECTOR_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </Select>
        </label>

        <label className="hidden items-center gap-1 eds-type-caption md:inline-flex">
          <span className="text-[var(--eds-text-muted)]">{t("nav.language")}</span>
          <Select
            className="eds-focus-ring max-w-[7rem]"
            value={locale}
            onChange={(e) => setLocale(e.target.value as Locale)}
            aria-label={t("nav.language")}
          >
            <option value="ru">Русский</option>
            <option value="en">English</option>
            <option value="uk">Українська</option>
          </Select>
        </label>

        <label className="hidden items-center gap-1 eds-type-caption xl:inline-flex">
          <span className="text-[var(--eds-text-muted)]">{t("role.switcher")}</span>
          <Select
            className="eds-focus-ring max-w-[9rem]"
            value={activeRoleId}
            onChange={(e) => {
              setRole(e.target.value);
              void telemetry.userActivity(`role_switch:${e.target.value}`);
            }}
            aria-label={t("role.switcher")}
          >
            {ROLE_SWITCHER_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </Select>
        </label>

        <Button
          size="sm"
          variant="secondary"
          className="eds-anim-micro"
          onClick={() => {
            openPalette();
            void telemetry.userActivity("open_palette");
          }}
        >
          {t("nav.commands")}
        </Button>

        <Button
          size="sm"
          variant="secondary"
          className="eds-anim-micro"
          onClick={() => {
            void telemetry.userActivity("open_search_workspace");
            navigate("/search");
          }}
        >
          {t("common.search")}
        </Button>

        <Button
          size="sm"
          variant="secondary"
          className="eds-anim-micro"
          onClick={() => {
            void telemetry.userActivity("open_ai_assistant");
            navigate("/platform-builder/concierge");
          }}
          aria-label={t("nav.aiAssistant")}
        >
          {t("nav.aiAssistant")}
        </Button>

        <span className="ews-ai-status" title={t("nav.aiStatus")}>
          <span className="ews-dot ews-dot--ok" aria-hidden />
          {t("nav.aiOnline")}
        </span>

        <Button
          size="sm"
          variant="secondary"
          className="eds-anim-micro"
          onClick={() => {
            void telemetry.userActivity("open_notifications");
            navigate("/notifications");
          }}
          aria-label={t("nav.notifications")}
        >
          {t("nav.notifications")} <Badge tone="warning">{count}</Badge>
        </Button>

        <Button
          size="sm"
          variant={leftOpen ? "primary" : "secondary"}
          className="eds-anim-micro hidden lg:inline-flex"
          onClick={() => toggleDock("left")}
          aria-pressed={leftOpen}
          aria-label={t("nav.leftDock")}
        >
          {t("nav.leftDock")}
        </Button>
        <Button
          size="sm"
          variant={bottomOpen ? "primary" : "secondary"}
          className="eds-anim-micro hidden lg:inline-flex"
          onClick={() => toggleDock("bottom")}
          aria-pressed={bottomOpen}
          aria-label={t("nav.health")}
        >
          {t("nav.health")}
        </Button>

        <div className="relative">
          {user ? (
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border border-[var(--ew-border)] px-2 py-1 text-left eds-anim-micro"
              onClick={() => setUserMenuOpen((v) => !v)}
              title={user.email}
              aria-expanded={userMenuOpen}
              aria-haspopup="menu"
            >
              <Avatar name={user.name} />
              <span className="hidden max-w-[8rem] truncate text-xs font-medium lg:inline">
                {user.name}
              </span>
            </button>
          ) : (
            <Button size="sm" variant="secondary" onClick={() => navigate("/login")}>
              {t("auth.login")}
            </Button>
          )}
          {userMenuOpen && user ? (
            <div className="ews-user-menu ews-glass" role="menu">
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setUserMenuOpen(false);
                  navigate("/identity/profile");
                }}
              >
                {t("nav.profile")}
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setUserMenuOpen(false);
                  navigate("/identity/security");
                }}
              >
                {t("nav.security")}
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setUserMenuOpen(false);
                  navigate("/owner");
                }}
              >
                {t("nav.ownerDashboard")}
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setUserMenuOpen(false);
                  navigate("/settings");
                }}
              >
                {t("nav.settings")}
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setUserMenuOpen(false);
                  navigate("/auth/logout");
                }}
              >
                {t("auth.logout")}
              </button>
            </div>
          ) : null}
        </div>

        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            const next = nextTheme(mode);
            setMode(next);
            void telemetry.userActivity(`theme:${next}`);
          }}
          aria-label={t("nav.theme")}
        >
          {t("nav.theme")} · {themeLabelRu(mode)}
        </Button>
      </div>
      <div className="px-4 pb-3">
        <Breadcrumbs />
      </div>
    </header>
  );
}
