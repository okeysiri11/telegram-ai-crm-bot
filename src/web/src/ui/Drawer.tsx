import type { ReactNode } from "react";
import { Button } from "./Button";

type Props = { open: boolean; title: string; onClose: () => void; children: ReactNode };

export function Drawer({ open, title, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30">
      <aside className="h-full w-full max-w-md border-l border-[var(--ew-border)] bg-[var(--ew-surface)] p-4 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
        </div>
        {children}
      </aside>
    </div>
  );
}
