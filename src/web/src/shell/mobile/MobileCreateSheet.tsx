import { useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { useMobileChromeStore } from "./mobileChromeStore";
import { createActionsForWorkspace } from "./mobileWorkspace";
import { closeMobileOverlay, navigateFromMobileOverlay } from "./useMobileOverlayHistory";

export function MobileCreateSheet({ verticalId }: { verticalId: string }) {
  const open = useMobileChromeStore((s) => s.createOpen);
  const navigate = useNavigate();
  const actions = createActionsForWorkspace(verticalId);

  if (!open) return null;

  function go(path: string) {
    navigateFromMobileOverlay(navigate, path);
  }

  return (
    <>
      <button type="button" className="ados-mobile-overlay" aria-label="Закрыть" onClick={closeMobileOverlay} />
      <div className="ados-mobile-sheet" data-testid="mobile-create-sheet" role="dialog" aria-modal="true">
        <div className="ados-mobile-sheet__head">
          <h2 className="font-semibold">Создать</h2>
          <Button size="sm" variant="ghost" onClick={closeMobileOverlay}>
            Закрыть
          </Button>
        </div>
        <div className="ados-mobile-sheet__body flex flex-col gap-1">
          {actions.map((action) => (
            <Button
              key={action.id}
              variant="ghost"
              className="justify-start"
              data-testid={`mobile-create-${action.id}`}
              onClick={() => go(action.href)}
            >
              {action.label}
            </Button>
          ))}
        </div>
      </div>
    </>
  );
}
