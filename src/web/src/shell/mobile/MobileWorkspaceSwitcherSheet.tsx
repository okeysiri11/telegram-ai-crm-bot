import { Link } from "react-router-dom";
import { Button } from "@/ui";
import { useMobileChromeStore } from "./mobileChromeStore";
import type { MobileNavLink } from "./opsCabinetNavStore";

export function MobileWorkspaceSwitcherSheet({ items }: { items: MobileNavLink[] }) {
  const open = useMobileChromeStore((s) => s.switcherOpen);
  const closeAll = useMobileChromeStore((s) => s.closeAll);

  if (!open) return null;

  return (
    <>
      <button type="button" className="ados-mobile-overlay" aria-label="Закрыть" onClick={closeAll} />
      <div className="ados-mobile-sheet" data-testid="mobile-workspace-switcher" role="dialog" aria-modal="true">
        <div className="ados-mobile-sheet__head">
          <h2 className="font-semibold">Рабочее пространство</h2>
          <Button size="sm" variant="ghost" onClick={closeAll}>
            Закрыть
          </Button>
        </div>
        <div className="ados-mobile-sheet__body flex flex-col gap-1">
          {items.map((item) => (
            <Link
              key={item.id}
              to={item.href}
              className="flex min-h-11 items-center rounded-md px-3 py-2"
              onClick={closeAll}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
