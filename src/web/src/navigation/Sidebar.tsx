import { useMemo, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useAuthStore } from "@/auth/authStore";
import { cn } from "@/utils/cn";
import { navigationManager } from "../../navigation/managers/navigationManager";
import { Badge } from "@/ui";
import { useIsPlatformOwner } from "../../platform-builder/managers/platformOwner";
import { ShellIcon, type ShellIconId } from "@/shell/enterprise";
import { shellModuleRegistry } from "@/shell/enterprise/shellModuleRegistry";
import { useShellPreferences } from "@/shell/enterprise/shellPreferencesStore";
import type { ShellModuleCategory } from "@/shell/enterprise/shellModuleRegistry";
import {
  CATEGORY_LABEL_RU,
  ENTERPRISE_RU_SIDEBAR,
  MODULE_LABEL_RU,
  OWNER_RU_NAV,
} from "./enterpriseRuNav";
import { useRoleSwitcher } from "./roleSwitcherStore";
import { SIMPLE_MODE_NAV, useExperienceModeStore, useModuleContextNav } from "@/ux-revolution";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";

/**
 * Sprint 30.2 / 33.1 — Russian enterprise sidebar + Simple/Pro + context nav.
 */
export function Sidebar({
  mobileOpen = false,
  onNavigate,
}: {
  mobileOpen?: boolean;
  onNavigate?: () => void;
} = {}) {
  const t = useI18n((s) => s.t);
  const navigate = useNavigate();
  const { openPalette } = useNavigationUi();
  const modules = useWorkspaceStore((s) => s.workspace.activeModules);
  const permissions = useWorkspaceStore((s) => s.workspace.permissions);
  const tenantId = useAuthStore((s) => s.user?.tenantId) || "demo";
  const roleId = useAuthStore((s) => s.user?.roleId);
  const isOwner = useIsPlatformOwner();
  const ownerView = useRoleSwitcher((s) => s.isOwnerView());
  const uxMode = useExperienceModeStore((s) => s.mode);
  const context = useModuleContextNav();
  const [platformOpen, setPlatformOpen] = useState(false);
  const [ownerOpen, setOwnerOpen] = useState(true);

  const pinned = useShellPreferences((s) => s.pinned);
  const favorites = useShellPreferences((s) => s.favorites);
  const recentModuleIds = useShellPreferences((s) => s.recentModuleIds);
  const collapsedCategories = useShellPreferences((s) => s.collapsedCategories);
  const togglePin = useShellPreferences((s) => s.togglePin);
  const toggleFavorite = useShellPreferences((s) => s.toggleFavorite);
  const toggleCategory = useShellPreferences((s) => s.toggleCategory);

  const navItems = useMemo(() => shellModuleRegistry.toNavItems(), []);
  const byId = useMemo(() => new Map(navItems.map((n) => [n.id, n])), [navItems]);

  const effectivePermissions = [
    ...permissions,
    ...(roleId ? [roleId] : []),
    ...(isOwner ? ["platform_owner", "admin"] : []),
  ];
  const items = navigationManager.forTenant(tenantId, effectivePermissions, "sidebar");

  const asideClass = cn(
    "ews-sidebar ews-glass eds-sidebar shrink-0",
    "md:block",
    mobileOpen ? "fixed inset-y-0 left-0 z-40 block shadow-lg eds-anim-slide" : "hidden",
  );

  const pinnedItems = pinned.map((id) => byId.get(id)).filter(Boolean);
  const favoriteItems = favorites.map((id) => byId.get(id)).filter(Boolean);
  const recentItems = recentModuleIds
    .map((id) => byId.get(id))
    .filter(Boolean)
    .slice(0, 6);

  const categories: ShellModuleCategory[] = ["core", "business", "ai", "ops", "platform", "system"];
  const showOwner = uxMode === "pro" && (isOwner || ownerView);
  const showProExtras = uxMode === "pro";
  const primaryNav = context ? null : uxMode === "simple" ? SIMPLE_MODE_NAV : ENTERPRISE_RU_SIDEBAR;

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
      <aside className={asideClass} data-ux-mode={uxMode}>
        <div className="mb-4 px-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--eds-text-muted)]">
            {t("app.title")}
          </p>
          <p className="eds-type-helper">
            {uxMode === "simple" ? "Simple Mode · UX 33.1" : t("nav.enterpriseOs")}
          </p>
        </div>

        {context ? (
          <nav aria-label={`Контекст · ${context.label}`} className="mb-4">
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
            <button
              type="button"
              className="mt-2 px-2 text-xs text-[var(--eds-text-muted)] underline"
              onClick={() => {
                navigate("/dashboard");
                onNavigate?.();
              }}
            >
              ← Все модули
            </button>
          </nav>
        ) : (
          <nav aria-label="Основное меню" className="mb-4">
            <p className="ews-nav-section">{t("nav.mainMenu")}</p>
            <ul className="ews-nav-list">
              {(primaryNav || []).map((item) => (
                <li key={item.id} className="ews-nav-row">
                  {"opensPalette" in item && item.opensPalette ? (
                    <button
                      type="button"
                      className="ews-nav-link w-full text-left"
                      onClick={() => {
                        onNavigate?.();
                        openPalette();
                      }}
                    >
                      <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                      <span className="ews-nav-label">{item.label}</span>
                    </button>
                  ) : (
                    <NavLink
                      to={item.route}
                      end={item.route === "/dashboard"}
                      onClick={onNavigate}
                      className={({ isActive }) => cn("ews-nav-link", isActive && "is-active")}
                    >
                      <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                      <span className="ews-nav-label">{item.label}</span>
                    </NavLink>
                  )}
                </li>
              ))}
            </ul>
          </nav>
        )}

        {showOwner ? (
          <nav aria-label="Режим владельца" className="mb-4">
            <button
              type="button"
              className="ews-nav-section ews-nav-section-btn"
              onClick={() => setOwnerOpen((v) => !v)}
            >
              {t("nav.ownerMode")}
              <span aria-hidden>{ownerOpen ? "−" : "+"}</span>
            </button>
            {ownerOpen ? (
              <ul className="ews-nav-list">
                {OWNER_RU_NAV.map((item) => (
                  <li key={item.id} className="ews-nav-row">
                    <NavLink
                      to={item.route}
                      onClick={onNavigate}
                      className={({ isActive }) =>
                        cn("ews-nav-link", isActive && "is-active")
                      }
                    >
                      <ShellIcon id={(item.icon || "dashboard") as ShellIconId} />
                      <span className="ews-nav-label">{item.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            ) : null}
          </nav>
        ) : null}

        {showProExtras && pinnedItems.length ? (
          <nav aria-label="Закреплённые" className="mb-3">
            <p className="ews-nav-section">{t("nav.pinned")}</p>
            <ul className="ews-nav-list">
              {pinnedItems.map((item) =>
                item ? (
                  <li key={`pin_${item.id}`} className="ews-nav-row">
                    <NavLink
                      to={item.route}
                      onClick={onNavigate}
                      className={({ isActive }) =>
                        cn("ews-nav-link", isActive && "is-active")
                      }
                    >
                      <ShellIcon id={item.icon as ShellIconId} />
                      <span className="ews-nav-label">
                        {MODULE_LABEL_RU[item.id] || item.label}
                      </span>
                      {item.badge ? <Badge>{item.badge}</Badge> : null}
                    </NavLink>
                    <button
                      type="button"
                      className="ews-nav-action is-on"
                      title={t("nav.unpin")}
                      aria-label={t("nav.unpin")}
                      onClick={(e) => {
                        e.preventDefault();
                        togglePin(item.id);
                      }}
                    >
                      ★
                    </button>
                  </li>
                ) : null,
              )}
            </ul>
          </nav>
        ) : null}

        {showProExtras && favoriteItems.length ? (
          <nav aria-label="Избранное" className="mb-3">
            <p className="ews-nav-section">{t("nav.favorites")}</p>
            <ul className="ews-nav-list">
              {favoriteItems.map((item) =>
                item ? (
                  <li key={`fav_${item.id}`} className="ews-nav-row">
                    <NavLink
                      to={item.route}
                      onClick={onNavigate}
                      className={({ isActive }) =>
                        cn("ews-nav-link", isActive && "is-active")
                      }
                    >
                      <ShellIcon id={item.icon as ShellIconId} />
                      <span className="ews-nav-label">
                        {MODULE_LABEL_RU[item.id] || item.label}
                      </span>
                    </NavLink>
                    <button
                      type="button"
                      className="ews-nav-action is-on"
                      title={t("nav.unfavorite")}
                      aria-label={t("nav.unfavorite")}
                      onClick={(e) => {
                        e.preventDefault();
                        toggleFavorite(item.id);
                      }}
                    >
                      ♥
                    </button>
                  </li>
                ) : null,
              )}
            </ul>
          </nav>
        ) : null}

        {showProExtras && recentItems.length ? (
          <nav aria-label="Недавние" className="mb-3">
            <p className="ews-nav-section">{t("nav.recent")}</p>
            <ul className="ews-nav-list">
              {recentItems.map((item) =>
                item ? (
                  <li key={`recent_${item.id}`} className="ews-nav-row">
                    <NavLink
                      to={item.route}
                      onClick={onNavigate}
                      className={({ isActive }) =>
                        cn("ews-nav-link", isActive && "is-active")
                      }
                    >
                      <ShellIcon id={item.icon as ShellIconId} />
                      <span className="ews-nav-label">
                        {MODULE_LABEL_RU[item.id] || item.label}
                      </span>
                    </NavLink>
                  </li>
                ) : null,
              )}
            </ul>
          </nav>
        ) : null}

        {showProExtras ? (
        <>
        <nav aria-label="Каталог модулей">
          {categories.map((cat) => {
            const mods = shellModuleRegistry.byCategory(cat);
            if (!mods.length) return null;
            const collapsed = collapsedCategories.includes(cat);
            return (
              <div key={cat} className="mb-2">
                <button
                  type="button"
                  className="ews-nav-section ews-nav-section-btn"
                  onClick={() => toggleCategory(cat)}
                >
                  {CATEGORY_LABEL_RU[cat] || cat}
                  <span aria-hidden>{collapsed ? "+" : "−"}</span>
                </button>
                {collapsed ? null : (
                  <ul className="ews-nav-list">
                    {mods.map((m) => {
                      const item = byId.get(m.id);
                      if (!item) return null;
                      return (
                        <li key={item.id} className="ews-nav-row">
                          <NavLink
                            to={item.route}
                            onClick={onNavigate}
                            className={({ isActive }) =>
                              cn(
                                "ews-nav-link",
                                isActive && "is-active",
                                item.comingSoon && "is-soon",
                              )
                            }
                          >
                            <ShellIcon id={item.icon as ShellIconId} />
                            <span className="ews-nav-label">
                              {MODULE_LABEL_RU[item.id] || item.label}
                            </span>
                          </NavLink>
                          <div className="ews-nav-actions">
                            <button
                              type="button"
                              className={cn(
                                "ews-nav-action",
                                pinned.includes(item.id) && "is-on",
                              )}
                              title={
                                pinned.includes(item.id) ? t("nav.unpin") : t("nav.pin")
                              }
                              aria-label={
                                pinned.includes(item.id) ? t("nav.unpin") : t("nav.pin")
                              }
                              onClick={(e) => {
                                e.preventDefault();
                                togglePin(item.id);
                              }}
                            >
                              {pinned.includes(item.id) ? "★" : "☆"}
                            </button>
                            <button
                              type="button"
                              className={cn(
                                "ews-nav-action",
                                favorites.includes(item.id) && "is-on",
                              )}
                              title={
                                favorites.includes(item.id)
                                  ? t("nav.unfavorite")
                                  : t("nav.favorite")
                              }
                              aria-label={
                                favorites.includes(item.id)
                                  ? t("nav.unfavorite")
                                  : t("nav.favorite")
                              }
                              onClick={(e) => {
                                e.preventDefault();
                                toggleFavorite(item.id);
                              }}
                            >
                              {favorites.includes(item.id) ? "♥" : "♡"}
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })}
        </nav>

        <div className="mt-6 px-1">
          <button
            type="button"
            className="mb-2 w-full rounded-md px-2 py-1 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--eds-text-muted)] hover:text-[var(--eds-primary)]"
            onClick={() => setPlatformOpen((v) => !v)}
          >
            {platformOpen ? t("nav.hidePlatform") : t("nav.platform")}
          </button>
          {platformOpen ? (
            <nav className="space-y-1" aria-label="Платформа">
              {items.slice(0, 12).map((item) => (
                <NavLink
                  key={item.id}
                  to={item.route}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      "block rounded-md px-2 py-1.5 text-xs",
                      isActive
                        ? "bg-[var(--ew-brand-soft)] font-semibold text-[var(--ew-brand)]"
                        : "text-[var(--ew-muted)]",
                    )
                  }
                >
                  {MODULE_LABEL_RU[item.module] || item.name}
                </NavLink>
              ))}
            </nav>
          ) : null}
        </div>

        {modules.length ? (
          <div className="mt-6 px-2">
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[var(--ew-muted)]">
              {t("nav.workspaceModules")}
            </div>
            <ul className="space-y-1 text-xs text-[var(--ew-muted)]">
              {modules.slice(0, 8).map((m) => (
                <li key={m}>{MODULE_LABEL_RU[m] || m}</li>
              ))}
            </ul>
          </div>
        ) : null}
        </>
        ) : null}
      </aside>
    </>
  );
}
