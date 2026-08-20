import { NavLink } from "react-router-dom";
import { Button } from "@/ui";
import { useMobileChromeStore } from "./mobileChromeStore";
import type { MobileNavLink } from "./opsCabinetNavStore";

export function MobileWorkspaceDrawer({
  workspaceLabel,
  roleLabel,
  items,
  showPlatform,
  platformItems,
}: {
  workspaceLabel: string;
  roleLabel: string;
  items: MobileNavLink[];
  showPlatform: boolean;
  platformItems: MobileNavLink[];
}) {
  const open = useMobileChromeStore((s) => s.drawerOpen);
  const closeAll = useMobileChromeStore((s) => s.closeAll);
  const setSwitcherOpen = useMobileChromeStore((s) => s.setSwitcherOpen);

  if (!open) return null;

  return (
    <>
      <button type="button" className="ados-mobile-overlay" aria-label="Закрыть меню" onClick={closeAll} />
      <aside className="ados-mobile-drawer" data-testid="mobile-workspace-drawer" role="dialog" aria-modal="true">
        <div className="ados-mobile-drawer__head">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">ADOS Enterprise</p>
          <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">Рабочее пространство:</p>
          <h2 className="text-lg font-semibold">{workspaceLabel}</h2>
          <p className="mt-1 eds-type-small text-[var(--eds-text-muted)]">Роль: {roleLabel}</p>
          <Button
            className="mt-3"
            variant="secondary"
            data-testid="mobile-switch-workspace"
            onClick={() => setSwitcherOpen(true)}
          >
            Сменить рабочее пространство
          </Button>
        </div>
        <nav className="ados-mobile-drawer__nav" aria-label="Разделы рабочего пространства">
          {items.map((item) => (
            <NavLink
              key={item.id}
              to={item.href}
              className={({ isActive }) => (isActive ? "is-active" : undefined)}
              onClick={closeAll}
            >
              {item.label}
            </NavLink>
          ))}
          {showPlatform ? (
            <div className="mt-4 border-t border-[var(--ew-border)] pt-3">
              <p className="mb-1 px-2 eds-type-caption text-[var(--eds-text-muted)]">Управление платформой</p>
              {platformItems.map((item) => (
                <NavLink key={item.id} to={item.href} onClick={closeAll}>
                  {item.label}
                </NavLink>
              ))}
            </div>
          ) : null}
        </nav>
      </aside>
    </>
  );
}
