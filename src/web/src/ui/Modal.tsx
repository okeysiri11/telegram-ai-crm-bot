import type { ReactNode } from "react";
import { Button } from "./Button";

type Props = { open: boolean; title: string; onClose: () => void; children: ReactNode };

export function Modal({ open, title, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-lg border border-[var(--ew-border)] bg-[var(--ew-surface)] p-4 shadow-lg">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
        </div>
        {children}
      </div>
    </div>
  );
}
