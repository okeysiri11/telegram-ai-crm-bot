import type { ReactNode } from "react";
import { Button } from "./Button";

type Props = { open: boolean; title: string; onClose: () => void; children: ReactNode };

export function Drawer({ open, title, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div className="eds-drawer-overlay" role="presentation" onClick={onClose}>
      <aside
        className="eds-drawer-panel"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="eds-drawer-header">
          <h2 className="eds-drawer-title">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
        {children}
      </aside>
    </div>
  );
}
