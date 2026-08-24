import { useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { useIsPlatformOwner } from "../../../platform-builder/managers/platformOwner";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useMobileChromeStore } from "./mobileChromeStore";
import { closeMobileOverlay, navigateFromMobileOverlay } from "./useMobileOverlayHistory";

export function MobileMoreSheet() {
  const open = useMobileChromeStore((s) => s.moreOpen);
  const setSwitcherOpen = useMobileChromeStore((s) => s.setSwitcherOpen);
  const setSearchOpen = useMobileChromeStore((s) => s.setSearchOpen);
  const navigate = useNavigate();
  const isOwner = useIsPlatformOwner() || useRoleSwitcher((s) => s.isOwnerView());

  if (!open) return null;

  function go(path: string) {
    navigateFromMobileOverlay(navigate, path);
  }

  return (
    <>
      <button type="button" className="ados-mobile-overlay" aria-label="Закрыть" onClick={closeMobileOverlay} />
      <div className="ados-mobile-sheet" data-testid="mobile-more-sheet" role="dialog" aria-modal="true">
        <div className="ados-mobile-sheet__head">
          <h2 className="font-semibold">Ещё</h2>
          <Button size="sm" variant="ghost" onClick={closeMobileOverlay}>
            Закрыть
          </Button>
        </div>
        <div className="ados-mobile-sheet__body flex flex-col gap-1">
          <Button variant="ghost" onClick={() => go("/settings")}>
            Настройки
          </Button>
          <Button variant="ghost" onClick={() => go("/identity/profile")}>
            Профиль
          </Button>
          <Button variant="ghost" onClick={() => setSwitcherOpen(true)}>
            Сменить Workspace
          </Button>
          <Button variant="ghost" onClick={() => go("/ai-agents")}>
            AI Agents
          </Button>
          <Button variant="ghost" onClick={() => setSearchOpen(true)}>
            Поиск
          </Button>
          <Button variant="ghost" onClick={() => go("/notifications")}>
            Уведомления
          </Button>
          {isOwner ? (
            <Button variant="ghost" data-testid="mobile-platform-mgmt" onClick={() => go("/owner")}>
              Управление платформой
            </Button>
          ) : null}
          <Button variant="danger" onClick={() => go("/auth/logout")}>
            Выйти
          </Button>
        </div>
      </div>
    </>
  );
}
