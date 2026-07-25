import type { ReactNode } from "react";
import { useState } from "react";
import { Button } from "./Button";

type Item = { id: string; label: string; onSelect: () => void };

export function Dropdown({ label, items }: { label: string; items: Item[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative inline-block">
      <Button variant="secondary" size="sm" onClick={() => setOpen((v) => !v)}>{label}</Button>
      {open ? (
        <div className="absolute right-0 z-20 mt-1 min-w-40 rounded-md border border-[var(--ew-border)] bg-[var(--ew-surface)] py-1 shadow">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              className="block w-full px-3 py-2 text-left text-sm hover:bg-[var(--ew-brand-soft)]"
              onClick={() => {
                item.onSelect();
                setOpen(false);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
