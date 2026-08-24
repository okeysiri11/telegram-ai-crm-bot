import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { useMobileChromeStore } from "./mobileChromeStore";
import { isMobileNavHrefActive } from "./mobileWorkspace";
import { closeMobileOverlay, navigateFromMobileOverlay } from "./useMobileOverlayHistory";
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
  const setSwitcherOpen = useMobileChromeStore((s) => s.setSwitcherOpen);
  const navigate = useNavigate();
  const { pathname, search } = useLocation();

  if (!open) return null;

  return (
    <>
      <button type="button" className="ados-mobile-overlay" aria-label="Закрыть меню" onClick={closeMobileOverlay} />
      <aside
        className="ados-mobile-drawer"
        data-testid="mobile-workspace-drawer"
        data-ops-panel="true"
        role="dialog"
        aria-modal="true"
        aria-label="Операционная панель"
      >
        <div className="ados-mobile-drawer__head">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">ADOS Enterprise</p>
          <p className="eds-type-caption text-[var(--eds-text-muted)]">Рабочее пространство:</p>
          <h2 className="text-base font-semibold">{workspaceLabel}</h2>
          <p className="eds-type-small text-[var(--eds-text-muted)]">Роль: {roleLabel}</p>
          <Button
            size="sm"
            className="mt-2"
            variant="secondary"
            data-testid="mobile-switch-workspace"
            onClick={() => setSwitcherOpen(true)}
          >
            Сменить рабочее пространство
          </Button>
        </div>
        <nav className="ados-mobile-drawer__nav" aria-label="Разделы рабочего пространства">
          {items.map((item) => {
            const active = isMobileNavHrefActive(item.href, pathname, search);
            return (
              <button
                key={item.id}
                type="button"
                data-testid={`mobile-drawer-${item.id}`}
                className={`ados-mobile-link${active ? " is-active" : ""}`}
                onClick={() => navigateFromMobileOverlay(navigate, item.href)}
              >
                {item.label}
              </button>
            );
          })}
          {showPlatform ? (
            <div className="ados-mobile-drawer__platform">
              <p className="mb-1 px-2 eds-type-caption text-[var(--eds-text-muted)]">Управление платформой</p>
              {platformItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="ados-mobile-link"
                  onClick={() => navigateFromMobileOverlay(navigate, item.href)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          ) : null}
        </nav>
      </aside>
    </>
  );
}
