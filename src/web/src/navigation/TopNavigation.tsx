/**
 * Sprint 42.0 / 42.2 / 42.9 — adaptive enterprise header + Owner Identity.
 */

import { Link, useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/auth/authStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { Avatar, Badge, Button } from "@/ui";
import { Breadcrumbs } from "./Breadcrumbs";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { useEffect, useRef, useState } from "react";
import { telemetry } from "@/integrations/telemetry";
import { ModuleHelpIcon } from "@/help/ModuleHelpIcon";
import { useViewModeStore } from "@/ux-revolution";
import { cn } from "@/utils/cn";
import { DevRoleSwitcher } from "@/multi-role/DevRoleSwitcher";
import { useAdaptiveShellStore } from "@/shell/enterprise/adaptiveShellStore";
import {
  OwnerIdentityStrip,
  ContextualAiChat,
  QuickCreatePanel,
} from "@/owner-experience";
import { ModeIndicator, ModeSwitch } from "@/platform-modes";
import { UnifiedIntentBar } from "@/workspace-chrome/unified-intent";

export function TopNavigation({
  onMenuToggle,
}: {
  onMenuToggle?: () => void;
} = {}) {
  const t = useI18n((s) => s.t);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const count = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const { openPalette } = useNavigationUi();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [menuPos, setMenuPos] = useState<{ top: number; right: number }>({ top: 56, right: 12 });
  const [aiOpen, setAiOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const avatarRef = useRef<HTMLButtonElement | null>(null);
  const headerCollapsed = useAdaptiveShellStore((s) => s.headerCollapsed);
  const toggleHeader = useAdaptiveShellStore((s) => s.toggleHeader);
  const activityMode = useAdaptiveShellStore((s) => s.activityMode);
  const setActivityMode = useAdaptiveShellStore((s) => s.setActivityMode);
  const focusMode = useAdaptiveShellStore((s) => s.focusMode);
  const toggleFocusMode = useAdaptiveShellStore((s) => s.toggleFocusMode);
  const viewMode = useViewModeStore((s) => s.viewMode);
  const isClient = viewMode === "client" || viewMode === "manager";
  const collapsed = headerCollapsed || focusMode;

  useEffect(() => {
    if (!userMenuOpen || !avatarRef.current) return;
    const rect = avatarRef.current.getBoundingClientRect();
    setMenuPos({
      top: rect.bottom + 8,
      right: Math.max(12, window.innerWidth - rect.right),
    });
  }, [userMenuOpen]);

  function toggleActivity() {
    if (activityMode === "hidden") setActivityMode("expanded");
    else if (activityMode === "expanded") setActivityMode("compact");
    else setActivityMode("hidden");
  }

  return (
    <>
      <header
        className={cn(
          "ews-header ews-glass border-b border-[var(--ew-border)] ews-header--anim",
          collapsed && "ews-header--collapsed",
          focusMode && "ews-header--focus",
        )}
        data-collapsed={collapsed ? "1" : "0"}
        data-testid="enterprise-toolbar"
      >
        {collapsed ? (
          <div className="ews-header-slim flex items-center gap-2 px-3">
            <Link to="/dashboard" className="ews-logo ews-logo--slim" aria-label={t("nav.homeAria")}>
              <span className="ews-logo-mark">AE</span>
              <span className="ews-logo-text">ADOS Enterprise</span>
            </Link>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => toggleHeader()}
              aria-label={t("toolbar.expand")}
              data-testid="toolbar-collapse"
              title={t("toolbar.expand")}
            >
              ▾
            </Button>
            {focusMode ? (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => toggleFocusMode()}
                data-testid="focus-mode"
              >
                {t("shell.focus.exit")}
              </Button>
            ) : null}
            <div className="min-w-0 flex-1">
              <Breadcrumbs />
            </div>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2 px-3 py-2">
              {onMenuToggle ? (
                <Button
                  size="sm"
                  variant="secondary"
                  className="md:hidden"
                  onClick={onMenuToggle}
                  aria-label={t("nav.openMenu")}
                >
                  {t("nav.menu")}
                </Button>
              ) : null}

              <Link to="/dashboard" className="ews-logo" aria-label={t("nav.homeAria")}>
                <span className="ews-logo-mark">AE</span>
                <span className="ews-logo-text hidden sm:inline">
                  ADOS <span>{t("nav.enterprise")}</span>
                </span>
              </Link>

              <OwnerIdentityStrip />

              <Button
                size="sm"
                variant="ghost"
                onClick={() => toggleHeader()}
                aria-label={t("toolbar.collapse")}
                aria-pressed={false}
                data-testid="toolbar-collapse"
                title={t("toolbar.collapse")}
              >
                ▴
              </Button>

              <div className="min-w-32 flex-1">
                <UnifiedIntentBar
                  compact
                  verticalId={isClient ? "auto" : "owner"}
                  showQuickHints={false}
                  showRecent={false}
                  onOpenAiChat={() => setAiOpen(true)}
                />
              </div>

              <Button size="sm" variant="secondary" onClick={() => setCreateOpen(true)} data-testid="header-create">
                Создать
              </Button>

              <Button
                size="sm"
                variant="secondary"
                onClick={() => setAiOpen(true)}
                data-testid="header-ai-chat"
              >
                Поговорить с AI
              </Button>

              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  openPalette();
                  void telemetry.userActivity("open_palette");
                }}
              >
                {t("nav.commands")}
              </Button>

              <DevRoleSwitcher />

              <ModeSwitch compact />
              <ModeIndicator className="hidden xl:inline-flex" />

              <Button
                size="sm"
                variant={activityMode !== "hidden" ? "primary" : "secondary"}
                onClick={() => toggleActivity()}
                aria-label={t("nav.notifications")}
                aria-pressed={activityMode !== "hidden"}
              >
                {t("nav.notifications")} <Badge tone="warning">{count}</Badge>
              </Button>

              {!isClient ? (
                <Button
                  size="sm"
                  variant={focusMode ? "primary" : "secondary"}
                  onClick={() => toggleFocusMode()}
                  aria-label={t("shell.focus.toggle")}
                  data-testid="focus-mode"
                  title={`${t("shell.focus.toggle")} · Ctrl+Shift+F`}
                >
                  {t("shell.focus.short")}
                </Button>
              ) : null}

              <Button
                size="sm"
                variant="secondary"
                onClick={() => navigate(isClient ? "/settings" : "/settings?tab=interface")}
                aria-label={t("nav.settings")}
              >
                ⚙
              </Button>

              <div className="relative">
                {user ? (
                  <button
                    ref={avatarRef}
                    type="button"
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--ew-border)] px-2 py-1"
                    onClick={() => setUserMenuOpen((v) => !v)}
                    title={user.email}
                    aria-expanded={userMenuOpen}
                    aria-haspopup="menu"
                    data-testid="user-menu-trigger"
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
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 pb-2">
              <div className="min-w-0 flex-1">
                <Breadcrumbs />
              </div>
              <ModuleHelpIcon />
            </div>
          </>
        )}
      </header>

      {userMenuOpen && user ? (
        <div
          className="ews-user-menu ews-glass"
          role="menu"
          data-testid="user-menu"
          style={{ top: menuPos.top, right: menuPos.right }}
        >
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
              navigate("/settings?tab=interface");
            }}
          >
            {t("iface.title")}
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setUserMenuOpen(false);
              navigate("/ai-tasks");
            }}
          >
            Центр AI-задач
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setUserMenuOpen(false);
              navigate("/settings/ai-mode");
            }}
          >
            Настройки AI
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

      <ContextualAiChat open={aiOpen} onClose={() => setAiOpen(false)} />
      <QuickCreatePanel open={createOpen} onClose={() => setCreateOpen(false)} />
    </>
  );
}
