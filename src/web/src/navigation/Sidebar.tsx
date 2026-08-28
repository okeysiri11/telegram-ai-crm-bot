/**
 * Sprint 33.2 / 42.2 — Intelligent Navigation sidebar with icon-rail collapse.
 */

import { useEffect, useMemo } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { cn } from "@/utils/cn";
import { useIsPlatformOwner } from "../../platform-builder/managers/platformOwner";
import { ShellIcon, type ShellIconId } from "@/shell/enterprise";
import { useRoleSwitcher } from "./roleSwitcherStore";
import {
  useExperienceModeStore,
  useModuleContextNav,
  groupsForMode,
  warmRegistryNavigation,
  useNavAccordionStore,
  resolveGroupForPath,
  isNavItemActive,
  NavAccordionGroup,
  useViewModeStore,
  viewModeLabel,
} from "@/ux-revolution";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { useAdaptiveShellStore } from "@/shell/enterprise/adaptiveShellStore";
import { Button } from "@/ui";
import "@/ux-revolution/intelligentNav.css";

export function Sidebar({
  mobileOpen = false,
  onNavigate,
}: {
  mobileOpen?: boolean;
  onNavigate?: () => void;
} = {}) {
  const t = useI18n((s) => s.t);
  const { pathname, search } = useLocation();
  const { openPalette } = useNavigationUi();
  const modules = useWorkspaceStore((s) => s.workspace.activeModules);
  const isOwner = useIsPlatformOwner();
  const ownerView = useRoleSwitcher((s) => s.isOwnerView());
  const viewMode = useViewModeStore((s) => s.viewMode);
  const locale = useI18n((s) => s.locale);
  const uxMode = useExperienceModeStore((s) => s.mode);
  const context = useModuleContextNav();
  const expandedId = useNavAccordionStore((s) => s.expandedId);
  const toggleGroup = useNavAccordionStore((s) => s.toggle);
  const sidebarCollapsed = useAdaptiveShellStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useAdaptiveShellStore((s) => s.toggleSidebar);
  const focusMode = useAdaptiveShellStore((s) => s.focusMode);

  const showOwner =
    (isOwner || ownerView) &&
    (viewMode === "platform_owner" || viewMode === "developer");
  const groups = useMemo(
    () => groupsForMode(uxMode, { owner: showOwner, viewMode }),
    [uxMode, showOwner, viewMode],
  );

  const flatItems = useMemo(() => {
    const items: Array<{ id: string; label: string; route: string; icon?: string; opensPalette?: boolean }> = [];
    for (const g of groups) {
      for (const item of g.items) {
        items.push(item);
      }
    }
    return items.slice(0, 24);
  }, [groups]);

  useEffect(() => {
    warmRegistryNavigation(uxMode, { owner: showOwner });
  }, [uxMode, showOwner]);

  useEffect(() => {
    const gid = resolveGroupForPath(pathname, search);
    useNavAccordionStore.getState().ensureForRoute(gid);
  }, [pathname, search]);

  if (focusMode) return null;

  const asideClass = cn(
    "ews-sidebar ews-glass eds-sidebar shrink-0 ews-sidebar--anim",
    sidebarCollapsed && "ews-sidebar--collapsed",
    "md:block",
    mobileOpen ? "fixed inset-y-0 left-0 z-40 block shadow-lg eds-anim-slide" : "hidden",
  );

  return (
    <>
      {mobileOpen ? (
        <button
          type="button"
          aria-label="Закрыть навигацию"
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={onNavigate}
        />
      ) : null}
      <aside
        className={asideClass}
        data-ux-mode={uxMode}
        data-collapsed={sidebarCollapsed ? "1" : "0"}
        data-testid="enterprise-sidebar"
      >
        <div className={cn("mb-3 flex items-center gap-2", sidebarCollapsed ? "justify-center px-1" : "px-2")}>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => toggleSidebar()}
            aria-label={sidebarCollapsed ? t("shell.sidebar.expand") : t("shell.sidebar.collapse")}
            aria-pressed={sidebarCollapsed}
            data-testid="sidebar-collapse"
            title={sidebarCollapsed ? t("shell.sidebar.expand") : t("shell.sidebar.collapse")}
          >
            ☰
          </Button>
          {!sidebarCollapsed ? (
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-[var(--eds-text-muted)] truncate">
                {t("nav.menu")}
              </p>
              <p className="eds-type-helper truncate" data-testid="sidebar-view-mode">
                {viewModeLabel(viewMode, locale === "en" ? "en" : "ru")}
              </p>
            </div>
          ) : null}
        </div>

        {sidebarCollapsed ? (
          <nav aria-label={t("nav.navigation")} className="ews-sidebar-rail">
            <ul className="ews-nav-list ews-nav-list--rail">
              {flatItems.map((item) => {
                const active = isNavItemActive(item, pathname, search);
                if (item.opensPalette) {
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        className={cn("ews-nav-link ews-nav-link--rail", active && "is-active")}
                        title={item.label}
                        aria-label={item.label}
                        onClick={() => {
                          onNavigate?.();
                          openPalette();
                        }}
                      >
                        <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                      </button>
                    </li>
                  );
                }
                return (
                  <li key={item.id}>
                    <NavLink
                      to={item.route}
                      end={item.route === "/dashboard"}
                      onClick={onNavigate}
                      title={item.label}
                      aria-label={item.label}
                      data-testid={`nav-${item.id}`}
                      className={() => cn("ews-nav-link ews-nav-link--rail", active && "is-active", item.id === "vert_casino" && "ews-nav-link--casino")}
                    >
                      <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </nav>
        ) : (
          <>
            {context ? (
              <nav aria-label={`Контекст · ${context.label}`} className="mb-3">
                <p className="ews-nav-section">{context.label}</p>
                <ul className="ews-nav-list">
                  {context.items.map((item) => (
                    <li key={item.id} className="ews-nav-row">
                      <NavLink
                        to={item.route}
                        onClick={onNavigate}
                        className={({ isActive }) => cn("ews-nav-link", isActive && "is-active")}
                      >
                        <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                        <span className="ews-nav-label">{item.label}</span>
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </nav>
            ) : null}

            <nav aria-label="Навигация" className="mb-4">
              {groups.map((group) => {
                const expanded = expandedId === group.id;
                return (
                  <NavAccordionGroup
                    key={group.id}
                    id={group.id}
                    label={group.label}
                    icon={group.icon}
                    expanded={expanded}
                    onToggle={() => toggleGroup(group.id)}
                  >
                    <ul className="ews-nav-list">
                      {group.items.map((item) => {
                        const active = isNavItemActive(item, pathname, search);
                        if (item.opensPalette) {
                          return (
                            <li key={item.id} className="ews-nav-row">
                              <button
                                type="button"
                                className={cn("ews-nav-link w-full text-left", active && "is-active")}
                                onClick={() => {
                                  onNavigate?.();
                                  openPalette();
                                }}
                              >
                                <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                                <span className="ews-nav-label">{item.label}</span>
                              </button>
                            </li>
                          );
                        }
                        return (
                          <li key={item.id} className="ews-nav-row">
                            <NavLink
                              to={item.route}
                              end={item.route === "/dashboard"}
                              onClick={onNavigate}
                              data-testid={`nav-${item.id}`}
                              className={() =>
                                cn(
                                  "ews-nav-link",
                                  active && "is-active",
                                  item.id === "vert_casino" && "ews-nav-link--casino",
                                )
                              }
                            >
                              <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                              <span className="ews-nav-label">{item.label}</span>
                            </NavLink>
                          </li>
                        );
                      })}
                    </ul>
                  </NavAccordionGroup>
                );
              })}
            </nav>

            <div className="mt-auto px-2 pb-3 eds-type-caption text-[var(--eds-text-muted)]">
              {modules.length ? `${modules.length} модулей` : "ADOS UX 42.2"}
              {showOwner ? " · Владелец" : ""}
            </div>
          </>
        )}
      </aside>
    </>
  );
}
