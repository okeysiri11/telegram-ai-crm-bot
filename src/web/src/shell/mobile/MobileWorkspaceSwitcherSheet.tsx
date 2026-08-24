import { useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { useMobileChromeStore } from "./mobileChromeStore";
import { closeMobileOverlay, navigateFromMobileOverlay } from "./useMobileOverlayHistory";
import type { MobileNavLink } from "./opsCabinetNavStore";

export function MobileWorkspaceSwitcherSheet({ items }: { items: MobileNavLink[] }) {
  const open = useMobileChromeStore((s) => s.switcherOpen);
  const setVerticalId = useVerticalWorkspaceStore((s) => s.setVerticalId);
  const navigate = useNavigate();

  if (!open) return null;

  function openWorkspace(id: string, href: string) {
    setVerticalId(id);
    navigateFromMobileOverlay(navigate, href);
  }

  return (
    <>
      <button type="button" className="ados-mobile-overlay" aria-label="Закрыть" onClick={closeMobileOverlay} />
      <div className="ados-mobile-sheet" data-testid="mobile-workspace-switcher" role="dialog" aria-modal="true">
        <div className="ados-mobile-sheet__head">
          <h2 className="font-semibold">Рабочее пространство</h2>
          <Button size="sm" variant="ghost" onClick={closeMobileOverlay}>
            Закрыть
          </Button>
        </div>
        <div className="ados-mobile-sheet__body flex flex-col gap-1">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              className="flex min-h-11 items-center rounded-md px-3 py-2 text-left"
              data-testid={`mobile-switch-${item.id}`}
              onClick={() => openWorkspace(item.id, item.href)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
