/**
 * Sprint 33.2 — Intelligent Navigation sidebar (collapsible groups).
 * Extends 33.1 Simple/Pro + context nav. Routes unchanged.
 */

import { useEffect, useMemo } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
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
} from "@/ux-revolution";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import "@/ux-revolution/intelligentNav.css";

export function Sidebar({
  mobileOpen = false,
  onNavigate,
}: {
  mobileOpen?: boolean;
  onNavigate?: () => void;
} = {}) {
  const t = useI18n((s) => s.t);
  const navigate = useNavigate();
  const { pathname, search } = useLocation();
  const { openPalette } = useNavigationUi();
  const modules = useWorkspaceStore((s) => s.workspace.activeModules);
  const isOwner = useIsPlatformOwner();
  const ownerView = useRoleSwitcher((s) => s.isOwnerView());
  const uxMode = useExperienceModeStore((s) => s.mode);
  const context = useModuleContextNav();
  const expandedId = useNavAccordionStore((s) => s.expandedId);
  const toggleGroup = useNavAccordionStore((s) => s.toggle);

  const showOwner = isOwner || ownerView;
  const groups = useMemo(
    () => groupsForMode(uxMode, { owner: showOwner }),
    [uxMode, showOwner],
  );

  useEffect(() => {
    warmRegistryNavigation(uxMode, { owner: showOwner });
  }, [uxMode, showOwner]);

  const visibleGroups = groups;
  useEffect(() => {
    const gid = resolveGroupForPath(pathname, search);
    // Call store action via getState to avoid unstable selector identity churn.
    useNavAccordionStore.getState().ensureForRoute(gid);
  }, [pathname, search]);

  const asideClass = cn(
    "ews-sidebar ews-glass eds-sidebar shrink-0",
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
      <aside className={asideClass} data-ux-mode={uxMode} data-sprint="33.2">
        <div className="mb-4 px-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--eds-text-muted)]">
            {t("app.title")}
          </p>
          <p className="eds-type-helper">
            {uxMode === "simple" ? "Simple · Intelligent Nav" : "Pro · Intelligent Nav"}
          </p>
        </div>

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

        <nav aria-label="Intelligent Navigation" className="mb-4">
          {visibleGroups.map((group) => {
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
                          className={() => cn("ews-nav-link", active && "is-active")}
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
          {modules.length ? `${modules.length} модулей` : "ADOS UX 33.2"}
          {showOwner ? " · Owner" : ""}
        </div>
      </aside>
    </>
  );
}
