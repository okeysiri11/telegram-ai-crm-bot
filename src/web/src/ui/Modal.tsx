import type { ReactNode } from "react";
import { Button } from "./Button";

type Props = { open: boolean; title: string; onClose: () => void; children: ReactNode };

export function Modal({ open, title, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div className="eds-dialog-overlay flex items-center justify-center p-[var(--eds-page-pad)]" role="presentation" onClick={onClose}>
      <div
        className="eds-card edm-overlay-panel w-full max-w-lg p-[var(--eds-dialog-pad)] shadow-[var(--eds-shadow-lg)]"
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
      </div>
    </div>
  );
}
